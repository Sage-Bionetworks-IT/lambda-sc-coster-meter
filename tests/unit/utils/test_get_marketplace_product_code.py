import unittest
from unittest.mock import MagicMock, patch

from botocore.stub import Stubber

from sc_cost_meter import utils


class TestGetMarketplaceCustomerID(unittest.TestCase):

  @patch('sc_cost_meter.utils.get_env_var_value')
  def test_missing_ddb_table_name_var(self, mock_get_env_var_value):
    mock_get_env_var_value.return_value = None
    expected = None
    result = utils.get_marketplace_product_code("111111")
    self.assertEqual(expected, result)

  def test_product_code_not_found(self):
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
        result = utils.get_marketplace_product_code("111111")
        self.assertEqual(expected, result)

  def test_product_code_found(self):
    client = utils.get_dynamo_client()
    with Stubber(client) as stubber, \
      patch('sc_cost_meter.utils.get_env_var_value') as mock_get_env_var_value:
        mock_get_env_var_value.return_value = "some-table"
        response = {
          "Item": {
            "ProductCode":
              {
                "S": "ProductCode1234"
              }
          },
          "ResponseMetadata": {
            "RequestId": "7f6e2b4e-537e-45b6-b48e-dbc0657861e4",
            "HTTPStatusCode": 200,
          }
        }

        expected = "ProductCode1234"
        stubber.add_response('get_item', response)
        utils.get_dynamo_client = MagicMock(return_value=client)
        result = utils.get_marketplace_product_code("111111")
        self.assertEqual(expected, result)
