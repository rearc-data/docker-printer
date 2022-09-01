(synthesize)=
# Synthesize

To synthesize the dockerfile and bake configuration files, just run:

```
docker-printer synth
```

This generates a `Dockerfile.synth` file and `docker-bake.<name>.json` files for each build config.

From here on out, you can use standard docker and `docker buildx` tooling to build your images.
