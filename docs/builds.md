(builds)=
# Builds

"Baked" build configurations are easy to generate, and make repeatable, platform-independent builds, as well as different build scenarios, straightforward to automate.

For example, you might have one build process (including dockerfile targets, image tags, where images should be pushed, what build caching should be used, etc.) for local development, and another build process in CI/CD. While these processes should be as similar as possible, they're fundamentally different situations with different goals. Defining bake configurations is an easy way to configure out the differences.

Build configurations are defined as a list, where each object looks like the following:

```yaml
- name: main
  image: docker.io/account/my-image
  build_args:
    platforms:
      - 'linux/amd64'
      - 'linux/arm64'
    cache-from: registry
    output: [type=registry]
    pull: true
```

Builds must be defined in `docker-printer/builds.yml` or `docker-printer/builds.yml.jinja2`

Each build configuration will be saved to a file named `docker-bake.<name>.json`. All images marked in this file can be built and, if desired, pushed at once using `docker buildx bake -f docker-bake.<name>.json`

## Build Arguments

`buildx` supports a wide variety of arguments, such as where to pull the build cache from, where to save the image, and which CPU architectures to build for. The full enumeration of these arguments [is available here](https://docs.docker.com/build/bake/file-definition/). You can pass through any of these as `build_args`.

(build_tagging)=
## Build Particular Tags

Build configurations can be limited to particular targets by specifying a set of tags. The build config will be exported to only specify targets in the dockerfile that match all the tags specified:

```yaml
- name: dev_local
  image: my-image
  build_args:
    output: [type=docker]
  limit_tags:
    - dev
```

## Image Tagging

Each build configuration specifies the images that should be built. Each target will be tagged with the target's name, with all tags being pushed to the same image/repository under those different tags. You can specify a shared prefix or postfix for this tag across an entire build configuration:

```yaml
- name: dev_local
  image: my-image
  tag_postfix: "local"
```

This will produce images tagged like the following:

```
my-image:target1-local
my-image:target2-local
my-image:target3-local
```

Alternatively, `tag_prefix` is also available.

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
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "tag_prefix": {
          "title": "Tag Prefix",
          "type": "string"
        },
        "tag_postfix": {
          "title": "Tag Postfix",
          "type": "string"
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
