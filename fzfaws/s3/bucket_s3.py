"""bucket transfer operation

contains the main function for moving object between buckets
"""
from fzfaws.s3.s3 import S3
from fzfaws.s3.helper.sync_s3 import sync_s3


def bucket_s3(from_path=None, to_path=None, recursive=False, sync=False, exclude=[], include=[]):
    """transfer file between buckts

    Args:
        from_path: string, target bucket path
        to_path: string, destination bucket path
        recursive: bool, whether to copy entire folder or just file
        sync: bool, use sync operation through subprocess
        exclude: list, list of glob pattern to exclude
        include: list, list of glob pattern to include afer exclude
    Return:
        None
    Exceptions:
        InvalidS3PathPattern: when the specified s3 path is invalid pattern
    """

    s3 = S3()

    target_bucket = None
    target_path = ''
    dest_bucket = None
    dest_path = ''

    search_folder = True if recursive or sync else False

    if from_path:
        target_bucket, target_path = process_path_param(
            from_path, s3, search_folder)
        s3.bucket_name = None
        s3.bucket_path = ''
        if to_path:
            dest_bucket, dest_path = process_path_param(
                to_path, s3, True)
    else:
        print('Set the target bucket which contains the file to move')
        s3.set_s3_bucket()
        if search_folder:
            s3.set_s3_path()
        else:
            s3.set_s3_object()
        target_bucket = s3.bucket_name
        target_path = s3.bucket_path

        print('Set the destination bucket where the file should be moved')
        s3.bucket_name = None
        s3.bucket_path = ''
        s3.set_s3_bucket()
        s3.set_s3_path()
        dest_bucket = s3.bucket_name
        dest_path = s3.bucket_path

    if sync:
        sync_s3(exclude, include, 's3://%s/%s' % (target_bucket,
                                                  target_path), 's3://%s/%s' % (dest_bucket, dest_path))


def process_path_param(path, s3, search_folder):
    """process path args and return bucket name and path

    Args:
        path: string, raw path from the argument
        s3: object, s3 instance from the S3 class
        search_folder: bool, search folder or file
    """
    s3.set_bucket_and_path(path)
    if not s3.bucket_path:
        if search_folder:
            s3.set_s3_path()
        else:
            s3.set_s3_object()
    return (s3.bucket_name, s3.bucket_path)
