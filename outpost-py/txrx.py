import os

from celery import Celery
from git import Repo

import image_utils as utils

RX_DATA = os.environ.get('RX_DATA')

txrx = Celery(
    'txrx',
    broker = os.environ.get('TXRX_REQUEST'),
    backend = os.environ.get('TXRX_RESPONSE'),
)


def transfer_git_history(repo_name):
    return _transfer_git_history.apply_async((repo_name,), countdown = 1)


@txrx.task(name = 'txrx.transfer_git_history')
def _transfer_git_history(repo_name):
    
    repo_path = os.path.join(os.environ.get('GIT_DATA'), repo_name)
    print(repo_path)
    
    repo = Repo.init(repo_path, mkdir = True)
    
    with open(os.path.join(repo_path, 'text.txt'), 'w') as file:
        file.write('test')
    
    index = repo.index
    index.add(repo.untracked_files)
    index.commit('Version 1.0.0')
    
    commit = repo.commit('master')
    
    return {
        'repo': repo_name,
        'branch': 'master',
        'hash': commit.hexsha,
        'datetime': commit.committed_datetime,
        'message': commit.message,
    }


def transfer_docker_image(image_name):
    return _transfer_docker_image.apply_async((image_name,), countdown = 15)


@txrx.task(name = 'txrx.transfer_docker_image')
def _transfer_docker_image(image_name):
    
    image_filename = image_name.replace(':', '-') + '.docker'
    
    image_meta = utils.build_and_save(
        image_name,
        os.path.join(RX_DATA, image_filename),
        os.environ.get('DOCKER_BUILD_DIR'),
    )
    
    image_meta['file'] = image_filename
    return image_meta


