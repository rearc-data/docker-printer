import subprocess
import textwrap
from pathlib import Path

import click

from .models import TargetCollection, BuildConfigCollection
from .utils import (
    config_dir,
    jinja_env,
    yml_load,
    preload_modules,
    targets_file,
    builds_file,
    base_dir,
)


@click.group()
def cli():
    pass


@cli.command()
def synth():
    _synth()


def _synth():
    preload_modules()

    targets = TargetCollection.parse_obj(yml_load(targets_file()))
    build_configs = BuildConfigCollection.parse_obj(yml_load(builds_file()))

    dockerfile = targets.render_dockerfile(jinja_env())
    dockerfile_path = base_dir() / "Dockerfile.synth"

    click.echo(f"Saving to {dockerfile_path}")
    with open(dockerfile_path, "w", newline="\n") as f:
        f.write(dockerfile)

    for build_config in build_configs.__root__:
        bakefile_path = base_dir() / f"docker-bake.{build_config.name}.json"
        bakefile = build_config.generate_bakefile(targets)
        with open(bakefile_path, "w", newline="\n") as f:
            f.write(bakefile + "\n")
        click.echo(build_config.build_command)

    return targets, build_configs


@cli.command()
@click.argument("name")
def build(name):
    _, build_configs = _synth()

    try:
        config = next(cfg for cfg in build_configs.__root__ if cfg.name == name)
    except StopIteration:
        raise click.Abort(f"No build config found with name '{name}'")

    subprocess.run(config.build_command)


@cli.command()
@click.argument("path", default=Path(), type=click.Path(exists=True, dir_okay=True))
def init(path):
    base_dir = path / "docker-printer"
    if base_dir.exists():
        click.echo(f"{base_dir} already exists, cannot initialize new project")
        raise click.Abort()

    base_dir.mkdir(exist_ok=False, parents=False)
    (base_dir / "modules").mkdir(exist_ok=False, parents=False)
    (base_dir / "templates").mkdir(exist_ok=False, parents=False)
    (base_dir / "targets.yml.jinja2").touch(exist_ok=False)
    (base_dir / "builds.yml.jinja2").touch(exist_ok=False)
    (base_dir / ".gitignore").write_text(
        textwrap.dedent(
            """
            *.rendered.yml
            """.lstrip()
        )
    )


@cli.command()
def version():
    from . import __version__

    print(__version__)
