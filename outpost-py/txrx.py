import os
import shutil
import re
from copy import copy
import random

from celery import Celery
import git

import image_utils as utils

RX_DATA = os.environ.get('RX_DATA')
TXRX_DELAY = int(os.environ.get('TXRX_DELAY') or '15')

txrx = Celery(
    'txrx',
    broker = os.environ.get('TXRX_REQUEST'),
    backend = os.environ.get('TXRX_RESPONSE'),
)


def bump_image_version(file_path):
    with open(file_path) as file:
        lines = file.read().splitlines()
    
    regex_str = 'data "docker_registry_image" "\w+" {'  # noqa: W605
    for line_num in range(0, len(lines)):
        if re.match(regex_str, lines[line_num]):
            break
    
    old_version = None
    for line in lines[line_num + 1:]:
        line_num += 1
        match = re.match('.*(?P<version>\d\.\d\.\d).*', line)  # noqa: W605
        if match:
            old_version = [int(part) for part in match.group('version').split('.')]
            break
    
    if not old_version:
        raise Exception("Didn't find old version")
    
    # Decide if updates should be performed
    if not random.choice([True, False, False]):
        return '.'.join(str(part) for part in old_version)
    
    # Bump version
    version = copy(old_version)
    version[2] += 1
    
    if random.choice([True, False, False]):
        version[1] += 1
        version[2] = 0
        
        if random.choice([True, False, False]):
            version[0] += 1
            version[1] = 0
    
    # Update configuration
    version_str = '.'.join(str(part) for part in version)
    lines[line_num] = re.sub(
        '.'.join(str(part) for part in old_version),
        '.'.join(str(part) for part in version),
        lines[line_num],
    )
    with open(file_path, 'w') as file:
        file.write('\n'.join(lines))
        file.write('\n')
    
    return version_str


def transfer_git_history(repo_name):
    return _transfer_git_history.apply_async((repo_name,), countdown = TXRX_DELAY)


@txrx.task(name = 'txrx.transfer_git_history')
def _transfer_git_history(repo_name):
    assert repo_name[-4:] == '.git'
    
    # Load existing source repository
    repo_path = os.path.join(os.environ.get('GIT_DATA'), repo_name)
    try:
        repo = git.Repo(repo_path)
        version = bump_image_version(os.path.join(repo_path, 'main.tf'))
    
    # Create new source repository
    except git.exc.NoSuchPathError:
        
        repo = git.Repo.init(repo_path, mkdir = True)
        version = '1.0.0'
        shutil.copytree(
            os.environ.get('TERRAFORM_TEMPLATE_PATH'),
            repo_path,
            ignore = shutil.ignore_patterns('.terraform'),
            dirs_exist_ok = True,
        )
        
    # Commit changes
    if (not repo.branches) or repo.is_dirty():
        index = repo.index
        index.add(repo.untracked_files)
        index.add([changed.a_path for changed in index.diff(None)])
        index.commit('Version {}'.format(version))
    
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
    return _transfer_docker_image.apply_async((image_name,), countdown = TXRX_DELAY)


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


