from typing import TypedDict


class Image():
    tags: list[str]


class ContainerAttrs(TypedDict):
    Created: str


class Container():
    name: str
    image: Image
    status: str
    attrs: ContainerAttrs


class Containers():
    
    def list(self) -> list[Container]:
        ...


class DockerClient():
    
    def __init__(self, base_url: str):
        ...
    
    containers: Containers

