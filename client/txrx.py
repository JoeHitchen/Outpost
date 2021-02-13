import os

from celery import Celery

import image_utils as utils

RX_DATA = os.environ.get('RX_DATA')

txrx = Celery(
    'txrx',
    broker = os.environ.get('TXRX_QUEUE'),
    backend = os.environ.get('TXRX_RESULTS'),
)


@txrx.task(name = 'txrx.docker_pull')
def request_image_transfer(image_name):
    
    image_short = image_name.split('/')[1]
    image_filename = image_short.replace(':', '.') + '.docker'
     
    image_meta = utils.build_and_save(
        image_short,
        os.path.join(RX_DATA, image_filename),
        'mock',
    )
    
    utils.load_and_push(
        image_name,
        os.path.join(RX_DATA, image_filename),
        image_meta['hash'],
    )


