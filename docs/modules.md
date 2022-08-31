(modules)=
# Modules

## `<module>.yml` schema

```json
{
  "title": "Module",
  "type": "object",
  "properties": {
    "name": {
      "title": "Name",
      "type": "string"
    },
    "depends_on": {
      "title": "Depends On",
      "default": [],
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "priority": {
      "title": "Priority",
      "default": 0,
      "type": "integer"
    },
    "setup": {
      "$ref": "#/definitions/FilledTemplate"
    },
    "template": {
      "$ref": "#/definitions/FilledTemplate"
    },
    "image_args": {
      "title": "Image Args",
      "default": {},
      "type": "object"
    }
  },
  "required": [
    "name",
    "template"
  ],
  "definitions": {
    "FilledTemplate": {
      "title": "FilledTemplate",
      "type": "object",
      "properties": {
        "file": {
          "title": "File",
          "default": "chunk.Dockerfile.jinja2",
          "type": "string"
        },
        "variables": {
          "title": "Variables",
          "default": {},
          "type": "object"
        }
      }
    }
  }
}
```
