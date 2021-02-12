import random

import docker


with open('mock/version_number.txt') as file:
    version = [int(part) for part in file.read().split('.')]


if random.choice([True]):
    version[2] += 1
    
    if random.choice([True, False]):
        version[1] += 1
        version[2] = 0
        
        if random.choice([True, False, False]):
            version[0] += 1
            version[1] = 0

new_version = '.'.join([str(num) for num in version])

with open('mock/version_number.txt', 'w') as file:
    file.write(new_version)

print('Releasing version {}'.format(new_version))

new_image = 'registry.outpost/mock:{}'.format(new_version)

client = docker.from_env()
client.images.build(path = 'mock', tag = new_image)
client.images.push(new_image)


