import unittest
from unittest.mock import MagicMock, patch

from botocore.stub import Stubber

from sc_cost_meter import utils


class TestGetMarketplaceCustomerID(unittest.TestCase):

  @patch('sc_cost_meter.utils.get_env_var_value')
  def test_missing_ddb_table_name_var(self, mock_get_env_var_value):
    mock_get_env_var_value.return_value = None
    expected = None
    result = utils.get_marketplace_customer_id("111111")
    self.assertEqual(expected, result)

  def test_customer_id_not_found(self):
    client = utils.get_dynamo_client()
    with Stubber(client) as stubber, \
      patch('sc_cost_meter.utils.get_env_var_value') as mock_get_env_var_value:
        mock_get_env_var_value.return_value = "some-table"
        response = {
          "ResponseMetadata": {
            "RequestId": "7f6e2b4e-537e-45b6-b48e-dbc0657861e4",
            "HTTPStatusCode": 200,
          }
        }

        expected = None
        stubber.add_response('get_item', response)
        utils.get_dynamo_client = MagicMock(return_value=client)
        result = utils.get_marketplace_customer_id("111111")
        self.assertEqual(expected, result)

  def test_customer_id_found(self):
    client = utils.get_dynamo_client()
    with Stubber(client) as stubber, \
      patch('sc_cost_meter.utils.get_env_var_value') as mock_get_env_var_value:
        mock_get_env_var_value.return_value = "some-table"
        response = {
          "Item": {
            "MarketplaceCustomerId":
              {
                "S": "12345ABCDE"
              }
          },
          "ResponseMetadata": {
            "RequestId": "7f6e2b4e-537e-45b6-b48e-dbc0657861e4",
            "HTTPStatusCode": 200,
          }
        }

        expected = "12345ABCDE"
        stubber.add_response('get_item', response)
        utils.get_dynamo_client = MagicMock(return_value=client)
        result = utils.get_marketplace_customer_id("111111")
        self.assertEqual(expected, result)
