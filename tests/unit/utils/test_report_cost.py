import unittest
from unittest.mock import MagicMock, patch

from botocore.stub import Stubber
from sc_cost_meter import app, utils


class TestReportCost(unittest.TestCase):

  def test_report_cost_default_attempts_failed(self):
    client = utils.get_meteringmarketplace_client()
    with Stubber(client) as stubber:
      responses = [
        {},
        {},
        {}
      ]
      for response in responses:
        stubber.add_response('batch_meter_usage', response)
      utils.get_meteringmarketplace_client = MagicMock(return_value=client)
      status, result = utils.report_cost(1.0, "cust-123", "prod-123")
      expected = ("Failed", None)
      self.assertEqual('Failed', status)
      self.assertEqual(None, result)

  def test_report_cost_non_default_attempts_failed(self):
    client = utils.get_meteringmarketplace_client()
    with Stubber(client) as stubber:
      responses = [
        {},
        {},
        {},
        {},
        {}
      ]
      for response in responses:
        stubber.add_response('batch_meter_usage', response)
      utils.get_meteringmarketplace_client = MagicMock(return_value=client)
      status, result = utils.report_cost(1.0, "cust-123", "prod-123", 5)
      expected = ("Failed", None)
      self.assertEqual('Failed', status)
      self.assertEqual(None, result)

  def test_report_cost_success(self):
    client = utils.get_meteringmarketplace_client()
    with Stubber(client) as stubber:
      response = {
        "Results": [
          {
            "UsageRecord": {
              "Timestamp": "2020-10-10",
              "CustomerIdentifier":"cust-123",
              "Dimension": "costs_accrued",
              "Quantity": 100
            },
            "MeteringRecordId": "rec-123",
            "Status": "Success"
          }
        ],
        "UnprocessedRecords": [
        ],
        "ResponseMetadata": {
          "RequestId": "066f8a74-f929-4595-bc19-1a16f605bed5",
          "HTTPStatusCode": 200,
        }
      }
      stubber.add_response('batch_meter_usage', response)
      utils.get_meteringmarketplace_client = MagicMock(return_value=client)
      status, result = utils.report_cost(1.0, "cust-123", "prod-123")
      self.assertEqual('Success', status)
      self.assertDictEqual(response['Results'][0], result)

  def test_report_cost_invalid_attempts(self):
    with self.assertRaises(ValueError):
      utils.report_cost(1.0, "cust-123", "prod-123", 0)

  def test_report_cost_invalid_cost_less_than_zero(self):
    with self.assertRaises(ValueError):
      utils.report_cost(-1.0, "cust-123", "prod-123")

  def test_report_cost_invalid_cost_invalid_type_str(self):
    with self.assertRaises(ValueError):
      utils.report_cost("1.0", "cust-123", "prod-123")
