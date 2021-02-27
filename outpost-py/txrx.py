import os
import shutil

from celery import Celery
import git

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
    assert repo_name[-4:] == '.git'
    
    # Load existing source repository
    repo_path = os.path.join(os.environ.get('GIT_DATA'), repo_name)
    try:
        repo = git.Repo(repo_path)
    
    # Create new source repository
    except git.exc.NoSuchPathError:
        
        repo = git.Repo.init(repo_path, mkdir = True)
        
        for file in os.listdir(os.environ.get('TERRAFORM_TEMPLATE_PATH')):
            shutil.copy2(os.path.join(os.environ.get('TERRAFORM_TEMPLATE_PATH'), file), repo_path)
        
        index = repo.index
        index.add(repo.untracked_files)
        index.commit('Version 1.0.0')
    
    
    # Get transfer repository name
    transfer_rel_path = os.path.join('git', repo_name)
    if not repo.remotes:
        
        transfer_abs_path = os.path.join(RX_DATA, transfer_rel_path)
        git.Repo.init(transfer_abs_path, bare = True, mkdir = True)
        repo.create_remote('origin', url = transfer_abs_path)
    
    
    # Perform transfer
    commit = repo.commit('master')
    repo.remotes.origin.push('master:master')
    return {
        'repo': repo_name,
        'branch': 'master',
        'hash': commit.hexsha,
        'datetime': commit.committed_datetime,
        'message': commit.message,
        'location': transfer_rel_path,
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


