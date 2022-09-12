[![Documentation Status](https://readthedocs.org/projects/docker-printer/badge/?version=latest)](https://docker-printer.readthedocs.io/en/latest/?badge=latest) ![PyPI](https://img.shields.io/pypi/v/docker-printer)

# Docker-Printer

`docker-printer` is a CLI for easily managing multistep and branching dockerfiles.

Regular multi-stage dockerfiles and `docker build` commands are incredibly powerful and useful; however, they are designed for building a single image. Multistage builds can be used to define multiple related images, but this quickly results in complicated dockerfiles, possibly duplicated instructions, and complicated collections of build commands.

`docker-printer` addresses this in two main ways:
- By allowing dockerfiles to be composed from re-usable modules.
- By building bake files for use by `docker buildx bake` that consolidate the build processes of multiple images in multiple environments into a single configuration file.

# Getting Started and Documentation

```
pip install docker-printer
docker-printer init
```

See the [documentation](https://docker-printer.readthedocs.io/en/latest/#) for how to get started.

There are also example docker constructs provided in the `/examples` folder.
