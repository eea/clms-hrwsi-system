#!/usr/bin/env python3
"""Files and directories utilities."""
import os
from os.path import dirname
import logging
import shutil

class FileUtil(object):
    '''Utility functions to manage file and directories.'''

    @staticmethod
    def create_dir(path:str, overwrite:bool=False, error_on_already_existing:bool=False)->None:
        '''
        Create directory tree-path recursively at provided location

        Create directory at provided location if irt does not exist yet.
        Otherwise, raises an error if asked to.
        Otherwise, overwrites the folder by recursively removing its content if asked to.

        Parameters
        ----------
        path : str
            path of directory to be created. Can be relative or absolute.
        overwrite : bool, optional
            set to True to overwrite an eventual already existing directory, by default False
        error_on_already_existing : bool, optional
            set to True to raise an error if the directory already exists, by default False
        '''
        if error_on_already_existing:
            try:
                assert os.path.exists(path)
            except AssertionError as error:
                logging.critical(f'Directory {path} cannot be created as it already exists and error_on_already_existing is set to {error_on_already_existing}.')
                logging.critical(f'{error}')
                raise error

        if overwrite and os.path.exists(path):
            logging.warning(f'Removing already existing directory {path}, its subfolders and files.')
            shutil.rmtree(path)

        try:
            os.makedirs(path, exist_ok=True)
        except PermissionError as error:
            logging.critical(f'Directory {path} cannot be created as due to permission issues.')
            logging.critical(f'{error}')
            raise error

    @staticmethod
    def create_file_path(path:str, overwrite:bool=False, error_on_already_existing:bool=False)->None:
        '''
        Create file's parent file-tree at provided location.

        Create file-tree at provided location if the directories do not exist yet.
        Otherwise, raises an error if asked to.
        Otherwise, overwrites the file-tree if asked to.

        Parameters
        ----------
        path : str
            path of file which file-tree is to be created including the file name. Can be relative or absolute.
        overwrite : bool, optional
            set to True to overwrite an eventual already existing file-tree, by default False
        error_on_already_existing : bool, optional
            set to True to raise an error if the file-tree alreday exists, by default False
        '''
        dir_path = dirname(path)

        if not dir_path:
            logging.error(f'No directory path can be extracted from {path}, aborting directory creation')
            return

        if error_on_already_existing:
            try:
                assert os.path.exists(dir_path)
            except AssertionError as error:
                logging.critical(f'Directory {dir_path} extracted from input {path} cannot be created as it already exists and error_on_already_existing is set to {error_on_already_existing}.')
                logging.critical(f'{error}')
                raise error

        if overwrite and os.path.exists(dir_path):
            logging.warning(f'Removing already existing folder {dir_path}, its subfolders and files.')
            shutil.rmtree(dir_path)

        FileUtil.create_dir(dir_path)

    @staticmethod
    def create_file(path, overwrite:bool=False, error_on_already_existing:bool=False)->None:
        '''
        Create file at provided location

        Create file at provided location if the no file exists yet.
        Otherwise, raises an error if asked to.
        Otherwise, overwrites the file if asked to.

        Parameters
        ----------
        path : str
            path of file to be created including the file name. Can be relative or absolute.
        overwrite : bool, optional
            set to True to overwrite an eventual already existing file, by default False
        error_on_already_existing : bool, optional
            set to True to raise an error if the file alreday exists, by default False
        '''

        if overwrite:
            writting_mode = 'w'
        else:
            writting_mode = 'x'

        try:
            logging.info(f'Creating file at location {path}')
            with open(path, writting_mode, encoding='utf-8') as file:
                pass
        except FileExistsError as error:
            logging.critical(f'File {path} cannot be created as it already exists, error_on_already_existing is set to {error_on_already_existing}, and overwrite is set to {overwrite}.')
            logging.critical(f'{error}')
            raise error
        except PermissionError as error:
            logging.critical(f'File {path} cannot be created as due to permission issues.')
            logging.critical(f'{error}')
            raise error
        except Exception as error:
            logging.critical(f'File {path} cannot be created as due to unexpected error.')
            logging.critical(f'{error}')
            raise error


if __name__ == "__main__":
    pass
