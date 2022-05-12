from datetime import datetime
import json

import requests


class DockerRegistryClient():
    
    def __init__(self, host, verify_ssl = True):
        """Prepares the client for future actions."""
        
        self.host = host.rstrip('/')
        self.verify_ssl = verify_ssl
    
    
    def _make_api_call(self, path):
        """Internal wrapper for API call boilerplate."""
        
        response = requests.get(f'{self.host}/v2/{path}', verify = self.verify_ssl)
        if not response.ok:
            response.raise_for_status()
        return response
    
    
    def check(self):
        """Verifies the access to the registry server using the healthcheck endpoint."""
        return self._make_api_call('').ok
    
    
    def list_repositories(self):
        """Lists the image repositories available on the registry server."""
        return self._make_api_call('_catalog').json()['repositories']
    
    
    def list_repository_tags(self, repository):
        """Lists the tags available for a specific repository."""
        return self._make_api_call(f'{repository}/tags/list').json()['tags']
    
    
    def get_image_metadata(self, repository, tag):
        """Provides the useful metadata for a repository/tag combination."""
        
        response = self._make_api_call(f'{repository}/manifests/{tag}')
        created_string = json.loads(response.json()['history'][0]['v1Compatibility'])['created']
        
        return {
            'created': datetime.fromisoformat(created_string.split('.')[0]),
            'digest': response.headers.get('Docker-Content-Digest'),
            # ^ N.B. This is NOT the local "Image ID". To compare run `docker image ls --digests`
        }


def get_registry_images(host, verify_ssl = True):
    registry = DockerRegistryClient(host, verify_ssl)
    
    images = []
    for repository in registry.list_repositories():
        
        tags = registry.list_repository_tags(repository)
        tags.sort(reverse = True)
        
        for tag in tags:
            
            metadata = registry.get_image_metadata(repository, tag)
            
            images.append({
                'image': repository,
                'tag': tag,
                'created': metadata['created'],
                'digest': metadata['digest'],
            })
    
    return images


