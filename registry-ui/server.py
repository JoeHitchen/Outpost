from http.server import BaseHTTPRequestHandler, HTTPServer
import os

import utils

hostName = '0.0.0.0'
serverPort = 8080


def create_image_box(image: utils.Image) -> str:
    """Helper function for creating the HTML to display individual images."""
    
    box_styling = 'd-flex justify-content-between align-items-center'
    return '''
          <div class="list-group-item list-group-item-action {box_styling}">
            <div class="fs-3 mb-2">{image.name}:{image.tag}</div>
            <div>
              <div>{image.digest:.20s}</div>
              <div class="small text-muted text-end">{image.created}</div>
            </div>
          </div>
    '''.format(image = image, box_styling = box_styling)


def create_container_box(container: utils.Container) -> str:
    """Helper function for creating the HTML to display individual containers."""
    
    status_colour = 'success' if container.status == 'running' else 'danger'
    return '''
          <div class="list-group-item list-group-item-action {box_styling}">
            <div class="mb-2">
              <span style="width: 1em; height: 1em" class="{status_styling}"></span>
              <span class="fs-3">{container.name}</span>
            </div>
            <div>
              <div>{container.image}</div>
              <div class="small text-muted text-end">{container.created}</div>
            </div>
          </div>
    '''.format(
        container = container,
        box_styling = 'd-flex justify-content-between align-items-center',
        status_styling = f'bg-{status_colour} d-inline-block rounded-circle',
    )


class RegistryUiServer(BaseHTTPRequestHandler):
    """A simple server class for rendering the contents of a registry."""
    
    def do_GET(self) -> None:
        """Handle all GET requests."""
        
        # Generate image boxes
        images = utils.get_registry_images(
            'https://' + os.environ.get('REGISTRY_HOST', ''),
            verify_ssl = os.environ.get('REGISTRY_VERIFY_SSL', '').lower() != 'false',
        )
        image_boxes = [create_image_box(image) for image in images]
        
        containers = utils.get_containers(os.environ.get('DOCKER_HOST', ''))
        container_boxes = [create_container_box(container) for container in containers]
        
        # Generate full page
        with open('registry_page.html') as file:
            page = file.read().format(
                registry_contents = ''.join(image_boxes),
                containers = ''.join(container_boxes),
            )
        
        # Send reponse
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(page, 'utf-8'))


if __name__ == '__main__':
    
    webServer = HTTPServer((hostName, serverPort), RegistryUiServer)
    print('Server started http://%s:%s' % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print('Server stopped.')

