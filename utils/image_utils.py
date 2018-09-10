import os
from enum import Enum
from uuid import uuid1

from flask import current_app, send_from_directory

ALLOWED_EXTENSION = ['png', 'jpg', 'jpeg']


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSION


def save_file(file, folder, tag1):
    try:
        # Check to assure file is accepted image type.
        if not allowed_file(file.filename):
            return None

        # Make a new file based on two ids. For contracts its issuer_id, and the contract_id.
        file_type = file.filename.split('.')[1].lower()
        new_file_name = "{}_{}.{}".format(tag1, uuid1(), file_type)

        # Generate the full path of where to save the file.
        file_save_path = os.path.join(*[current_app.root_path, 'PICTURES', folder, new_file_name])

        # Save the file and return the new filename for retrieval if needed later.
        file.save(file_save_path)
        return new_file_name
    except Exception as e:
        print(str(e))
        return None


def serve_file(name, folder_type):
    # Specify location to look into.
    if folder_type == ImageFolders.CONTRACTS.value:
        folder = os.path.join(*[current_app.root_path, 'PICTURES', ImageFolders.CONTRACTS.value])
    else:
        folder = None
    return send_from_directory(folder, name)


class ImageFolders(Enum):
    CONTRACTS = 'CONTRACTS'
