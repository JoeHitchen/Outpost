import os

from celery import Celery, result

import image_utils as utils
import txrx

RX_DATA = os.environ.get('RX_DATA')

gateway = Celery(
    'gateway',
    broker = os.environ.get('GATEWAY_REQUEST'),
    backend = os.environ.get('GATEWAY_RESPONSE'),
)


@gateway.task(name = 'gateway.docker_pull')
def request_image_transfer(image_name):
    
    with result.allow_join_result():
        image_meta = txrx.transfer_docker_image(image_name).wait()
    assert image_meta['name'] == image_name
    
    utils.load_and_push(
        '/'.join([os.environ.get('REGISTRY_HOST'), image_name]),
        os.path.join(RX_DATA, image_meta['file']),
        image_meta['hash'],
    )


