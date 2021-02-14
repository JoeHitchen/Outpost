import os

from celery import Celery

import image_utils as utils

RX_DATA = os.environ.get('RX_DATA')

txrx = Celery(
    'txrx',
    broker = os.environ.get('TX_MESSAGES'),
    backend = os.environ.get('RX_MESSAGES'),
)


def transfer_docker_image(image_name):
    return _transfer_docker_image.apply_async((image_name,), countdown = 15)


@txrx.task(name = 'txrx.transfer_docker_image')
def _transfer_docker_image(image_name):
    
    image_filename = image_name.replace(':', '-') + '.docker'
    
    image_meta = utils.build_and_save(
        image_name,
        os.path.join(RX_DATA, image_filename),
        'mock',
    )
    
    image_meta['file'] = image_filename
    return image_meta


