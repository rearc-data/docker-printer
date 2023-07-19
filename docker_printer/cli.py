import subprocess
import textwrap
from pathlib import Path

import typer

from . import __version__
from .models import BuildConfigCollection, TargetCollection
from .utils import (
    base_dir,
    builds_file,
    jinja_env,
    preload_modules,
    targets_file,
    yml_load,
)

app = typer.Typer()


def version_callback(value: bool):
    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
):
    # Do other global stuff, handle other global options here
    return


@app.command()
def synth():
    _synth()


def _synth():
    preload_modules()

    targets = TargetCollection.parse_obj(yml_load(targets_file()))
    build_configs = BuildConfigCollection.parse_obj(yml_load(builds_file()))

    dockerfile = targets.render_dockerfile(jinja_env())
    dockerfile_path = base_dir() / "Dockerfile.synth"

    typer.echo(f"Saving to {dockerfile_path}")
    with open(dockerfile_path, "w", newline="\n") as f:
        f.write(dockerfile)

    for build_config in build_configs.__root__:
        bakefile_path = base_dir() / f"docker-bake.{build_config.name}.json"
        bakefile = build_config.generate_bakefile(targets)
        with open(bakefile_path, "w", newline="\n") as f:
            f.write(bakefile + "\n")
        typer.echo(build_config.build_command)

    return targets, build_configs


@app.command()
def build(name: str):
    _, build_configs = _synth()

    try:
        config = next(cfg for cfg in build_configs.__root__ if cfg.name == name)
    except StopIteration:
        raise typer.Abort(f"No build config found with name '{name}'")

    subprocess.run(config.build_command)


@app.command()
def init(
    path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=True,
    )
):
    base_dir = path / "docker-printer"
    if base_dir.exists():
        typer.echo(f"{base_dir} already exists, cannot initialize new project")
        raise typer.Abort()

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
