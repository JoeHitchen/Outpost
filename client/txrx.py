import os

from celery import Celery, result

import image_utils as utils

RX_DATA = os.environ.get('RX_DATA')

txrx = Celery(
    'txrx',
    broker = os.environ.get('TX_MESSAGES'),
    backend = os.environ.get('RX_MESSAGES'),
)


@txrx.task(name = 'txrx.docker_pull')
def request_image_transfer(image_name):
    
    image_name_repoless = '/'.join(image_name.split('/')[1:])
    
    with result.allow_join_result():
        image_meta = transfer_docker_image(image_name_repoless).wait()
    assert image_meta['name'] == image_name_repoless
    
    utils.load_and_push(
        image_name,
        os.path.join(RX_DATA, image_meta['file']),
        image_meta['hash'],
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


