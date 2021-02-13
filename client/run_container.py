import os

import docker


if __name__ == '__main__':
    
    REGISTRY_HOST = os.environ.get('REGISTRY_HOST')
    docker_client = docker.from_env()
    
    target_image_version = '1.0.0'
    target_image_name = '{}/mock:{}'.format(REGISTRY_HOST, target_image_version)
    
    try:
        target_image_meta = docker_client.images.get_registry_data(target_image_name)
    except docker.errors.APIError:
        raise LookupError('Need to make request for image')
    
    
    out = docker_client.containers.run(target_image_name)
    print(out)


