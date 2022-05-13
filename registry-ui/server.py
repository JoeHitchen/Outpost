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
            <div class="fs-3 pb-1">{image.name}:{image.tag}</div>
            <div>
              <div>{image.created}</div>
              <div class="small text-muted text-end">{image.digest:.15s}</div>
            </div>
          </div>
    '''.format(image = image, box_styling = box_styling)


class RegistryUiServer(BaseHTTPRequestHandler):
    
    
    def do_GET(self) -> None:
        """Handle all GET requests."""
        
        # Generate image boxes
        images = utils.get_registry_images(
            'https://' + os.environ.get('REGISTRY_HOST', ''),
            verify_ssl = os.environ.get('REGISTRY_VERIFY_SSL', '').lower() != 'false',
        )
        image_boxes = [create_image_box(image) for image in images]
        
        # Generate full page
        with open('registry_page.html') as file:
            page = file.read().format(registry_contents = ''.join(image_boxes))
        
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

