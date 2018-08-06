import logging
import os
import sys
from pathlib import Path
import magic

from helperFunctions.dataConversion import make_unicode_string
from common_helper_process.fail_safe_subprocess import execute_shell_command_get_return_code


def get_src_dir():
    '''
    Returns the absolute path of the src directory
    '''
    return get_parent_dir(get_directory_of_current_file())


def get_test_data_dir():
    '''
    Returns the absolute path of the test data directory
    '''
    return os.path.join(get_src_dir(), 'test/data')


def get_faf_bin_dir():
    '''
    Returns the absolute path of the bin directory
    '''
    return os.path.join(get_src_dir(), 'bin')


def get_template_dir():
    '''
    Returns the absolute path of the template directory
    '''
    return os.path.join(get_src_dir(), 'web_interface/templates')


def get_directory_of_current_file():
    return os.path.dirname(os.path.abspath(__file__))


def get_parent_dir(dir_path):
    dir_path = dir_path.split('/')
    dir_path = dir_path[0:len(dir_path) - 1]
    dir_path = '/'.join(dir_path)
    return dir_path


def get_absolute_path(path, base_dir=os.getcwd()):
    '''
    Returns path if path is absolute
    Returns base_dir/path if path is relative
    '''
    if path[0] == '/':
        return path
    else:
        return os.path.join(base_dir, path)


def get_chroot_path(absolute_path, base_path):
    '''
    set new root for path
    example:
    input: absolute_path=/foo/bar/abc, base_path=/foo/
    output: /bar/abc
    '''
    if absolute_path[0:len(base_path)] == base_path:
        new_path = absolute_path[len(base_path):len(absolute_path)]
        if new_path[0] != '/':
            new_path = '/{}'.format(new_path)
        return new_path
    else:
        return absolute_path


def get_chroot_path_excluding_extracted_dir(absolute_path, base_path):
    '''
    like get_chroot_path but removing 'faf_extracted' dir as well
    '''
    tmp = get_chroot_path(absolute_path, base_path)
    return get_chroot_path(tmp, '/faf_extracted')


def get_file_type_from_path(file_path):
    '''
    This functions returns a dict with the file's mime- and full-type.
    It uses the custom mime database found in src/bin/custommime.mgc
    If no match was found, it uses the standard system magic file.
    '''
    return _get_file_type(file_path, 'from_file')


def get_file_type_from_binary(binary):
    '''
    Works like get_file_type with the distinction of using a byte object instead of a file path
    '''
    return _get_file_type(binary, 'from_buffer')


def _get_file_type(path_or_binary, function_name):
    magic_path = os.path.join(get_src_dir(), 'bin/custommime.mgc')

    magic_wrapper = magic.Magic(magic_file=magic_path, mime=True)
    mime = _get_type_from_magic_object(path_or_binary, magic_wrapper, function_name, mime=True)

    magic_wrapper = magic.Magic(magic_file=magic_path, mime=False)
    full = _get_type_from_magic_object(path_or_binary, magic_wrapper, function_name, mime=False)

    if mime == 'application/octet-stream':
        mime = _get_type_from_magic_object(path_or_binary, magic, function_name, mime=True)
        full = _get_type_from_magic_object(path_or_binary, magic, function_name, mime=False)
    return {'mime': mime, 'full': full}


def _get_type_from_magic_object(path_or_binary, magic_object, function_name, mime=True):
    try:
        if isinstance(magic_object, magic.Magic):
            result = make_unicode_string(getattr(magic_object, function_name)(path_or_binary))
        else:
            result = make_unicode_string(getattr(magic_object, function_name)(path_or_binary, mime=mime))
    except FileNotFoundError as e:
        logging.error('File not found: {}'.format(e))
        result = 'error/file-not-found' if mime else 'Error: File not in storage!'
    except Exception as exception:
        logging.error('Could not determine file type: {} {}'.format(type(exception), str(exception)))
        result = 'application/octet-stream' if mime else 'data'
    return result


def file_is_empty(file_path):
    '''
    Returns True if file in file_path has 0 Bytes
    Returns False otherwise
    '''
    try:
        if os.path.getsize(file_path) == 0:
            return True
    except (FileNotFoundError, PermissionError, OSError):
        return False
    except Exception as e:
        logging.error('Unexpected Exception: {} {}'.format(sys.exc_info()[0].__name__, e))
    else:
        return False


def create_dir_for_file(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)


def compress_and_pack_folder(input_dir: Path, output_file: Path):
    '''
    create tar.gz of input_dir and store it to output_file
    return None on error or output_file on success
    '''
    create_dir_for_file(output_file)
    output, rc = execute_shell_command_get_return_code('tar -C {} -cvzf {} .'.format(input_dir, output_file))
    if rc != 0:
        logging.error('Could not create tar.gz:\n{}'.format(output))
        return None
    else:
        return output_file
