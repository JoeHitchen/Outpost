import os

from celery import Celery, result

import image_utils as utils
import txrx

RX_DATA = os.environ.get('RX_DATA')

gateway = Celery(
    'middleware',
    broker = os.environ.get('GATEWAY_REQUEST'),
    backend = os.environ.get('GATEWAY_RESPONSE'),
)


@gateway.task(name = 'gateway.docker_pull')
def request_image_transfer(image_name):
    
    image_name_repoless = '/'.join(image_name.split('/')[1:])
    
    with result.allow_join_result():
        image_meta = txrx.transfer_docker_image(image_name_repoless).wait()
    assert image_meta['name'] == image_name_repoless
    
    utils.load_and_push(
        image_name,
        os.path.join(RX_DATA, image_meta['file']),
        image_meta['hash'],
    )


