import sys
import os

import image_utils as utils

REGISTRY_HOST = os.environ.get('REGISTRY_HOST')
RX_DATA = os.environ.get('RX_DATA')

try:
    version = sys.argv[1]
except IndexError:
    raise IndexError('Must provide version number as command line argument')


image_short = 'mock:{}'.format(version)
image_filename = image_short.replace(':', '-') + '.docker'

utils.load_and_push(
    '{}/{}'.format(REGISTRY_HOST, image_short),
    os.path.join(RX_DATA, image_filename),
)


