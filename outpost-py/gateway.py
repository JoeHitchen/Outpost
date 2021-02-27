import os

from celery import Celery, result
import git

import image_utils as utils
import txrx

RX_DATA = os.environ.get('RX_DATA')

gateway = Celery(
    'middleware',
    broker = os.environ.get('GATEWAY_REQUEST'),
    backend = os.environ.get('GATEWAY_RESPONSE'),
)


@gateway.task(name = 'gateway.git_fetch')
def request_git_fetch(repo_name):
    assert repo_name[-4:] == '.git'
    
    with result.allow_join_result():
        reply = txrx.transfer_git_history(repo_name).wait()
    
    source_repo = git.Repo(os.path.join(RX_DATA, reply['location']))
    assert source_repo.commit(reply['branch']).hexsha == reply['hash']
    
    if not source_repo.remotes:
        remote_url = os.path.join(os.environ.get('GIT_HOST'), repo_name)
        git.Repo.init(':'.join(remote_url.split(':')[1:])[2:], bare = True, mkdir = True)
        source_repo.create_remote('origin', url = remote_url)
    
    source_repo.remotes.origin.push('master:master')
    
    reply.pop('location')
    return reply


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


