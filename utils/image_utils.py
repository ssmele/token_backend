import os
from enum import Enum
from uuid import uuid1

from flask import current_app, send_from_directory

from utils.utils import log_kv, LOG_ERROR

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


def save_qrcode(file, tag0, tag1):
    """
    This method saves a qr code.
    :param file: PIL IMAGE.
    :param tag0: should be con_id of the contract.
    :param tag1: should be t_id of the contract.
    :return: filename of newly saved qrcode.
    """
    try:
        file_type = 'png'
        new_file_name = "{}-{}_{}.{}".format(tag0, tag1, uuid1(), file_type)
        # Generate the full path of where to save the file.
        file_save_path = os.path.join(*[current_app.root_path, 'PICTURES', ImageFolders.QR_CODES.value, new_file_name])
        file.save(file_save_path)
        return new_file_name
    except Exception as e:
        log_kv(LOG_ERROR, {"info": "Error saving qr code", "error": str(e)}, exception=True)
        return None


def serve_file(name, folder_type):
    # Specify location to look into.
    folder = os.path.join(*[current_app.root_path, 'PICTURES', folder_type])
    return send_from_directory(folder, name)


class ImageFolders(Enum):
    CONTRACTS = 'CONTRACTS'
    QR_CODES = 'QR_CODES'
