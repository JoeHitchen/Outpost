import os

from flask import Flask

import utils


server = Flask(__name__)


@server.route('/')
def index() -> str:
    """Creates the main dashboard page."""
    
    with open('registry_page.html') as file:
        return file.read().format(
            registry_contents = create_image_boxes(),
            containers = create_container_boxes(),
        )


def create_image_box(image: utils.Image) -> str:
    """Helper function for displaying a note if there are no images."""
    
    box_styling = 'd-flex justify-content-between align-items-center'
    return '''
          <div class="list-group-item list-group-item-action {box_styling} p-2">
            <div class="fs-4 font-monospace ms-2">{image.name}:{image.tag}</div>
            <div>
              <div class="lh-1">{image.digest:.20s}</div>
              <div class="small text-muted text-end">{image.created}</div>
            </div>
          </div>
    '''.format(image = image, box_styling = box_styling)


@server.route('/images/')
def create_image_boxes() -> str:
    """Loads and generates the HTML for the registry images."""
    
    images = utils.get_registry_images(
        'https://' + os.environ.get('REGISTRY_HOST', ''),
        verify_ssl = os.environ.get('REGISTRY_VERIFY_SSL', '').lower() != 'false',
    )
    if images:
        return ''.join(create_image_box(image) for image in images)
    
    return '''
          <div class="list-group-item list-group-item-action {box_styling} p-2">
            <div class="fs-5 ms-2">{message}</div>
          </div>
    '''.format(
        message = 'No images to show',
        box_styling = 'd-flex justify-content-between align-items-center',
    )


def create_container_box(container: utils.Container) -> str:
    """Helper function for creating the HTML to display individual containers."""
    
    status_colour = 'success' if container.status == 'running' else 'danger'
    return '''
          <div class="list-group-item list-group-item-action {box_styling} p-2">
            <div>
              <span style="width: 1em; height: 1em" class="{status_styling}"></span>
              <span class="fs-4 font-monospace">{container.name}</span>
            </div>
            <div>
              <div class="lh-1">{container.image}</div>
              <div class="small text-muted text-end">{container.created}</div>
            </div>
          </div>
    '''.format(
        container = container,
        box_styling = 'd-flex justify-content-between align-items-center',
        status_styling = f'bg-{status_colour} d-inline-block rounded-circle mx-2',
    )


@server.route('/containers/')
def create_container_boxes() -> str:
    """Loads and generates the HTML for the server containers."""
    
    containers = utils.get_containers(os.environ.get('DOCKER_HOST', ''))
    
    if containers:
        return ''.join(create_container_box(container) for container in containers)
    
    return '''
      <div class="list-group-item list-group-item-action {box_styling} p-2">
        <div>
          <span style="width: 1em; height: 1em" class="{status_styling}"></span>
          <span class="fs-5">{message}</span>
        </div>
      </div>
    '''.format(
        message = 'No containers to show',
        box_styling = 'd-flex justify-content-between align-items-center',
        status_styling = 'bg-danger d-inline-block rounded-circle mx-2',
    )

