#!/usr/bin/env python3
"""Generate OpenAPI schema from FastAPI app."""

import json
import yaml
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.main import app

# Get OpenAPI schema
openapi_schema = app.openapi()

# Write to YAML file
output_path = Path(__file__).parent.parent / "openapi" / "schema.yml"
output_path.parent.mkdir(exist_ok=True)

with open(output_path, "w") as f:
    yaml.dump(openapi_schema, f, default_flow_style=False, sort_keys=False)

print(f"OpenAPI schema written to {output_path}")
