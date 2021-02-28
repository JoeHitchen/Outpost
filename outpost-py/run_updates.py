import os
import logging

import git

import gateway


logging.basicConfig(level = logging.ERROR)
logger = logging.getLogger('Updates')
logger.setLevel(logging.INFO)


def check_for_updates(app_name, app_work_dir):
    
    # Request remote update
    gateway.request_git_fetch.delay(app_name + '.git').wait()
    
    # Update local working directory
    app_repo = git.Repo.init(app_work_dir, mkdir = True)
    if not app_repo.remotes:
        app_git_remote = '{}/{}.git'.format(os.environ.get('GIT_HOST'), app_name)
        app_repo.create_remote('origin', url = app_git_remote)
    pull = app_repo.remotes.origin.pull('master:master')[0]
    
    # Log and return update status
    if pull.flags != git.remote.FetchInfo.HEAD_UPTODATE:
        logger.info('App "{}" has updates'.format(app_name))
        return True
    else:
        logger.info('App "{}" does not have updates'.format(app_name))
        return False


if __name__ == '__main__':
    
    app_name = 'target'
    app_work_dir = os.path.join(os.environ.get('TERRAFORM_DIR'), app_name)
    
    has_updates = check_for_updates(app_name, app_work_dir)


