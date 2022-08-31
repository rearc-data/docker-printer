import shutil
import subprocess
from pathlib import Path

import click

from .models import TargetCollection, BuildConfig, BuildConfigCollection
from .utils import (
    config_dir,
    jinja_env,
    yml_load,
    preload_modules,
    targets_file,
    builds_file,
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
    dockerfile_path = Path("Dockerfile.synth")

    click.echo(f"Saving to {dockerfile_path}")
    dockerfile_path.write_text(dockerfile)

    for build_config in build_configs.__root__:
        bakefile_path = Path(f"docker-bake.{build_config.name}.json")
        bakefile = build_config.generate_bakefile(targets)
        bakefile_path.write_text(bakefile)
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
def init():
    base_dir = config_dir()
    if base_dir.exists():
        click.echo(f"{base_dir} already exists, cannot initialize new project")
        raise click.Abort()

    base_dir.mkdir(exist_ok=False, parents=False)
    (base_dir / "modules").mkdir(exist_ok=False, parents=False)
    (base_dir / "templates").mkdir(exist_ok=False, parents=False)
    (base_dir / "targets.yml.jinja2").touch(exist_ok=False)
    (base_dir / "builds.yml.jinja2").touch(exist_ok=False)
