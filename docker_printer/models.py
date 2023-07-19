import json
import re
from collections import defaultdict
from typing import Any, Dict, Hashable, Iterable, List, Optional, Set, Union

import jinja2
from pydantic import BaseModel, PrivateAttr, validator
from rich import print
from rich.tree import Tree


class CommonListTree:
    class Node:
        def __init__(self):
            self.children = defaultdict(CommonListTree.Node)
            self.labels = set()
            # self.parent: CommonListTree.Node = None

        def merge_list(self, vals: List[Hashable], label: str):
            self.labels.add(label)
            if not vals:
                return

            v, *remaining = vals
            child = self.children[v]
            # child.parent = self
            child.merge_list(remaining, label)

        @property
        def terminal_labels(self):
            return set(self.labels) - {
                lbl for child in self.children.values() for lbl in child.labels
            }

        def tree(self, tree=None) -> Tree:
            for value, child in self.children.items():
                terminals = " ".join(
                    f"[code]{lbl}[/code]" for lbl in child.terminal_labels
                )
                text = f"{value} {terminals}"
                subtree = tree.add(text.strip())
                child.tree(subtree)

        def visit(self, func):
            for value, child in self.children.items():
                func(value, child, self)
                child.visit(func)

    def __init__(self):
        self.root = CommonListTree.Node()

    def merge_list(self, *args, **kwargs):
        self.root.merge_list(*args, **kwargs)

    def tree(self) -> Tree:
        root = Tree("[dim]Dockerfile.synth[/dim]")
        self.root.tree(root)
        return root

    def visit(self, func):
        self.root.visit(func)


class FilledTemplate(BaseModel):
    file: str = "stage.Dockerfile.jinja2"
    variables: Dict[str, Any] = {}

    def render(self, environment: jinja2.Environment):
        return environment.get_template(self.file).render(**self.variables)


