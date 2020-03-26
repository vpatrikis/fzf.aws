"""handles uploading operation of s3

upload local files/directories to s3
"""
import os
import sys
import fnmatch
import subprocess
from s3transfer import S3Transfer
from fzfaws.s3.s3 import S3
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.util import get_confirmation
from fzfaws.s3.helper.sync_s3 import sync_s3
from fzfaws.s3.helper.exclude_file import exclude_file
from fzfaws.s3.helper.s3progress import S3Progress


def upload_s3(bucket=None, local_paths=[], recursive=False, hidden=False, root=False, sync=False, exclude=[], include=[], storage_class=False):
    """upload local files/directories to s3

    upload through boto3 s3 client
    glob pattern are handled first exclude list then will run the include list

    Args:
        bucket: string, the bucket or bucket path for upload destination
            format: s3://bucketname or s3://bucketname/path/ or s3://bucketname/filename
        local_paths: list, list of local file to upload
            Note: only the first in the list is taken for recursive operation
        recursive: bool, upload directory
        hidden: bool, include hidden file during local file search
        root: bool, search local file from root
        sync: bool, use s3 cli sync operation
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include after exclude
        storage_class: bool, use different class rather than the default class
    Returns:
        None
    Raises:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
        NoSelectionMade: when the required fzf selection is empty
        SubprocessError: when the local file search got zero result from fzf(no selection in fzf)
    """

    s3 = S3()
    s3.set_bucket_and_path(bucket)
    if not s3.bucket_name:
        s3.set_s3_bucket()
    if not s3.bucket_path:
        s3.set_s3_path()

    fzf = Pyfzf()
    if not local_paths:
        recursive = True if recursive or sync else False
        # don't allow multi_select for recursive operation
        multi_select = True if not recursive else False
        local_paths = fzf.get_local_file(
            search_from_root=root, directory=recursive, hidden=hidden, empty_allow=recursive, multi_select=multi_select)

    # get the first item from the array since recursive operation doesn't support multi_select
    if isinstance(local_paths, list):
        local_path = local_paths[0]
    else:
        local_path = local_paths

    if storage_class:
        print('Select a storage class, esc to use the default storage class')
        class_fzf = Pyfzf()
        class_fzf.append_fzf('STANDARD\n')
        class_fzf.append_fzf('REDUCED_REDUNDANCY\n')
        class_fzf.append_fzf('STANDARD_IA\n')
        class_fzf.append_fzf('ONEZONE_IA\n')
        class_fzf.append_fzf('INTELLIGENT_TIERING\n')
        class_fzf.append_fzf('GLACIER\n')
        class_fzf.append_fzf('DEEP_ARCHIVE\n')
        storage_class = class_fzf.execute_fzf(empty_allow=True, print_col=1)

    # construct extra argument for upload
    extra_args = dict()
    if storage_class:
        extra_args['StorageClass'] = storage_class

    if sync:
        sync_s3(exclude=exclude, include=include, from_path=local_path,
                to_path='s3://%s/%s' % (s3.bucket_name, s3.bucket_path))

    elif recursive:
        upload_list = []
        for root, dirs, files in os.walk(local_path):
            for filename in files:
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, local_path)

                if not exclude_file(exclude, include, relative_path):
                    destination_key = s3.get_s3_destination_key(
                        relative_path, recursive=True)
                    print('(dryrun) upload: %s to s3://%s/%s' %
                          (relative_path, s3.bucket_name, destination_key))
                    upload_list.append(
                        {'local_path': full_path, 'bucket': s3.bucket_name, 'key': destination_key, 'relative': relative_path})

        if get_confirmation('Confirm?'):
            for item in upload_list:
                print('upload: %s to s3://%s/%s' %
                      (item['relative'], item['bucket'], item['key']))
                transfer = S3Transfer(s3.client)
                transfer.upload_file(item['local_path'], item['bucket'], item['key'],
                                     callback=S3Progress(item['local_path']), extra_args=extra_args)
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')
    else:
        for filepath in local_paths:
            # get the formated s3 destination
            destination_key = s3.get_s3_destination_key(filepath)
            print('(dryrung) upload: %s to s3://%s/%s' %
                  (filepath, s3.bucket_name, destination_key))

        if get_confirmation('Confirm?'):
            for filepath in local_paths:
                destination_key = s3.get_s3_destination_key(filepath)
                print('upload: %s to s3://%s/%s' %
                      (filepath, s3.bucket_name, destination_key))
                transfer = S3Transfer(s3.client)
                transfer.upload_file(filepath, s3.bucket_name, destination_key,
                                     callback=S3Progress(filepath), extra_args=extra_args)
                # remove the progress bar
                sys.stdout.write('\033[2K\033[1G')
