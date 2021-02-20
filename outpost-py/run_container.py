import random
import os

import docker

import image_utils as utils
import gateway


def get_and_bump_version():
    
    with open('version_number.txt') as file:
        version = [int(part) for part in file.read().rstrip().split('.')]
    
    if random.choice([True, False, False]):
        version[2] += 1
        
        if random.choice([True, False, False]):
            version[1] += 1
            version[2] = 0
            
            if random.choice([True, False, False]):
                version[0] += 1
                version[1] = 0
    
    new_version = '.'.join([str(num) for num in version])
    
    with open('version_number.txt', 'w') as file:
        file.write(new_version)
    
    return new_version


if __name__ == '__main__':
    
    REGISTRY_HOST = os.environ.get('REGISTRY_HOST')
    docker_client = docker.from_env()
    
    target_image_version = get_and_bump_version()
    target_image_name = '{}/mock:{}'.format(REGISTRY_HOST, target_image_version)
    print('Loading version {} ...'.format(target_image_version))
    
    if not utils.check_repository_for_image(target_image_name):
        print('{} must be requested'.format(target_image_name))
        
        gateway.request_image_transfer.delay(target_image_name).wait()
        
        assert utils.check_repository_for_image(target_image_name)
    
    for container in docker_client.containers.list(all = True):
        if container.status == 'running':
            container.stop()
        container.remove()
    out = docker_client.containers.run(target_image_name, detach = True, ports = {8000: 8000})
    print(out)