class Module(BaseModel):
    __modules__: Dict[str, "Module"] = dict()

    name: str
    depends_on: List[str] = []
    priority: int = 0
    template: FilledTemplate
    image_args: Dict[str, Any] = {}

    _all_modules: Set["Module"] = PrivateAttr(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.name in self.__modules__:
            raise RuntimeError(
                f"Multiple modules defined with the same name: '{self.name}'"
            )
        self.__modules__[self.name] = self

    def __hash__(self):
        return hash(self.name)

    @validator("image_args", pre=True)
    def ensure_is_dictionary(cls, v):
        if isinstance(v, (list, tuple)):
            return {k: None for k in v}
        else:
            return v

    def all_modules(self) -> Set["Module"]:
        if self._all_modules is None:
            self._all_modules = {self} | {
                mod
                for dep in self.depends_on
                for mod in Module.__modules__[dep].all_modules()
            }
        return self._all_modules

    def get_chunk(self, environment: jinja2.Environment, prev_name, cur_name):
        vars = dict(self.template.variables)
        vars.setdefault("base", prev_name)
        vars.setdefault("name", cur_name)
        vars.setdefault("labels", {})
        vars.setdefault("arguments", {})
        vars.setdefault("env", {})
        return environment.get_template(self.template.file).render(**vars)

    def __repr__(self):
        return f"<{type(self).__name__} {self.name}>"

    def __str__(self):
        return self.name


class Target(BaseModel):
    __targets__: Dict[str, "Target"] = {}

    name: str
    modules: List[str] = set()
    extends: List[str] = []
    exclude: bool = False
    tags: List[str] = []

    _all_modules: List[Module] = PrivateAttr(default=None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.name in self.__targets__:
            raise RuntimeError(
                f"Multiple targets defined with the same name: '{self.name}'"
            )
        self.__targets__[self.name] = self

    def __hash__(self):
        return hash(self.name)

    @property
    def _resolved_modules(self):
        return [Module.__modules__[m] for m in self.modules]

    @property
    def _extended_targets(self) -> Set["Target"]:
        return {
            target
            for extended_target in self.extends
            for target in Target.__targets__[extended_target].all_targets()
        }

    def all_targets(self):
        return {self} | self._extended_targets

    def all_modules(self) -> Iterable[Module]:
        if self._all_modules is None:
            modules = {
                mod
                for base_mod in self._resolved_modules
                for mod in base_mod.all_modules()
            } | {
                mod for target in self._extended_targets for mod in target.all_modules()
            }
            self._all_modules = list(
                sorted(modules, key=lambda m: (-m.priority, m.name))
            )

        return self._all_modules

    def render_dockerfile(self, environment: jinja2.Environment):
        image_args = {}
        for mod in self._resolved_modules:
            image_args.update(mod.image_args)

        prev_mod = None
        chunks = []
        for mod in self.all_modules():
            chunks.append(mod.get_chunk(environment, prev_mod.name, mod.name))
            prev_mod = mod

        dockerfile = environment.get_template("base.Dockerfile.jinja2").render(
            image_arguments=image_args, chunks=chunks
        )
        dockerfile = re.sub(r"\n{3,}", r"\n\n", dockerfile)
        return dockerfile

    def __repr__(self):
        return f"<{type(self).__name__} {self.name}>"

    def __str__(self):
        return self.name


class TargetCollection(BaseModel):
    __root__: Set[Target]

    @property
    def targets(self):
        return [t for t in self.__root__ if not t.exclude]

    # def __getitem__(self, item: str) -> Target:
    #     try:
    #         return next(t for t in self.targets if t.name == item)
    #     except StopIteration:
    #         raise KeyError(f"Name {item} not found in target collection")

    def render_dockerfile(
        self, environment: jinja2.Environment, targets: List[str] = ()
    ):
        targets = sorted(self.targets, key=lambda t: t.name)

        pre_image_args = dict()
        for target in targets:
            for module in target.all_modules():
                pre_image_args.update(module.image_args)

        module_tree = CommonListTree()
        for target in targets:
            module_tree.merge_list(target.all_modules(), target.name)

        print(module_tree.tree())
        chunks: Dict[Union[CommonListTree.Node, str], str] = {}
        names = {}
        image_args = {}
        last_chunk_per_target = {}

        def visit_node(
            module: Module, node: CommonListTree.Node, parent: CommonListTree.Node
        ):
            image_args.update(module.image_args)

            if len(node.terminal_labels) == 1:  # This is a terminal node for a target
                cur_name = list(node.terminal_labels)[0]
            elif len(node.labels) == len(targets):  # All targets go through this node
                cur_name = module.name
            else:  # Something in between
                cur_name = "-".join([module.name] + list(sorted(node.labels)))

            for label in node.labels:
                last_chunk_per_target[label] = cur_name

            names[node] = cur_name
            prev_name = names.get(parent)
            chunks[node] = module.get_chunk(environment, prev_name, cur_name)

        module_tree.visit(visit_node)
        for target in targets:
            if target.name not in names.values():
                chunks[target.name] = environment.get_template(
                    "stage.Dockerfile.jinja2"
                ).render(
                    base=last_chunk_per_target[target.name],
                    name=target.name,
                    labels={},
                    arguments={},
                    env={},
                )

        dockerfile = environment.get_template("base.Dockerfile.jinja2").render(
            image_arguments=image_args, chunks=list(chunks.values())
        )
        dockerfile = re.sub(r"\n{3,}", r"\n\n", dockerfile)

        return dockerfile


class BuildConfig(BaseModel):
    name: str
    image: List[str]
    tag_prefix: Optional[str]
    tag_postfix: Optional[str]
    build_args: Dict[str, Any] = {"load": True}
    limit_tags: List[str] = []

    @validator("image", pre=True)
    def ensure_image_is_list(cls, v):
        if not isinstance(v, list):
            return [v]
        return v

    def _render_build_args(self, target: Target, args):
        if isinstance(args, list):
            return [self._render_build_args(target, a) for a in args]
        elif isinstance(args, dict):
            return {k: self._render_build_args(target, v) for k, v in args.items()}
        elif isinstance(args, str):
            for k, v in {
                "${TARGET}": target.name,
            }.items():
                args = args.replace(k, v)
            return args
        else:
            return args

    def generate_bakefile(self, target_collection: TargetCollection):
        def tag_maker(name):
            return "-".join(v for v in [self.tag_prefix, name, self.tag_postfix] if v)

        targets = [
            t
            for t in sorted(target_collection.targets, key=lambda t: t.name)
            if all(tag in t.tags for tag in self.limit_tags)
        ]

        return json.dumps(
            dict(
                group=dict(default=dict(targets=[target.name for target in targets])),
                target={
                    target.name: dict(
                        dockerfile="Dockerfile.synth",
                        tags=[f"{img}:{tag_maker(target.name)}" for img in self.image],
                        target=target.name,
                        **self._render_build_args(target, self.build_args),
                    )
                    for target in targets
                },
            ),
            indent=2,
        )

    @property
    def build_command(self):
        return f"docker buildx bake -f docker-bake.{self.name}.json"


class BuildConfigCollection(BaseModel):
    __root__: List[BuildConfig]
