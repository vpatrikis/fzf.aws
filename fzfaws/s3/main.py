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
                                     usage='faws s3 [-h] {upload,download,delete,bucket,presign,ls} ...')
    subparsers = parser.add_subparsers(dest='subparser_name')
    upload_cmd = subparsers.add_parser(
        'upload', description='upload a local file/directory to s3 bucket')
    upload_cmd.add_argument('-R', '--root', action='store_true',
                            default=False, help='search local file from root directory')
    upload_cmd.add_argument('-p', '--path', nargs=1, action='store', default=None,
                            help='specify a s3 path (bucketName/path) using this flag and skip s3 bucket/path selection')
    upload_cmd.add_argument('-P', '--local', nargs=1, action='store', default=None,
                            help='specify the path of a local file to upload')
    upload_cmd.add_argument('-r', '--recursive', action='store_true',
                            default=False, help='upload a directory to s3 bucket recursivly')
    upload_cmd.add_argument('-s', '--sync', action='store_true',
                            default=False, help='use the aws cli s3 sync operation')
    upload_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                            help='specify a bash style globbing pattern to exclude a number of patterns')
    upload_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                            help='specify a bash style globbing pattern to include files after excluding')
    upload_cmd.add_argument('-H', '--hidden', action='store_true', default=False,
                            help='when fd is installed, add this flag to include hidden files in the search')
    download_cmd = subparsers.add_parser(
        'download', description='download a file/directory from s3 to local')
    download_cmd.add_argument('-R', '--root', action='store_true', default=False,
                              help='search local directory from root directory')
    download_cmd.add_argument('-p', '--path', nargs=1, action='store', default=[],
                              help='specify a s3 path (bucketName/path) using this flag and skip s3 bucket/path selection')
    download_cmd.add_argument('-P', '--local', nargs=1, action='store', default=[],
                              help='specify the path of a local file to download')
    download_cmd.add_argument('-r', '--recursive', action='store_true',
                              default=False, help='download a directory from s3 recursivly')
    download_cmd.add_argument('-s', '--sync', action='store_true',
                              default=False, help='use the aws cli s3 sync operation')
    download_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                              help='specify a bash style globbing pattern to exclude a number of patterns')
    download_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                              help='specify a bash style globbing pattern to include files after excluding')
    download_cmd.add_argument('-H', '--hidden', action='store_true', default=False,
                              help='when fd is installed, add this flag to include hidden files in the search')
    bucket_cmd = subparsers.add_parser(
        'bucket', description='move file/directory between s3 buckets')
    bucket_cmd.add_argument('-p', '--path', nargs='+', action='store', default=[],
                            help='spcify 1 or 2 path for the from bucket and to bucket respectively')
    bucket_cmd.add_argument('-r', '--recursive', action='store_true', default=False,
                            help='move bucket object respectively')
    bucket_cmd.add_argument('-s', '--sync', action='store_true', default=False,
                            help='use the aws cli s3 sync operation')
    bucket_cmd.add_argument('-e', '--exclude', nargs='+', action='store', default=[],
                            help='specify a bash style globbing pattern to exclude a number of patterns')
    bucket_cmd.add_argument('-i', '--include', nargs='+', action='store', default=[],
                            help='specify a bash style globbing pattern to include files after excluding')
    args = parser.parse_args(raw_args)

    if not raw_args:
        available_commands = ['upload']
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
        exit()

    if args.subparser_name == 'upload':
        upload_s3(args)
    elif args.subparser_name == 'download':
        path = args.path[0] if args.path else None
        local = args.local[0] if args.local else None
        download_s3(path, local, args.recursive, args.root,
                    args.sync, args.exclude, args.include, args.hidden)
    elif args.subparser_name == 'bucket':
        from_path = args.path[0] if args.path else None
        to_path = args.path[1] if len(args.path) > 1 else None
        bucket_s3(from_path, to_path, args.recursive,
                  args.sync, args.exclude, args.include)
