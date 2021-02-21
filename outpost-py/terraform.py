import os
import re

from python_terraform import Terraform

import gateway


def identify_missing_containers(stderr):
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


if __name__ == '__main__':
    
    tf = Terraform(
        working_dir = os.environ.get('TERRAFORM_DIR'),
        terraform_bin_path = os.path.join(os.environ.get('TERRAFORM_DIR'), 'terraform'),
    )
    
    status, stdout, stderr = tf.init()
    print((status, stdout, stderr))
    
    count = 0
    retry = True
    while retry and count < 10:
        count += 1
        retry = False
        
        status, stdout, stderr = tf.apply(
            var = {
                'docker_host': os.environ.get('DOCKER_HOST'),
                'registry_host': os.environ.get('REGISTRY_HOST'),
            },
            skip_plan = True,
            # ^ `skip_plan` replaces auto-approve, intentionally or otherwise
            # https://github.com/beelit94/python-terraform/issues/84#issuecomment-648896385
        )
        print((status, stdout, stderr))
        if status:
            missing_image = identify_missing_containers(stderr)
            gateway.request_image_transfer.delay(missing_image).wait()
            retry = True


