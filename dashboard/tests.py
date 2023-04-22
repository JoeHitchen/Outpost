from datetime import datetime
from unittest import TestCase
from unittest.mock import patch
from dataclasses import dataclass

import requests

import utils

CREATED_STR = '2022-05-01T12:00:00.000Z'
CREATED = datetime.fromisoformat(CREATED_STR.rstrip('Z'))
DIGEST = 'sha256:6c3c624b58dbbcd3c0dd82b4c53f04194d1247c6eebdaab7c610cf7d66709b3b'


def registry_api_mock(host, should_error = False):
    
    class MockResponse():
        
        def __init__(self, *args, **kwargs):
            self.url = args[0]
            self.ok = not should_error
            self.status_code = 404 if should_error else 200
        
        headers = {
            'Docker-Content-Digest': DIGEST,
        }
        
        def json(self):
            return {
                f'{host}/v2/': {},
                f'{host}/v2/_catalog': {'repositories': ['mock', 'test']},
                f'{host}/v2/mock/tags/list': {
                    'name': 'mock',
                    'tags': ['1.0.1', '1.0.0', '1.1.0', '1.0.2'],
                },
                f'{host}/v2/test/tags/list': {'name': 'test', 'tags': ['2.0.1']},
                f'{host}/v2/mock/manifests/1.0.0': {'history': [
                    {'v1Compatibility': f'{{"created": "{CREATED_STR}"}}'},
                ]},
                f'{host}/v2/mock/manifests/1.0.1': {'history': [
                    {'v1Compatibility': f'{{"created": "{CREATED_STR}"}}'},
                ]},
                f'{host}/v2/mock/manifests/1.1.0': {'history': [
                    {'v1Compatibility': f'{{"created": "{CREATED_STR}"}}'},
                ]},
                f'{host}/v2/mock/manifests/1.0.2': {'history': [
                    {'v1Compatibility': f'{{"created": "{CREATED_STR}"}}'},
                ]},
                f'{host}/v2/test/manifests/2.0.1': {'history': [
                    {'v1Compatibility': f'{{"created": "{CREATED_STR}"}}'},
                ]},
            }[self.url]
        
        def raise_for_status(self):
            raise requests.HTTPError
        
    return MockResponse



class MockDocker():
    
    def __init__(self, base_url):
        self.containers = self.Containers()
    
    @dataclass
    class MockImage():
        tags: list[bool]
    
    @dataclass
    class MockContainer():
        name: str
        image: 'MockDocker.MockImage'
        status: str
        attrs: dict
    
    container_examples = {
        'image': MockContainer(
            name = 'mock_container',
            image = MockImage(tags = ['some_image:tag']),
            status = 'running',
            attrs = {'Created': CREATED_STR},
        ),
        'thing': MockContainer(
            name = 'other_container',
            image = MockImage(tags = ['a_thing:latest']),
            status = 'exited',
            attrs = {'Created': CREATED_STR},
        ),
    }
    
    class Containers():
        def list(self):
            return [MockDocker.container_examples['image'], MockDocker.container_examples['thing']]



