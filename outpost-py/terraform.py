import os
import re
import logging
import random
from copy import copy

from python_terraform import Terraform

import gateway

logging.basicConfig(level = logging.ERROR)
logger = logging.getLogger('Terraform')
logger.setLevel(logging.INFO)


def bump_image_version():
    with open(os.path.join(os.environ.get('TERRAFORM_DIR'), 'main.tf')) as file:
        lines = file.read().splitlines()
    
    regex_str = 'data "docker_registry_image" "\w+" {'
    for line_num in range(0, len(lines)):
        if re.match(regex_str, lines[line_num]):
            break
    
    old_version = None
    for line in lines[line_num+1:]:
        line_num += 1
        match = re.match('.*(?P<version>\d\.\d\.\d).*', line)
        if match:
            old_version = [int(part) for part in match.group('version').split('.')]
            break
    
    if not old_version:
        raise Exception('Didn\'t find old version')
    
    version = copy(old_version)
    if random.choice([True, False, False]):
        version[2] += 1
        
        if random.choice([True, False, False]):
            version[1] += 1
            version[2] = 0
            
            if random.choice([True, False, False]):
                version[0] += 1
                version[1] = 0
    
    lines[line_num] = re.sub(
        '.'.join(str(part) for part in old_version),
        '.'.join(str(part) for part in version),
        lines[line_num],
    )
    with open(os.path.join(os.environ.get('TERRAFORM_DIR'), 'main.tf'), 'w') as file:
        file.write('\n'.join(lines))


def identify_missing_image(stderr):
    match = None
    regex_str = '  on (?P<file>\w+.tf) line (?P<line>\d+), in data "docker_registry_image" "\w+":'
    for line in stderr.split('\n'):
        match = re.match(regex_str, line)
        if match:
            break
    
    if not match:
        raise ValueError(stderr)
    
    with open(os.path.join(os.environ.get('TERRAFORM_DIR'), match.group('file'))) as file:
        lines = file.read().splitlines()
    
    assert lines[int(match.group('line'))-1][:28] == 'data "docker_registry_image"'
    resource_lines = []
    for line in lines[int(match.group('line')):]:
        if re.match('\s*}\s*', line):
            break
        resource_lines.append(line)
    
    image = None
    for line in resource_lines:
        match = re.match('\s*name\s*=\s*"(?P<image>.*)"\s*', line)
        if match:
            image = match.group('image').split('/')[-1]
    assert image
    
    return image


def run_terraform():
    logger.info('Running Terraform')
    
    # Prepare Terraform
    tf = Terraform(
        working_dir = os.environ.get('TERRAFORM_DIR'),
        terraform_bin_path = os.path.join(os.environ.get('TERRAFORM_DIR'), 'terraform'),
    )
    
    # Initialise Terraform configuration
    status, stdout, stderr = tf.init()
    if status:
        for line in stderr.split('\n'):
            logger.error(line)
        raise Exception('`terraform init` failed')
    for line in stdout.split('\n'):
        logger.debug(line)
    
    # Iterate Terraform apply attempts
    count = 0
    retry = True
    while retry and count < 10:
        count += 1
        retry = False
        
        # Attempt apply
        logger.info('Apply attempt #{}'.format(count))
        status, stdout, stderr = tf.apply(
            var = {
                'docker_host': os.environ.get('DOCKER_HOST'),
                'registry_host': os.environ.get('REGISTRY_HOST'),
            },
            skip_plan = True,
            # ^ `skip_plan` replaces auto-approve, intentionally or otherwise
            # https://github.com/beelit94/python-terraform/issues/84#issuecomment-648896385
        )
        
        # Record success and exit
        if not status:
            logger.info('Apply successful')
            for line in stdout.split('\n'):
                logger.debug(line)
            return
        
        # Log apply error
        logger.info('Apply failed')
        for line in stderr.split('\n'):
            logger.debug(line)
        
        # Attempt resolution
        if status:
            
            # Missing Docker image?
            missing_image = identify_missing_image(stderr)
            if missing_image:
                logger.info('Identified missing Docker image - {}'.format(missing_image))
                gateway.request_image_transfer.delay(missing_image).wait()
                retry = True
                continue
    
    # Accept defeat
    logger.error('Apply iteration failed to succeed in {} attempts'.format(count))
    raise Exception('`terraform apply` failed too many times')


if __name__ == '__main__':
    bump_image_version()
    run_terraform()


