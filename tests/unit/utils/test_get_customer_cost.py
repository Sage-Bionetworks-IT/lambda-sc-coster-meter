import unittest
from unittest.mock import MagicMock, patch

from botocore.stub import Stubber
from sc_cost_meter import app, utils


class TestGetCustomerCost(unittest.TestCase):

  def test_get_cost(self):
    client = utils.get_ce_client()
    with Stubber(client) as stubber:
      response = {
        "ResultsByTime": [
          {
            "TimePeriod": {
              "Start": "2020-11-09",
              "End": "2020-11-10"
            },
            "Total": {
              "UnblendedCost": {
                "Amount": "0.2764",
                "Unit": "USD"
              }
            },
            "Groups": [],
            "Estimated": True
          }
      ],
        "ResponseMetadata": {
          "RequestId": "9fb57117-bd89-4b4d-933a-ef487cd86177",
          "HTTPStatusCode": 200,
        }
      }

      expected = (0.2764, "USD")
      stubber.add_response('get_cost_and_usage', response)
      utils.get_ce_client = MagicMock(return_value=client)
      yesterday = app.get_time_period_yesterday()
      result = utils.get_customer_cost("111111", yesterday, "DAILY")
      self.assertTupleEqual(expected, result)
