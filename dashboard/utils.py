from datetime import datetime
from dataclasses import dataclass
from typing import cast, List
import json

import requests
import docker


@dataclass
class Image():
    name: str
    tag: str
    created: datetime
    digest: str


@dataclass
class Container():
    name: str
    image: str
    created: datetime
    status: str


class DockerRegistryClient():
    """Provides an interface for interacting with the Docker registry API."""
    
    def __init__(self, host: str, verify_ssl: bool = True):
        """Prepares the client for future actions."""
        
        self.host = host.rstrip('/')
        self.verify_ssl = verify_ssl
    
    
    def _make_api_call(self, path: str) -> requests.Response:
        """Internal wrapper for API call boilerplate."""
        
        response = requests.get(f'{self.host}/v2/{path}', verify = self.verify_ssl)
        if not response.ok:
            response.raise_for_status()
        return response
    
    
    def check(self) -> bool:
        """Verifies the access to the registry server using the healthcheck endpoint."""
        return self._make_api_call('').ok
    
    
    def list_repositories(self) -> List[str]:
        """Lists the image repositories available on the registry server."""
        return cast(List[str], self._make_api_call('_catalog').json()['repositories'])
    
    
    def list_repository_tags(self, repository: str) -> List[str]:
        """Lists the tags available for a specific repository."""
        return cast(List[str], self._make_api_call(f'{repository}/tags/list').json()['tags'])
    
    
    def get_image(self, repository: str, tag: str) -> Image:
        """Returns an object describing the Image available."""
        
        response = self._make_api_call(f'{repository}/manifests/{tag}')
        created_string = json.loads(response.json()['history'][0]['v1Compatibility'])['created']
        
        return Image(
            name = repository,
            tag = tag,
            created = datetime.fromisoformat(created_string.split('.')[0]),
            digest = response.headers.get('Docker-Content-Digest', ''),
            # ^ N.B. This is NOT the local "Image ID". To compare run `docker image ls --digests`
        )


def get_registry_images(host: str, verify_ssl: bool = True) -> List[Image]:
    """Returns a list of images available on a registry server, ordered by tag."""
    
    registry = DockerRegistryClient(host, verify_ssl)
    
    images: List[Image] = []
    for repository in registry.list_repositories():
        
        tags = registry.list_repository_tags(repository)
        tags.sort(reverse = True)
        
        images.extend(registry.get_image(repository, tag) for tag in tags)
    
    return images


def get_containers(host: str) -> List[Container]:
    """Returns a list of the containers (active or stopped) on the Docker host."""
    
    server = docker.DockerClient(base_url = host)
    
    containers = []
    for container in server.containers.list():
        
        containers.append(Container(
            name = container.name,
            image = container.image.tags[0],
            created = datetime.fromisoformat(container.attrs['Created'].split('.')[0]),
            status = container.status,
        ))
    
    return containers

