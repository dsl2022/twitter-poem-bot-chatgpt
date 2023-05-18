import io
import os
import platform
import shutil
import subprocess
import uuid
from zipfile import ZipFile, ZIP_DEFLATED

import boto3

s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')


def execute_os_command(command):
    print('Executing OS command')
    proc = subprocess.Popen(
        [command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = proc.communicate()
    print('Output: ', output),
    print('Error: ', error)
    return output, error


def upgrade_pip(layer_dir):
    print('Upgrading pip')
    pip_upgrade_command = f'{layer_dir}/env/bin/pip install --upgrade pip --no-cache-dir;'
    output, error = execute_os_command(pip_upgrade_command)
    if error and not error.decode('utf8').startswith('WARNING:'):
        raise Exception('Unable to upgrade pip')


def create_virtual_environment(layer_dir):
    print('Creating a virtual environment')
    venv_command = f'python3 -m venv {layer_dir}/env'
    output, error = execute_os_command(venv_command)
    if error and not error.decode('utf8').startswith('WARNING:'):
        raise Exception('Unable to create virtual environment')


def upload_file_to_s3(zip_buffer, s3_bucket_name, s3_key):
    print(f'Uploading zip to s3 at {s3_bucket_name}/{s3_key}')
    response = s3_client.put_object(
        Body=zip_buffer.read(),
        Bucket=s3_bucket_name,
        Key=s3_key,
    )
    print(response)


def create_zip_layer(layer_dir, packages_dir):
    print('Creating a zip file')
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, 'w', ZIP_DEFLATED) as zip_object:
        # Iterate over all the files in directory
        for folder_name, sub_folders, filenames in os.walk(packages_dir):
            for filename in filenames:
                # create complete filepath of file in directory
                file_path = os.path.join(folder_name, filename)
                # Add file to zip
                relative_root = os.path.relpath(folder_name, layer_dir)
                zip_object.write(file_path, os.path.join(
                    relative_root, filename))
    zip_buffer.seek(0)
    print('Zip file creation done.')
    return zip_buffer


def lambda_handler(event, context):
    s3_bucket_name = event['s3Bucket']
    publish_layer = event['publishLayer']
    packages = event['packages']

    print('Creating layer')

    layer_id = str(uuid.uuid4())  # Generate unique layer id
    print(f'Layer ID: {layer_id}')

    # Directories
    layer_dir = f'/tmp/{layer_id}'
    packages_dir = f'{layer_dir}/python'

    try:
        os.makedirs(packages_dir)  # Create required directories
        # Create python virtual environment
        create_virtual_environment(layer_dir)

        if event.get('upgradePip', True):
            upgrade_pip(layer_dir)  # Upgrading pip

        print('Installing packages')
        packages_string = '\n'.join(packages)
        requirements_filepath = f'{layer_dir}/requirements.txt'
        # Create requirements.txt file in lambda /tmp memory
        with open(requirements_filepath, 'w') as requirements_file:
            requirements_file.write(packages_string)

        # Most important pip install command!
        command = f'{layer_dir}/env/bin/pip install -r {requirements_filepath} -t {packages_dir} --no-cache-dir --upgrade; exit 0'

        # Execute the command on lambda using subprocess
        output, error = execute_os_command(command)
        if error and not error.decode('utf8').startswith('WARNING:'):
            print(
                "Error packaging your dependencies. Kindly try again. Contact the developer (^_^) if the issue persists.")
            print(error.decode('utf8'))
            raise Exception('Unable to install packages')

        # If everything goes well then zip the dependencies.
        zip_buffer = create_zip_layer(layer_dir, packages_dir)

        s3_key = f'layers/{layer_id}/python.zip'
        upload_file_to_s3(zip_buffer, s3_bucket_name, s3_key)
        download_link = s3_client.generate_presigned_url('get_object',
                                                         Params={'Bucket': s3_bucket_name,
                                                                 'Key': s3_key},
                                                         ExpiresIn=5 * 60)  # Valid for 5 minutes

        # Publish layer if provided
        if publish_layer:
            layer_name = event.get('layerNameOrArn', f'LayerIt-{layer_id}')
            print(f'Publishing layer {layer_name}')
            architecture = 'arm64' if platform.machine() == 'aarch64' else 'x86_64'
            response = lambda_client.publish_layer_version(
                LayerName=layer_name,
                Description=f'Layer contains {", ".join(packages)}',
                Content={
                    'S3Bucket': s3_bucket_name,
                    'S3Key': s3_key
                },
                CompatibleRuntimes=[os.environ.get(
                    'AWS_EXECUTION_ENV').strip('AWS_Lambda_')],
                # CompatibleArchitectures=[architecture]
            )
            print(response)

        print('Cleaning /tmp directory')
        shutil.rmtree(layer_dir)

        print('Layer creation done.')
        print(f'Download link: {download_link}')
    except Exception as e:
        print(e)
        print('Something went terribly wrong! Contact the developer (^_^) if the issue persists.')
