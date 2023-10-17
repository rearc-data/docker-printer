import os
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


def base_dir_callback(value: str = None):
    # Change CWD to target so path resolution works as expected
    if value:
        resoled_value = Path(value).resolve()
        os.chdir(str(resoled_value))


@app.callback()
def main(
    version: bool = typer.Option(
        None, "--version", callback=version_callback, is_eager=True
    ),
    base_dir: str = typer.Option(
        None, "--basedir", callback=base_dir_callback, is_eager=True
    ),
):
    # Do other global stuff, handle other global options here
    return


@app.command()
def synth():
    """Synthesizes new Dockerfiles from configuration."""
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

    for build_config in build_configs.configs:
        bakefile_path = base_dir() / f"docker-bake.{build_config.name}.json"
        bakefile = build_config.generate_bakefile(targets)
        with open(bakefile_path, "w", newline="\n") as f:
            f.write(bakefile + "\n")
        typer.echo(build_config.build_command)

    return targets, build_configs


@app.command()
def build(name: str = "default"):
    """Builds the current configuration from synthesized Dockerfile(s)."""
    _, build_configs = _synth()

    try:
        config = next(cfg for cfg in build_configs.configs if cfg.name == name)
    except StopIteration:
        names = ", ".join(set([x.name for x in build_configs.configs]))
        typer.secho(
            f"Error: No build config found with name '{name}'", fg=typer.colors.RED
        )
        typer.secho(f"Valid names: {names}", fg=typer.colors.YELLOW)
        typer.Exit(1)
    else:
        typer.echo(config.build_command)
        subprocess.run(config.build_command, shell=True)


@app.command()
def show_config():
    """List the current config files and build targets."""
    preload_modules()

    target_config_file = targets_file()
    build_config_file = builds_file()
    target_configs = TargetCollection.parse_obj(yml_load(target_config_file))
    build_configs = BuildConfigCollection.parse_obj(yml_load(build_config_file))

    typer.secho("Config files", bold=True, fg=typer.colors.GREEN)
    typer.echo(str(target_config_file))
    typer.echo(str(build_config_file))

    typer.secho("\nTargets", bold=True, fg=typer.colors.GREEN)
    for target in target_configs.targets:
        typer.echo(target.name)
        for mod in target.all_modules():
            typer.echo(f"  {mod.name}")
        typer.echo()

    typer.secho("\nBuilds", bold=True, fg=typer.colors.GREEN)
    for build_config in build_configs.configs:
        typer.echo(f"{build_config.name} {build_config.image}")


@app.command()
def init(
    path: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=True,
    )
):
    """Initializes a new project tree."""
    base_dir = path / "docker-printer"
    if base_dir.exists():
        typer.secho(
            f"Error: {base_dir} already exists, cannot initialize new project",
            fg=typer.colors.RED,
        )
        typer.Exit(1)

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
