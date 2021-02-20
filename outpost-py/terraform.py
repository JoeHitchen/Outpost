import os

from python_terraform import Terraform


tf = Terraform(
    working_dir = os.environ.get('TERRAFORM_DIR'),
    terraform_bin_path = os.path.join(os.environ.get('TERRAFORM_DIR'), 'terraform'),
)

status, stdout, stderr = tf.init()
print((status, stdout, stderr))

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



