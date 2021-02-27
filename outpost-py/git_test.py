import os

from git import Repo

import gateway


repo_name = 'repo.git'
git_fetch = gateway.request_git_fetch.delay(repo_name).wait()
print(git_fetch)

repo = Repo.init(os.path.join(os.environ.get('TERRAFORM_DIR'), repo_name), mkdir = True)
if not repo.remotes:
    repo.create_remote('origin', url = '{}/{}'.format(os.environ.get('GIT_HOST'), repo_name))
repo.remotes.origin.pull('master:master')

print(os.listdir(os.path.join(os.environ.get('TERRAFORM_DIR'), repo_name)))


