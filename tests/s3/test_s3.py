import io
import json
import os
import sys
import unittest
from unittest.mock import PropertyMock, patch
from fzfaws.s3 import S3
from fzfaws.utils import FileLoader, Pyfzf, BaseSession
from botocore.stub import Stubber
import boto3
from fzfaws.utils.exceptions import InvalidFileType, InvalidS3PathPattern
from botocore.paginate import Paginator


class TestS3(unittest.TestCase):
    def setUp(self):
        self.capturedOutput = io.StringIO()
        sys.stdout = self.capturedOutput
        fileloader = FileLoader()
        config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        fileloader.load_config_file(config_path=config_path)
        self.s3 = S3()

    def tearDown(self):
        sys.stdout = sys.__stdout__

    def test_constructor(self):
        self.assertEqual(self.s3.profile, "default")
        self.assertEqual(self.s3.region, "ap-southeast-2")
        self.assertEqual(self.s3.bucket_name, "")
        self.assertEqual(self.s3.path_list, [""])

        s3 = S3(profile="root", region="us-east-1")
        self.assertEqual(s3.profile, "root")
        self.assertEqual(s3.region, "us-east-1")
        self.assertEqual(s3.bucket_name, "")
        self.assertEqual(s3.path_list, [""])

    @patch.object(BaseSession, "client", new_callable=PropertyMock)
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "process_list")
    def test_set_s3_bucket(self, mocked_list, mocked_execute, mocked_client):
        self.s3.bucket_name = ""
        self.s3.path_list = [""]
        s3_data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_bucket.json"
        )
        with open(s3_data_path, "r") as file:
            response = json.load(file)

        # normal test
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("list_buckets", response)
        stubber.activate()
        mocked_client.return_value = s3
        mocked_execute.return_value = "kazhala-version-testing"
        self.s3.set_s3_bucket()
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        mocked_list.assert_called_with(response["Buckets"], "Name")
        mocked_execute.assert_called_with(header="")

        # empty test
        s3 = boto3.client("s3")
        stubber = Stubber(s3)
        stubber.add_response("list_buckets", {"Buckets": []})
        stubber.activate()
        mocked_client.return_value = s3
        mocked_execute.return_value = ""
        self.s3.set_s3_bucket(header="hello")
        self.assertEqual(self.s3.bucket_name, "")
        mocked_list.assert_called_with([], "Name")
        mocked_execute.assert_called_with(header="hello")

    @patch.object(S3, "_validate_input_path")
    def test_set_bucket_and_path(self, mocked_validation):
        self.s3.bucket_name = ""
        self.s3.path_list = [""]
        self.s3.set_bucket_and_path(bucket="")

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", ""),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, [""])

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", "object1"),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/object1")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, ["object1"])

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", "folder/folder2/"),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/folder/folder2/")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, ["folder/folder2/"])

        mocked_validation.return_value = (
            "bucketpath",
            ("kazhala-version-testing/", "folder/object1"),
        )
        self.s3.set_bucket_and_path(bucket="kazhala-version-testing/folder/object1")
        self.assertEqual(self.s3.bucket_name, "kazhala-version-testing")
        self.assertEqual(self.s3.path_list, ["folder/object1"])

        mocked_validation.return_value = (None, None)
        self.assertRaises(
            InvalidS3PathPattern,
            self.s3.set_bucket_and_path,
            bucket="kazhala-version-testing",
        )

        mocked_validation.return_value = (
            "accesspoint",
            ("arn:aws:s3:us-west-2:123456789012:accesspoint/test/", "object"),
        )
        self.s3.set_bucket_and_path(
            bucket="arn:aws:s3:us-west-2:123456789012:accesspoint/test/object"
        )
        self.assertEqual(
            self.s3.bucket_name, "arn:aws:s3:us-west-2:123456789012:accesspoint/test"
        )
        self.assertEqual(self.s3.path_list, ["object"])

    def test_validate_input_path(self):
        result, match = self.s3._validate_input_path("kazhala-version-testing/")
        self.assertEqual(result, "bucketpath")
        self.assertEqual(match, ("kazhala-version-testing/", ""))

        result, match = self.s3._validate_input_path("kazhala-version-testing")
        self.assertEqual(result, None)
        self.assertEqual(match, None)

        result, match = self.s3._validate_input_path("kazhala-version-testing/hello")
        self.assertEqual(result, "bucketpath")
        self.assertEqual(match, ("kazhala-version-testing/", "hello"))

        result, match = self.s3._validate_input_path(
            "kazhala-version-testing/hello/world"
        )
        self.assertEqual(result, "bucketpath")
        self.assertEqual(match, ("kazhala-version-testing/", "hello/world"))

        result, match = self.s3._validate_input_path(
            "arn:aws:s3:us-west-2:123456789012:accesspoint/test/hello"
        )
        self.assertEqual(result, "accesspoint")
        self.assertEqual(
            match, ("arn:aws:s3:us-west-2:123456789012:accesspoint/test/", "hello"),
        )

        result, match = self.s3._validate_input_path(
            "arn:aws:s3:us-west-2:123456789012:accesspoint/test/hello/world"
        )
        self.assertEqual(result, "accesspoint")
        self.assertEqual(
            match,
            ("arn:aws:s3:us-west-2:123456789012:accesspoint/test/", "hello/world"),
        )

        result, match = self.s3._validate_input_path(
            "arn:aws:s3:us-west-2:123456789012:accesspoint/test"
        )
        self.assertEqual(result, None)
        self.assertEqual(match, None)

    @patch("fzfaws.s3.s3.get_confirmation")
    @patch.object(Pyfzf, "execute_fzf")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Paginator, "paginate")
    @patch("builtins.input")
    @patch.object(S3, "_get_path_option")
    def test_set_s3_path(
        self,
        mocked_option,
        mocked_input,
        mocked_paginator,
        mocked_append,
        mocked_execute,
        mocked_confirmation,
    ):
        # input
        self.s3.bucket_name = "kazhala-version-testing"
        mocked_option.return_value = "input"
        mocked_input.return_value = "hello"
        self.s3.set_s3_path()
        self.assertEqual(self.s3.path_list[0], "hello")

        # root
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_option.return_value = "root"
        self.s3.set_s3_path()
        self.assertEqual(
            self.capturedOutput.getvalue(), "S3 file path is set to root\n"
        )

        # interactively normal
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = [""]
        mocked_option.return_value = "interactively"
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)
        mocked_paginator.return_value = response
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/ (press ESC to use current path)",
            preview="echo .DS_Store Fortnite refund.docx README.md VideoPageSpec.docx boob.docx boto3-s3-filter.png cloudformation_parameters.png elb.pem lab.pem ooooo.doc version1.com version2.com version3.com | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        mocked_confirmation.assert_called()
        self.assertRegex(self.capturedOutput.getvalue(), "S3 file path is set to root")

        # interactively empty with path
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        mocked_paginator.return_value = []
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = ["hello/"]
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/hello/ (press ESC to use current path)",
            preview="echo  | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        mocked_confirmation.assert_called()
        self.assertRegex(
            self.capturedOutput.getvalue(), "S3 file path is set to hello/"
        )

        # append normal
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = [""]
        mocked_option.return_value = "append"
        mocked_paginator.return_value = response
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        mocked_input.return_value = "newpath/"
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/ (press ESC to use current path)",
            preview="echo .DS_Store Fortnite refund.docx README.md VideoPageSpec.docx boob.docx boto3-s3-filter.png cloudformation_parameters.png elb.pem lab.pem ooooo.doc version1.com version2.com version3.com | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        self.assertRegex(
            self.capturedOutput.getvalue(), "S3 file path is set to newpath/"
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            "Current PWD is s3://kazhala-version-testing/",
        )
        self.assertEqual(self.s3.path_list, ["newpath/"])

        # append empty with path
        self.capturedOutput.truncate(0)
        self.capturedOutput.seek(0)
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = ["newpath/"]
        mocked_option.return_value = "append"
        mocked_paginator.return_value = response
        mocked_execute.return_value = ""
        mocked_confirmation.return_value = True
        mocked_input.return_value = "obj1"
        self.s3.set_s3_path()
        mocked_execute.assert_called_with(
            empty_allow=True,
            print_col=0,
            header="PWD: s3://kazhala-version-testing/newpath/ (press ESC to use current path)",
            preview="echo .DS_Store Fortnite refund.docx README.md VideoPageSpec.docx boob.docx boto3-s3-filter.png cloudformation_parameters.png elb.pem lab.pem ooooo.doc version1.com version2.com version3.com | tr ' ' '\n'",
        )
        mocked_append.assert_called_with("versiontesting/\n")
        self.assertRegex(
            self.capturedOutput.getvalue(), "S3 file path is set to newpath/obj1"
        )
        self.assertRegex(
            self.capturedOutput.getvalue(),
            "Current PWD is s3://kazhala-version-testing/newpath/",
        )
        self.assertEqual(self.s3.path_list, ["newpath/obj1"])

    @patch.object(Paginator, "paginate")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    def test_s3_object(self, mocked_execute, mocked_append, mocked_paginator):
        self.s3.path_list = [""]
        self.s3.bucket_name = "kazhala-version-testing"
        # non version single test
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)
        mocked_paginator.return_value = response
        mocked_execute.return_value = ".DS_Store"
        self.s3.set_s3_object()
        self.assertEqual(self.s3.path_list[0], ".DS_Store")
        mocked_append.assert_called_with("Key: version3.com\n")

        # non version multi test
        mocked_execute.return_value = [".DS_Store", "object1"]
        self.s3.set_s3_object(multi_select=True)
        self.assertEqual(self.s3.path_list, [".DS_Store", "object1"])
        mocked_append.assert_called_with("Key: version3.com\n")

        # version single test
        self.s3.path_list = [""]
        self.s3.bucket_name = "kazhala-version-testing"
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object_ver.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)
        mocked_paginator.return_value = response
        mocked_execute.return_value = "sync/policy.json"
        self.s3.set_s3_object(version=True)
        self.assertEqual(self.s3.path_list[0], "sync/policy.json")
        mocked_append.assert_called_with("Key: wtf.pem\n")
        mocked_execute.assert_called_with(print_col=-1)

        # version multi test
        mocked_execute.return_value = ["sync/policy.json", "wtf.pem"]
        self.s3.set_s3_object(version=True, multi_select=True)
        self.assertEqual(self.s3.path_list, ["sync/policy.json", "wtf.pem"])
        mocked_append.assert_called_with("Key: wtf.pem\n")
        mocked_execute.assert_called_with(print_col=-1, multi_select=True)

        # version delete marker single
        mocked_execute.return_value = " wtf.txt"
        self.s3.set_s3_object(version=True, deletemark=True)
        self.assertEqual(self.s3.path_list[0], " wtf.txt")
        mocked_append.assert_called_with("\x1b[31mKey: .DS_Store\x1b[0m\n")

        # version delete marker multiple
        mocked_execute.return_value = [" wtf.txt", ".DS_Store"]
        self.s3.set_s3_object(version=True, deletemark=True, multi_select=True)
        self.assertEqual(self.s3.path_list, [" wtf.txt", ".DS_Store"])
        mocked_append.assert_called_with("\x1b[31mKey: .DS_Store\x1b[0m\n")

    @patch.object(Paginator, "paginate")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "execute_fzf")
    def test_get_object_version(self, mocked_execute, mocked_process, mocked_paginator):
        self.s3.path_list = ["wtf.pem"]
        self.s3.bucket_name = "kazhala-version-testing"
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/s3_object_ver.json"
        )
        with open(data_path, "r") as file:
            response = json.load(file)

        # general test single test
        mocked_paginator.return_value = response
        mocked_execute.return_value = "111111"
        result = self.s3.get_object_version()
        mocked_process.assert_called()
        self.assertEqual(result, [{"Key": "wtf.pem", "VersionId": "111111"}])

        # general parameter test
        mocked_paginator.return_value = response
        mocked_execute.return_value = "111111"
        result = self.s3.get_object_version(key="hello")
        mocked_process.assert_called()
        self.assertEqual(result, [{"Key": "hello", "VersionId": "111111"}])

        # non-current test
        wtf = self.s3.get_object_version(non_current=True)
        mocked_execute.return_value = "111111"
        self.assertEqual(wtf, [{"Key": "wtf.pem", "VersionId": "111111"}])

        # delete test
        mocked_paginator.return_value = response
        mocked_execute.return_value = ["111111", "2222222"]
        result = self.s3.get_object_version(delete=True)
        mocked_process.assert_called()
        self.assertEqual(
            result,
            [
                {"Key": "wtf.pem", "VersionId": "111111"},
                {"Key": "wtf.pem", "VersionId": "2222222"},
            ],
        )

        # delete multi test
        self.s3.path_list = ["wtf.pem", ".DS_Store"]
        mocked_paginator.return_value = response
        mocked_execute.return_value = ["111111", "2222222"]
        result = self.s3.get_object_version(delete=True)
        mocked_process.assert_called()
        self.assertEqual(
            result,
            [
                {"Key": "wtf.pem", "VersionId": "111111"},
                {"Key": "wtf.pem", "VersionId": "2222222"},
                {"Key": ".DS_Store", "VersionId": "111111"},
                {"Key": ".DS_Store", "VersionId": "2222222"},
            ],
        )

        # select all test
        self.s3.path_list = ["wtf.pem"]
        mocked_paginator.return_value = response
        result = self.s3.get_object_version(select_all=True)
        self.assertEqual(
            result[0],
            {"Key": "wtf.pem", "VersionId": "L2e4FjTfzOFyWZ1wsZwLYZSPWdxys9hZ"},
        )

    @patch.object(BaseSession, "resource", new_callable=PropertyMock)
    @patch.object(FileLoader, "process_json_body")
    @patch.object(FileLoader, "process_yaml_body")
    def test_get_object_data(self, mocked_yaml, mocked_json, mocked_resource):
        self.s3.bucket_name = "kazhala-version-testing"
        self.s3.path_list = ["wtf.pem"]
        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../data/ec2_sg.json"
        )
        with open(data_path, "r") as file:
            s3 = boto3.resource("s3")
            stubber = Stubber(s3.meta.client)
            stubber.add_response("get_object", {"Body": file})
            stubber.activate()
            mocked_resource.return_value = s3
            mocked_json.return_value = {"hello"}
            result = self.s3.get_object_data(file_type="json")
            mocked_json.assert_called_once()
        self.assertEqual(result, {"hello"})

        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        with open(data_path, "r") as file:
            s3 = boto3.resource("s3")
            stubber = Stubber(s3.meta.client)
            stubber.add_response("get_object", {"Body": file})
            stubber.activate()
            mocked_resource.return_value = s3
            mocked_yaml.return_value = {"hello"}
            result = self.s3.get_object_data(file_type="yaml")
            mocked_yaml.assert_called_once()
        self.assertEqual(result, {"hello"})

        data_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "../../fzfaws.yml"
        )
        with open(data_path, "r") as file:
            s3 = boto3.resource("s3")
            stubber = Stubber(s3.meta.client)
            stubber.add_response("get_object", {"Body": file})
            stubber.activate()
            mocked_resource.return_value = s3
            mocked_yaml.return_value = {"hello"}
            self.assertRaises(InvalidFileType, self.s3.get_object_data, file_type="txt")
