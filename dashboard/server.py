import os

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

import utils


server = Flask(__name__)
server.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '___')
socket = SocketIO(server)

update_status = 'update-complete'


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


@socket.on('update-trigger', namespace = '/public/')
def handle_update_trigger() -> None:
    emit('update-trigger', namespace = '/private/', broadcast = True)


@socket.on('update-status', namespace = '/public/')
def handle_update_status_public() -> None:
    emit('update-status', update_status, broadcast = True)


@socket.on('update-status', namespace = '/private/')
def handle_update_status_private(status: str) -> None:
    global update_status
    update_status = status
    emit('update-status', status, namespace = '/public/', broadcast = True)


if __name__ == '__main__':
    socket.run(server, host = '0.0.0.0', port = 8080)

