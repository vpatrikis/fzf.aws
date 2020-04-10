"""main entry point for all s3 operations

process raw args passed from __main__.py and route
commands to appropriate sub functions
"""
import argparse
import json
import subprocess
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.s3.upload_s3 import upload_s3
from fzfaws.s3.download_s3 import download_s3
from fzfaws.s3.bucket_s3 import bucket_s3
from fzfaws.s3.delete_s3 import delete_s3
from fzfaws.s3.presign_s3 import presign_s3
from fzfaws.s3.object_s3 import object_s3
from fzfaws.s3.ls_s3 import ls_s3


def s3(raw_args):
    """main function for s3 operations

    Args:
        raw_args: raws args from __main__.py, starting from sys.argv[2:]
    Returns:
        None
    Raises:
        subprocess.CalledProcessError: When user exit the fzf subshell by ctrl-c
        ClientError: aws boto3 exceptions
        KeyboardInterrupt: ctrl-c during python operations
        NoNameEntered: when the required name entry is empty
        NoSelectionMade: when required fzf selection is not made
    """

    parser = argparse.ArgumentParser(description='perform CRUD operations with aws s3 bucket',
                                     usage='faws s3 [-h] {upload,download,delete,bucket,presign,object,ls} ...')
    subparsers = parser.add_subparsers(dest='subparser_name')
    upload_cmd = subparsers.add_parser(
        'upload', description='upload a local file/directory to s3 bucket')
    upload_cmd.add_argument('-R', '--root', action='store_true',
                            default=False, help='search local file from root directory')
    upload_cmd.add_argument('-b', '--bucket', nargs=1, action='store', default=[],
                            help='specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)' +
                            'using this flag and skip s3 bucket/path selection')
    upload_cmd.add_argument('-p', '--path', nargs='+', action='store', default=[],
                            help='specify the path/paths of a local file to upload' +
                            '(e.g. ~/folder/ or ~/folder/filename)')
    upload_cmd.add_argument('-r', '--recursive', action='store_true',
                            default=False, help='upload a directory to s3 bucket recursivly')
    upload_cmd.add_argument('-s', '--sync', action='store_true',
                            default=False, help='use the aws cli s3 sync operation')
    upload_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to exclude a number of patterns')
    upload_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to include files after excluding')
    upload_cmd.add_argument('-H', '--hidden', action='store_true', default=False,
                            help='when fd is installed, add this flag to include hidden files in the search')
    upload_cmd.add_argument('-E', '--extra', action='store_true', default=False,
                            help='configure extra settings for this upload operation (e.g. ACL, storage class, encryption)' +
                            'otherwise, default settings of the bucket would be used')
    upload_cmd.add_argument('-P', '--profile', nargs='?', action='store', default=False,
                            help='use a different profile, set the flag without argument to use fzf and select a profile')

    download_cmd = subparsers.add_parser(
        'download', description='download a file/directory from s3 to local')
    download_cmd.add_argument('-R', '--root', action='store_true', default=False,
                              help='search local directory from root directory')
    download_cmd.add_argument('-b', '--bucket', nargs=1, action='store', default=[],
                              help='specify a s3 path (bucketname/filename or bucketname/path/ or bucketName/)' +
                              'using this flag and skip s3 bucket/path selection')
    download_cmd.add_argument('-p', '--path', nargs=1, action='store', default=[],
                              help='specify the path for the download destination of the s3 object' +
                              '(e.g. ~/folder/ or ~/folder/filename)')
    download_cmd.add_argument('-r', '--recursive', action='store_true',
                              default=False, help='download a directory from s3 recursivly')
    download_cmd.add_argument('-s', '--sync', action='store_true',
                              default=False, help='use the aws cli s3 sync operation')
    download_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                              help='specify a number of bash style globbing pattern to exclude a number of patterns')
    download_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                              help='specify a number of bash style globbing pattern to include files after excluding')
    download_cmd.add_argument('-H', '--hidden', action='store_true', default=False,
                              help='when fd is installed, add this flag to include hidden files in the search')
    download_cmd.add_argument('-v', '--version', action='store_true', default=False,
                              help='choose a version of the object and download, Note: does not support recursive flag')

    bucket_cmd = subparsers.add_parser(
        'bucket', description='move file/directory between s3 buckets')
    bucket_cmd.add_argument('-b', '--bucket', nargs='+', action='store', default=[],
                            help='spcify 1 or 2 path for the from bucket and to bucket respectively')
    bucket_cmd.add_argument('-r', '--recursive', action='store_true', default=False,
                            help='move bucket object respectively')
    bucket_cmd.add_argument('-s', '--sync', action='store_true', default=False,
                            help='use the aws cli s3 sync operation')
    bucket_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to exclude a number of patterns')
    bucket_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to include files after excluding')
    bucket_cmd.add_argument('-v', '--version', action='store_true', default=False,
                            help='choose a version of the object and transfer, Note: does not support recursive flag')
    bucket_cmd.add_argument('-p', '--preserve', action='store_true', default=False,
                            help='preserve all object details when moving object, default False, will use the bucket setting')

    delete_cmd = subparsers.add_parser(
        'delete', description='delete file/directory on the s3 bucket')
    delete_cmd.add_argument('-b', '--bucket', nargs=1, action='store', default=[],
                            help='specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)' +
                            'using this flag and skip s3 bucket/path selection')
    delete_cmd.add_argument('-r', '--recursive', action='store_true',
                            default=False, help='download a directory from s3 recursivly')
    delete_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to exclude a number of patterns')
    delete_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to include files after excluding')
    delete_cmd.add_argument('-m', '--mfa', nargs=2, action='store', default=[],
                            help='Two argument needed to be specifies, the authentication device\'s serial number ' +
                            'and the value that is displayed on your authentication device. ' +
                            'Required to permanently delete a versioned object if versioning is configured with MFA delete enabled')
    delete_cmd.add_argument('-v', '--version', action='store_true', default=False,
                            help='choose an or multiple object versions to delete, Note: does not support recursive, to delete all versions recursivly, use -V flag')
    delete_cmd.add_argument('-V', '--allversion', action='store_true', default=False,
                            help='delete a versioned object completely including all versions and delete markes')
    delete_cmd.add_argument('-d', '--deletemark', action='store_true', default=False,
                            help='only display and delete object with delete marker, used for cleanup all deleted unwanted object')
    delete_cmd.add_argument('-c', '--clean', action='store_true', default=False,
                            help='delete all versions recursivly except the current one, used for cleanup s3 bucket with all older versions')

    presign_cmd = subparsers.add_parser(
        'presign', description='generate presign url on the selected object based on your current profile permission')
    presign_cmd.add_argument('-b', '--bucket', nargs=1, action='store', default=[],
                             help='spcify a s3 path (buckeName/path), use this flag to skip s3 bucket/path selection')
    presign_cmd.add_argument('-v', '--version', action='store_true', default=False,
                             help='generate presign url on a specific version of the object')
    presign_cmd.add_argument('-e', '--expires', nargs=1, action='store', default=[3600],
                             help='specify a expiration period in seconds, default is 3600 seconds')

    object_cmd = subparsers.add_parser(
        'object', description='configure settings and properties of objects in S3')
    object_cmd.add_argument('-b', '--bucket', nargs=1, action='store', default=[],
                            help='specify a s3 path (bucketName/filename or bucketName/path/ or bucketName/)' +
                            'using this flag and skip s3 bucket/path selection')
    object_cmd.add_argument('-r', '--recursive', action='store_true', default=False,
                            help='update setting/configuration of a \'folder\' recursivly on s3')
    object_cmd.add_argument('-v', '--version', action='store_true', default=False,
                            help='update setting/configuration of versions of objects')
    object_cmd.add_argument('-V', '--allversion', action='store_true', default=False,
                            help='update setting/configuration for all versions of the selected object')
    object_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to exclude a number of patterns')
    object_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                            help='specify a number of bash style globbing pattern to include files after excluding')
    object_cmd.add_argument('-N', '--name', action='store_true', default=False,
                            help='update the name of the selected object')
    object_cmd.add_argument('-S', '--storage', action='store_true', default=False,
                            help='update storage class of the selected object')
    object_cmd.add_argument('-M', '--meta', action='store_true', default=False,
                            help='update metadata of the selected object')
    object_cmd.add_argument('-t', '--tag', action='store_true', default=False,
                            help='update tag of the selected object')
    object_cmd.add_argument('-E', '--encryption', action='store_true', default=False,
                            help='update encryption method of the selected object')
    object_cmd.add_argument('-A', '--ACL', action='store_true', default=False,
                            help='update acl method of the selected object')

    ls_cmd = subparsers.add_parser(
        'ls', description='display details about selected object')
    ls_cmd.add_argument('-b', '--bucket', action='store_true', default=False,
                        help='list bucket and display bucket setting')
    ls_cmd.add_argument('-v', '--version', action='store_true', default=False,
                        help='list file versions of the selected files')
    ls_cmd.add_argument('-d', '--deletemark', action='store_true', default=False,
                        help='only list file with delete marker associated')
    args = parser.parse_args(raw_args)

    if not raw_args:
        available_commands = ['upload', 'download',
                              'bucket', 'delete', 'object', 'ls']
        fzf = Pyfzf()
        for command in available_commands:
            fzf.append_fzf(command)
            fzf.append_fzf('\n')
        selected_command = fzf.execute_fzf(
            empty_allow=True, print_col=1, preview='faws s3 {} -h')
        if selected_command == 'upload':
            upload_cmd.print_help()
        elif selected_command == 'download':
            download_cmd.print_help()
        elif selected_command == 'bucket':
            bucket_cmd.print_help()
        elif selected_command == 'delete':
            delete_cmd.print_help()
        elif selected_command == 'object':
            object_cmd.print_help()
        elif selected_command == 'ls':
            ls_cmd.print_help()
        exit()

    if args.subparser_name == 'upload':
        bucket = args.bucket[0] if args.bucket else None
        upload_s3(bucket, args.path, args.recursive, args.hidden,
                  args.root, args.sync, args.exclude, args.include, args.extra)
    elif args.subparser_name == 'download':
        bucket = args.bucket[0] if args.bucket else None
        local_path = args.path[0] if args.path else None
        download_s3(bucket, local_path, args.recursive, args.root,
                    args.sync, args.exclude, args.include, args.hidden, args.version)
    elif args.subparser_name == 'bucket':
        from_bucket = args.bucket[0] if args.bucket else None
        to_bucket = args.bucket[1] if len(args.bucket) > 1 else None
        bucket_s3(from_bucket, to_bucket, args.recursive,
                  args.sync, args.exclude, args.include, args.version, args.preserve)
    elif args.subparser_name == 'delete':
        bucket = args.bucket[0] if args.bucket else None
        mfa = ' '.join(args.mfa)
        delete_s3(bucket, args.recursive, args.exclude,
                  args.include, mfa, args.version, args.allversion, args.deletemark, args.clean)
    elif args.subparser_name == 'presign':
        bucket = args.bucket[0] if args.bucket else None
        presign_s3(bucket, args.version, int(args.expires[0]))
    elif args.subparser_name == 'object':
        bucket = args.bucket[0] if args.bucket else None
        object_s3(bucket, args.recursive, args.version, args.allversion,
                  args.exclude, args.include, args.name, args.storage, args.encryption, args.meta, args.tag, args.ACL)
    elif args.subparser_name == 'ls':
        ls_s3(args.bucket, args.version, args.deletemark)
