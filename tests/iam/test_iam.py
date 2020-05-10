import unittest
from unittest.mock import patch
from fzfaws.iam.iam import IAM
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.utils.session import BaseSession


class TestIAM(unittest.TestCase):
    def test_constructor(self):
        iam = IAM(profile="default", region="ap-southeast-2")
        self.assertEqual([""], iam.arns)
        self.assertEquals("default", iam.profile)
        self.assertEquals("ap-southeast-2", iam.region)

    @patch.object(BaseSession, "get_paginated_result")
    @patch.object(Pyfzf, "process_list")
    @patch.object(Pyfzf, "append_fzf")
    @patch.object(Pyfzf, "execute_fzf")
    def test_setarns(
        self, mocked_fzf_execute, mocked_fzf_append, mocked_fzf_list, mocked_result
    ):
        iam = IAM()
        self.assertEquals(None, iam.profile)
        self.assertEquals(None, iam.region)

        mocked_result.return_value = [
            {
                "Roles": [
                    {
                        "Path": "/",
                        "RoleName": "admincloudformaitontest",
                        "RoleId": "AROAVQL5EWXLRDZGWYAU2",
                        "Arn": "arn:aws:iam::378756445655:role/admincloudformaitontest",
                        "CreateDate": "2010-09-09",
                        "AssumeRolePolicyDocument": {
                            "Version": "2012-10-17",
                            "Statement": [
                                {
                                    "Sid": "",
                                    "Effect": "Allow",
                                    "Principal": {
                                        "Service": "cloudformation.amazonaws.com"
                                    },
                                    "Action": "sts:AssumeRole",
                                }
                            ],
                        },
                        "Description": "Allows CloudFormation to create and manage AWS stacks and resources on your behalf.",
                        "MaxSessionDuration": 3600,
                    }
                ]
            }
        ]
        mocked_fzf_execute.return_value = (
            "arn:aws:iam::378756445655:role/admincloudformaitontest"
        )
        iam.set_arns(service="cloudformation.amazonaws.com")
        mocked_fzf_append.assert_called_with(
            "RoleName: admincloudformaitontest  Arn: arn:aws:iam::378756445655:role/admincloudformaitontest"
        )
        self.assertEqual(
            "arn:aws:iam::378756445655:role/admincloudformaitontest", iam.arns[0]
        )

        iam.set_arns()
        mocked_fzf_list.assert_called_with(
            [
                {
                    "Path": "/",
                    "RoleName": "admincloudformaitontest",
                    "RoleId": "AROAVQL5EWXLRDZGWYAU2",
                    "Arn": "arn:aws:iam::378756445655:role/admincloudformaitontest",
                    "CreateDate": "2010-09-09",
                    "AssumeRolePolicyDocument": {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Sid": "",
                                "Effect": "Allow",
                                "Principal": {
                                    "Service": "cloudformation.amazonaws.com"
                                },
                                "Action": "sts:AssumeRole",
                            }
                        ],
                    },
                    "Description": "Allows CloudFormation to create and manage AWS stacks and resources on your behalf.",
                    "MaxSessionDuration": 3600,
                }
            ],
            "RoleName",
            "Arn",
        )
