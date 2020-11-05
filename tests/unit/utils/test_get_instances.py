import unittest
from unittest.mock import MagicMock

import boto3
import botocore
from botocore.stub import Stubber

from sc_cost_meter import utils


class TestGetInstances(unittest.TestCase):

  def test_get_running_instance(self):
    ec2 = utils.get_ec2_client()
    with Stubber(ec2) as stubber:
      response = {
        "Reservations": [
          {
            "Groups": [

            ],
            "Instances": [
              {
                "InstanceId": "i-1111111",
                "InstanceType": "t3.micro",
                "State": {
                  "Code": 16,
                  "Name": "running"
                }
              }
            ]
          }
        ],
        "ResponseMetadata": {
          "RequestId": "7f6e2b4e-537e-45b6-b48e-dbc0657861e4",
          "HTTPStatusCode": 200,
        }
      }
      expected = [
        {
          "InstanceId": "i-1111111",
          "InstanceType": "t3.micro",
          "State": {
            "Code": 16,
            "Name": "running"
          }
        }
      ]
      stubber.add_response('describe_instances', response)
      utils.get_ec2_client = MagicMock(return_value=ec2)
      result = utils.get_instances(['running'])
      self.assertEqual(expected, result)

  def test_get_instance_invalid_state(self):
    ec2 = utils.get_ec2_client()
    with Stubber(ec2) as stubber:
      response = {
        "Reservations": [],
        "ResponseMetadata": {
          "RequestId": "7f6e2b4e-537e-45b6-b48e-dbc0657861e4",
          "HTTPStatusCode": 200,
        }
      }
      expected = []
      stubber.add_response('describe_instances', response)
      utils.get_ec2_client = MagicMock(return_value=ec2)
      result = utils.get_instances(['fooing'])
      self.assertEqual(expected, result)
