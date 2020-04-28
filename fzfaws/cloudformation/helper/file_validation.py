"""helper functions for file name validations"""
import re
from fzfaws.utils.exceptions import InvalidFileType


def is_yaml(file_name):
    """check if it is yaml file"""
    return re.match(r"^.*\.(yaml|yml)$", file_name)


def is_json(file_name):
    """check if it is json file"""
    return re.match(r"^.*\.json$", file_name)


def check_is_valid(file_name):
    """check if the file is json or yaml

    :param file_name: file path to validate
    :type file_name: str
    :raises InvalidFileType: When the file is not json or yaml
    """
    if not is_yaml(file_name) and not is_json(file_name):
        raise InvalidFileType("Selected file is not a valid template file type")
