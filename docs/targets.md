(targets)=
# Targets

While a synthesized dockerfile may have many stages, only some represent final stages for images you care about. Target definitions are how we specify the final stages we care about, and from there `docker-printer` can figure out how to create the dockerfile necessary to produce that stage.

Targets must be defined in `docker-printer/targets.yml` or `docker-printer/targets.yml.jinja2`.

## Example

In your `docker-printer/` folder, define a `targets.yml` file. It will be a list of targets, each of which looks like the following:

```yaml
- name: my-target
  modules:
    - mod1
    - mod2
```

A target can extend another target:

```yaml
- name: my-next-target
  extends:
    - my-target
  modules:
    - mod3
```

This will mark that the new `my-next-target` target relies on all the same modules as `my-target`. This will result in its dockerfile stages being based on the stages of the earlier target. This can be useful, for example, to define a "dev" target with your application dependencies, then a "prod" target that also includes your source code.

### Tags

Targets can be tagged, which allows them to be filtered later in particular build configurations.

```yaml
- name: dev1
  tags:
    - dev
  # ...

- name: dev2
  tags:
    - dev
  # ...
```

See [building tags](build_tagging).

### Exclude

Targets can be excluded from being directly built if they merely represent a common ancestor of other targets.

```yaml
- name: base
  modules:
    - mod1
    - mod2
    - mod3
  exclude: true

- name: dev
  extends:
    - base
  modules:
    - mod4

- name: prod
  extends:
    - base
  modules:
    - mod5
```

### Templating

The targets file can also be written as a jinja2 template by simply renaming it `targets.yml.jinja2`:

```yaml+jinja
{% for i in [1,2,3] %}
- name: dev{{i}}
  tags:
    - dev
{% endfor %}
```

## `targets.yml` Schema

```json
{
  "title": "TargetCollection",
  "type": "array",
  "items": {
    "$ref": "#/definitions/Target"
  },
  "uniqueItems": true,
  "definitions": {
    "Target": {
      "title": "Target",
      "type": "object",
      "properties": {
        "name": {
          "title": "Name",
          "type": "string"
        },
        "modules": {
          "title": "Modules",
          "default": [],
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "extends": {
          "title": "Extends",
          "default": [],
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "exclude": {
          "title": "Exclude",
          "default": false,
          "type": "boolean"
        },
        "tags": {
          "title": "Tags",
          "default": [],
          "type": "array",
          "items": {
            "type": "string"
          }
        }
      },
      "required": [
        "name"
      ]
    }
  }
}
```
