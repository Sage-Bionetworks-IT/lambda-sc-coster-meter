import unittest
from unittest.mock import MagicMock, patch

from botocore.stub import Stubber

from sc_cost_meter import utils


class TestGetMarketplaceSynapseIDs(unittest.TestCase):

  @patch('sc_cost_meter.utils.get_env_var_value')
  def test_missing_ddb_table_name_var(self, mock_get_env_var_value):
    mock_get_env_var_value.return_value = None
    expected = []
    result = utils.get_marketplace_synapse_ids()
    self.assertEqual(expected, result)

  def test_no_synapse_ids_in_ddb(self):
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
        expected = []
        stubber.add_response('scan', response)
        utils.get_dynamo_client = MagicMock(return_value=client)

        result = utils.get_marketplace_synapse_ids()
        self.assertEqual(expected, result)

  def test_multiple_synapse_ids(self):
    client = utils.get_dynamo_client()
    with Stubber(client) as stubber, \
      patch('sc_cost_meter.utils.get_env_var_value') as mock_get_env_var_value:
        mock_get_env_var_value.return_value = "some-table"
        response = {
          "Items": [
            {
              "SynapseUserId":
                {
                  "S": "111111"
                }
            },
            {
              "SynapseUserId":
                {
                  "S": "222222"
                }
            }
          ],
          "ResponseMetadata": {
            "RequestId": "7f6e2b4e-537e-45b6-b48e-dbc0657861e4",
            "HTTPStatusCode": 200,
          }
        }
        expected = [
          "111111",
          "222222"
        ]
        stubber.add_response('scan', response)
        utils.get_dynamo_client = MagicMock(return_value=client)

        result = utils.get_marketplace_synapse_ids()
        self.assertEqual(expected, result)
