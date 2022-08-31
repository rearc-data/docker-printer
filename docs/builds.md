(builds)=
# Builds


(build_tagging)=
### Build Particular Tags



## `builds.yml` Schema

```json
{
  "title": "BuildConfigCollection",
  "type": "array",
  "items": {
    "$ref": "#/definitions/BuildConfig"
  },
  "definitions": {
    "BuildConfig": {
      "title": "BuildConfig",
      "type": "object",
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "image": {
          "title": "Image",
          "type": "string"
        },
        "tag_prefix": {
          "title": "Tag Prefix",
          "type": "string"
        },
        "tag_postfix": {
          "title": "Tag Postfix",
          "type": "string"
        },
        "platforms": {
          "title": "Platforms",
          "default": [
            "linux/amd64"
          ],
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "build_args": {
          "title": "Build Args",
          "default": {
            "load": true
          },
          "type": "object"
        },
        "limit_tags": {
          "title": "Limit Tags",
          "default": [],
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "name",
        "image"
      ]
    }
  }
}

```
