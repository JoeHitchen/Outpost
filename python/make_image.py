import random
import os

import image_utils as utils

REGISTRY_HOST = 'registry.outpost'
DATA_DIR = '/tmp'


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


image_short = 'mock:{}'.format(new_version)
image_filename = image_short.replace(':', '-') + '.docker'

utils.build_and_save(
    image_short,
    os.path.join(DATA_DIR, image_filename),
    'mock',
)


