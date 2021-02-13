import docker


def load_and_push(image_name, image_path):
    print('Loading {} from {} ...'.format(image_name, image_path))
    
    images = docker.from_env().images
    image_name_parts = image_name.split(':')
    
    with open(image_path, 'rb') as file:
        image = images.load(file.read())[0]
    
    image.tag(repository = image_name_parts[0], tag = image_name_parts[1])
    
    print('Pushing {} ...'.format(image_name))
    images.push(repository = image_name_parts[0], tag = image_name_parts[1])
    
    try:
        images.get_registry_data(image_name)
        print('{} now available'.format(image_name))
        return True
    
    except docker.errors.APIError:
        print('{} unavailable'.format(image_name))
        return False


