import getpass
import platform
from functools import lru_cache
from importlib import resources
from pathlib import Path

import jinja2
import yaml
from yaml.scanner import ScannerError

from .models import Module


@lru_cache(maxsize=None)
def base_dir(default_to_local=False) -> Path:
    root_dir = Path().resolve()
    while not (root_dir / "docker-printer").exists():
        if root_dir == root_dir.parent:
            if default_to_local:
                return Path().resolve()
            raise RuntimeError(
                "Must run `docker-printer` from a folder that contains a folder "
                "named `docker-printer` (or any subfolder of that top-level directory)"
            )
        root_dir = root_dir.parent
    return root_dir


@lru_cache(maxsize=None)
def config_dir(default_to_local=False) -> Path:
    return base_dir(default_to_local=default_to_local) / "docker-printer"


def base_resources_dir() -> Path:
    with resources.path("docker_printer", "resources") as resources_dir:
        return resources_dir


def jinja_env():
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(
            searchpath=[
                config_dir() / "templates",
                base_resources_dir() / "templates",
            ]
        ),
        auto_reload=True,
    )


def yml_load(path: Path):
    try:
        return yaml.safe_load(path.open())
    except ScannerError as e:
        raise ValueError(f"Invalid YAML file: {path.resolve()}") from e


def preload_modules():
    for root in [base_resources_dir(), config_dir()]:
        for f in (root / "modules").rglob("*.yml"):
            Module.parse_obj(yml_load(f))  # Side effect: stored in Module.__modules__


def targets_file():
    targets_raw_path = config_dir() / "targets.yml"
    targets_template_path = config_dir() / "targets.yml.jinja2"
    targets_rendered_path = config_dir() / "targets.rendered.yml"

    if targets_raw_path.exists() and targets_template_path.exists():
        raise RuntimeError(
            f"Can only have one of {targets_raw_path} or {targets_template_path}"
        )

    elif targets_template_path.exists():
        rendered = jinja2.Template(targets_template_path.read_text()).render()
        targets_rendered_path.write_text(rendered)
        return targets_rendered_path

    elif targets_raw_path.exists():
        return targets_raw_path

    else:
        raise RuntimeError(f"No targets.yml found in {config_dir()}")


def _local_docker_architecture():
    architecture_map = {
        "x86_64": "amd64",
    }
    arch = platform.machine().lower()
    return architecture_map.get(arch, arch)


def builds_file():
    builds_raw_path = config_dir() / "builds.yml"
    builds_template_path = config_dir() / "builds.yml.jinja2"
    builds_rendered_path = config_dir() / "builds.rendered.yml"

    if builds_raw_path.exists() and builds_template_path.exists():
        raise RuntimeError(
            f"Can only have one of {builds_raw_path} or {builds_template_path}"
        )

    elif builds_template_path.exists():
        rendered = jinja2.Template(builds_template_path.read_text()).render(
            username=getpass.getuser(),
            local_architecture=_local_docker_architecture(),
        )
        builds_rendered_path.write_text(rendered)
        return builds_rendered_path

    elif builds_raw_path.exists():
        return builds_raw_path

    else:
        raise RuntimeError(f"No builds.yml found in {config_dir()}")
