import docker


def check_repository_for_image(image_name):
    
    try:
        meta = docker.from_env().images.get_registry_data(image_name)
        print('{} is available'.format(image_name))
        return meta
    
    except docker.errors.APIError:
        print('{} unavailable'.format(image_name))
        return False


def build_and_save(image_name, image_path, build_path):
    print('Building {} as {} ...'.format(build_path, image_name))
    
    image, _ = docker.from_env().images.build(
        path = build_path,
        tag = image_name,
        buildargs = {'IMAGE_NAME': image_name},
    )
    
    print('Saving {} to {} ...'.format(image_name, image_path))
    with open(image_path, 'wb') as file:
        for chunk in image.save():
            file.write(chunk)
    
    return {
        'name': image_name,
        'hash': image.id,
        'hash_short': image.short_id,
    }


def load_and_push(image_name, image_path, image_hash):
    print('Loading {} from {} ...'.format(image_name, image_path))
    
    images = docker.from_env().images
    image_name_parts = image_name.split(':')
    
    with open(image_path, 'rb') as file:
        image = images.load(file.read())[0]
    
    if image.id != image_hash:
    	raise ValueError('Loaded image hash does not match expected value')
    
    image.tag(repository = image_name_parts[0], tag = image_name_parts[1])
    
    print('Pushing {} ...'.format(image_name))
    images.push(repository = image_name_parts[0], tag = image_name_parts[1])


