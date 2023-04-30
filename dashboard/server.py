import os

from flask import Flask, render_template

import utils


server = Flask(__name__)


@server.route('/')
def index() -> str:
    """Creates the main dashboard page."""
    
    images = utils.get_registry_images(
        'https://' + os.environ.get('REGISTRY_HOST', ''),
        verify_ssl = os.environ.get('REGISTRY_VERIFY_SSL', '').lower() != 'false',
    )
    containers = utils.get_containers(os.environ.get('DOCKER_HOST', ''))
    
    return render_template('index_page.html', images = images, containers = containers)


@server.route('/images/')
def create_image_boxes() -> str:
    """Loads and generates the HTML for the registry images."""
    
    images = utils.get_registry_images(
        'https://' + os.environ.get('REGISTRY_HOST', ''),
        verify_ssl = os.environ.get('REGISTRY_VERIFY_SSL', '').lower() != 'false',
    )
    return render_template('images.html', images = images)


@server.route('/containers/')
def create_container_boxes() -> str:
    """Loads and generates the HTML for the server containers."""
    
    containers = utils.get_containers(os.environ.get('DOCKER_HOST', ''))
    return render_template('containers.html', containers = containers)

