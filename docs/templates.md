(templates)=
# Templates

`docker-printer` uses `jinja2` for file templating. Templates can be parameterized by [modules](modules) to define chunks of the final dockerfile. In general, templates should probably extend the [chunks template](chunks_template), but entirely custom templates are fine too.

Templates must be defined in `docker-printer/templates/*.jinja2`

## Provided Templates

(chunks_template)=
### `stage.Dockerfile.jinja2`

```{literalinclude} ../docker_printer/resources/templates/stage.Dockerfile.jinja2
:language: dockerfile
```
