import os

import image_utils as utils

RX_DATA = os.environ.get('RX_DATA')


def request_image_transfer(image_name):
    
    image_short = image_name.split('/')[1]
    image_filename = image_short.replace(':', '.') + '.docker'
     
    utils.build_and_save(
        image_short,
        os.path.join(RX_DATA, image_filename),
        'mock',
    )
    
    utils.load_and_push(
        image_name,
        os.path.join(RX_DATA, image_filename),
    )


