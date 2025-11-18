#!/usr/bin/env python3
"""
Generate OpenAPI spec from FastAPI and convert to YAML with proper formatting
"""
import json
import yaml
import requests
import sys
from datetime import datetime


def generate_spec(host="localhost", port=8000):
    """Fetch OpenAPI spec from FastAPI and enhance it"""
    
    # Fetch the spec from FastAPI
    url = f"http://{host}:{port}/openapi.json"
    print(f"Fetching OpenAPI spec from {url}...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        spec = response.json()
    except requests.RequestException as e:
        print(f"Error fetching spec: {e}")
        sys.exit(1)
    
    # Enhance the spec with additional metadata
    spec["info"]["version"] = "1.0.0"
    spec["info"]["description"] = "Single source of truth for the Loan Manager API. Auth via JWT cookies; FE consumes this spec for types and a thin client."
    
    # Add server configuration
    spec["servers"] = [
        {"url": f"http://localhost:{port}"}
    ]
    
    # Add security schemes if not present
    if "components" not in spec:
        spec["components"] = {}
    
    if "securitySchemes" not in spec["components"]:
        spec["components"]["securitySchemes"] = {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "access_token"
            },
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
    
    # Add global security requirement
    spec["security"] = [
        {"cookieAuth": []},
        {"bearerAuth": []}
    ]
    
    # Clean up the paths to remove /v1 prefix (it's in the server URL)
    cleaned_paths = {}
    for path, methods in spec.get("paths", {}).items():
        if path.startswith("/v1"):
            cleaned_path = path[3:]  # Remove /v1
            cleaned_paths[cleaned_path] = methods
        else:
            cleaned_paths[path] = methods
    spec["paths"] = cleaned_paths
    
    # Update server URL to include /v1
    spec["servers"][0]["url"] = f"http://localhost:{port}/v1"
    
    # Sort paths for consistency
    spec["paths"] = dict(sorted(spec["paths"].items()))
    
    # Sort schemas for consistency
    if "components" in spec and "schemas" in spec["components"]:
        spec["components"]["schemas"] = dict(sorted(spec["components"]["schemas"].items()))
    
    return spec


def save_spec(spec, output_file):
    """Save spec as YAML with proper formatting"""
    
    # Custom YAML representer to format lists nicely
    def list_representer(dumper, data):
        if len(data) <= 3 and all(isinstance(item, str) for item in data):
            # Short string lists on one line
            return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=False)
    
    yaml.add_representer(list, list_representer)
    
    with open(output_file, 'w') as f:
        yaml.dump(spec, f, 
                  default_flow_style=False, 
                  allow_unicode=True,
                  width=120,
                  sort_keys=False)
    
    print(f"Generated {output_file}")
    
    # Also save as JSON for reference
    json_file = output_file.replace('.yml', '.json').replace('.yaml', '.json')
    with open(json_file, 'w') as f:
        json.dump(spec, f, indent=2)
    print(f"Also saved as {json_file}")


if __name__ == "__main__":
    spec = generate_spec()
    save_spec(spec, "openapi/schema.yml")

