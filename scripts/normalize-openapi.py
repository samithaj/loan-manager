#!/usr/bin/env python3
"""
Normalize OpenAPI specs to reduce noisy diffs:
 - Ignore camelCase vs snake_case (normalize property names to a common form)
 - Ignore string formats (e.g., uuid, date)
 - Ignore required "id" (treat IDs as optional for diff purposes)

Usage:
  python scripts/normalize-openapi.py <input.{json|yml|yaml}> <output.json>

Notes:
 - This script reads JSON or YAML, but always writes JSON for stability.
 - Only structural changes matter after normalization.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


def load_spec(path: str) -> dict:
    p = Path(path)
    data_text = p.read_text(encoding="utf-8")
    # Try JSON first
    try:
        return json.loads(data_text)
    except json.JSONDecodeError:
        if yaml is None:
            raise SystemExit("YAML support not available. Install PyYAML or provide JSON input.")
        return yaml.safe_load(data_text)


def save_json(data: dict, path: str) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_name(name: str) -> str:
    # Collapse underscores and lowercase to ignore case/style differences
    # e.g. display_name -> displayname, displayName -> displayname
    return name.replace("_", "").lower()


def normalize_schema_object(obj: dict) -> dict:
    # Remove string formats (uuid, date, date-time, etc.)
    if isinstance(obj, dict):
        if obj.get("type") == "string" and "format" in obj:
            obj = dict(obj)
            obj.pop("format", None)
    return obj


def normalize_required(required: list | None) -> list | None:
    if not required:
        return required
    # Remove id from required to treat ids as optional
    return [r for r in required if normalize_name(r) != "id"]


def normalize_spec(spec: dict) -> dict:
    spec = json.loads(json.dumps(spec))  # deep copy

    # Normalize components.schemas
    comps = spec.get("components", {})
    schemas = comps.get("schemas", {})
    new_schemas = {}

    for schema_name, schema_def in schemas.items():
        schema_def = _normalize_schema_recursive(schema_def)
        # Also normalize required arrays on top-level schemas
        if isinstance(schema_def, dict):
            if "required" in schema_def and isinstance(schema_def["required"], list):
                schema_def["required"] = normalize_required(schema_def["required"])
        new_schemas[schema_name] = schema_def

    if schemas:
        spec.setdefault("components", {})["schemas"] = new_schemas

    # Normalize paths' request/response bodies schemas as well
    paths = spec.get("paths", {})
    for path_key, path_item in paths.items():
        for method_key, method_item in list(path_item.items()):
            if not isinstance(method_item, dict):
                continue
            # requestBody
            rb = method_item.get("requestBody")
            if isinstance(rb, dict):
                method_item["requestBody"] = _normalize_content(rb)
            # responses
            responses = method_item.get("responses")
            if isinstance(responses, dict):
                for status_code, resp in responses.items():
                    if isinstance(resp, dict):
                        responses[status_code] = _normalize_content(resp)

    return spec


def _normalize_content(obj: dict) -> dict:
    obj = dict(obj)
    content = obj.get("content")
    if isinstance(content, dict):
        for ctype, media in content.items():
            if isinstance(media, dict):
                schema = media.get("schema")
                if isinstance(schema, dict):
                    media["schema"] = _normalize_schema_recursive(schema)
    return obj


def _normalize_schema_recursive(schema: dict) -> dict:
    schema = dict(schema)

    # Remove format on strings
    schema = normalize_schema_object(schema)

    # Normalize properties names
    if "properties" in schema and isinstance(schema["properties"], dict):
        props = schema["properties"]
        new_props = {}
        for prop_name, prop_schema in props.items():
            new_name = normalize_name(prop_name)
            new_props[new_name] = _normalize_schema_recursive(prop_schema) if isinstance(prop_schema, dict) else prop_schema
        schema["properties"] = new_props

    # Normalize required list (remove id)
    if "required" in schema and isinstance(schema["required"], list):
        schema["required"] = normalize_required(schema["required"]) or []

    # Recurse into items (arrays)
    if "items" in schema and isinstance(schema["items"], dict):
        schema["items"] = _normalize_schema_recursive(schema["items"])

    # Recurse into allOf/anyOf/oneOf
    for key in ("allOf", "anyOf", "oneOf"):
        if key in schema and isinstance(schema[key], list):
            schema[key] = [
                _normalize_schema_recursive(s) if isinstance(s, dict) else s for s in schema[key]
            ]

    return schema


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)
    src, dst = sys.argv[1], sys.argv[2]
    spec = load_spec(src)
    norm = normalize_spec(spec)
    save_json(norm, dst)


if __name__ == "__main__":
    main()