class Test__DockerRegistryClient(TestCase):
    
    host = 'https://registry.outpost-iac.uk'
    
    def test__init__hosts(self):
        """The host provided is stored on the client object."""
        
        client = utils.DockerRegistryClient(self.host)
        self.assertEqual(client.host, self.host)
    
    
    def test__init__host_trailing_slash(self):
        """Trailing slashes are removed from the provided host."""
        
        host_with_slash = f'{self.host}/'
        
        client = utils.DockerRegistryClient(host_with_slash)
        self.assertEqual(client.host, self.host)
    
    
    def test__init__verify_ssl_default(self):
        """SSL verification is True by default."""
        
        client = utils.DockerRegistryClient(self.host)
        self.assertTrue(client.verify_ssl)
    
    
    def test__init__verify_ssl_set_false(self):
        """SSL verification can be set False with input."""
        
        client = utils.DockerRegistryClient(self.host, verify_ssl = False)
        self.assertFalse(client.verify_ssl)
    
    
    @patch('requests.get', side_effect = registry_api_mock(host))
    def test__check__success(self, requests_mock):
        """Indicates that the client is able to connect to the registry server."""
        
        client = utils.DockerRegistryClient(self.host)
        self.assertEqual(client.check(), True)  # Checks 'True' is specifically returned
    
    
    @patch('requests.get', side_effect = registry_api_mock(host, should_error = True))
    def test__check__error(self, requests_mock):
        """Raises an error if the request was not successful."""
        
        client = utils.DockerRegistryClient(self.host)
        
        with self.assertRaises(requests.HTTPError):
            client.check()
    
    
    @patch('requests.get', side_effect = registry_api_mock(host))
    def test__list_repositories__success(self, requests_mock):
        """Returns a list of the repositories found on the registry."""
        
        client = utils.DockerRegistryClient(self.host)
        
        self.assertEqual(client.list_repositories(), ['mock', 'test'])
    
    
    @patch('requests.get', side_effect = registry_api_mock(host, should_error = True))
    def test__list_repositories__404_error(self, requests_mock):
        """Raises an error if the request was not successful."""
        
        client = utils.DockerRegistryClient(self.host)
        
        with self.assertRaises(requests.HTTPError):
            client.list_repositories()
    
    
    @patch('requests.get', side_effect = registry_api_mock(host))
    def test__list_repository_tags__success(self, requests_mock):
        """Returns a list of the tags available for an image on the repository."""
        
        client = utils.DockerRegistryClient(self.host)
        
        self.assertEqual(client.list_repository_tags('mock'), ['1.0.1', '1.0.0', '1.1.0', '1.0.2'])
    
    
    @patch('requests.get', side_effect = registry_api_mock(host, should_error = True))
    def test__list_repository_tags__error(self, requests_mock):
        """Raises an error if the request was not successful."""
        
        client = utils.DockerRegistryClient(self.host)
        
        with self.assertRaises(requests.HTTPError):
            client.list_repository_tags('mock')
    
    
    @patch('requests.get', side_effect = registry_api_mock(host))
    def test__get_image__success(self, requests_mock):
        """Returns an Image object (including metadata) for an image/tag combination."""
        
        client = utils.DockerRegistryClient(self.host)
        
        self.assertEqual(
            client.get_image('mock', '1.0.1'),
            utils.Image(name = 'mock', tag = '1.0.1', created = CREATED, digest = DIGEST),
        )
    
    
    @patch('requests.get', side_effect = registry_api_mock(host, should_error = True))
    def test__get_image__error(self, requests_mock):
        """Raises an error if the metadata request was not successful."""
        
        client = utils.DockerRegistryClient(self.host)
        
        with self.assertRaises(requests.HTTPError):
            client.get_image('mock', '1.0.1')



class Test__GetRegistryImages(TestCase):
    
    host = 'https://registry.outpost-iac.uk'
    
    @patch('requests.get', side_effect = registry_api_mock(host))
    def test__success(self, requests_mock):
        """Returns a list of images sorted by reverse tag order."""
        
        images = utils.get_registry_images(self.host)
        self.assertEqual(
            images,
            [
                utils.Image(name = 'mock', tag = '1.1.0', created = CREATED, digest = DIGEST),
                utils.Image(name = 'mock', tag = '1.0.2', created = CREATED, digest = DIGEST),
                utils.Image(name = 'mock', tag = '1.0.1', created = CREATED, digest = DIGEST),
                utils.Image(name = 'mock', tag = '1.0.0', created = CREATED, digest = DIGEST),
                utils.Image(name = 'test', tag = '2.0.1', created = CREATED, digest = DIGEST),
            ],
        )



class Test__GetContainers(TestCase):
    
    host = 'https://dockerd.outpost-iac.uk:2375'
    
    @patch('docker.DockerClient', new = MockDocker)
    def test__success(self):
        
        container_1 = utils.Container(
            name = 'mock_container',
            image = 'some_image:tag',
            status = 'running',
            created = CREATED,
        )
        container_2 = utils.Container(
            name = 'other_container',
            image = 'a_thing:latest',
            status = 'exited',
            created = CREATED,
        )
        
        containers = utils.get_containers(self.host)
        self.assertEqual(containers, [container_1, container_2])

