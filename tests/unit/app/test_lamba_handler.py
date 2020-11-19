import unittest
from unittest.mock import patch

from sc_cost_meter import app


class TestLambdaHandler(unittest.TestCase):

  @patch('sc_cost_meter.utils.get_marketplace_synapse_ids')
  @patch('sc_cost_meter.utils.report_cost')
  def test_no_customers(self,
                        mock_report_cost,
                        mock_get_marketplace_synapse_ids):
    mock_get_marketplace_synapse_ids.return_value = []
    app.lambda_handler(None, None)
    mock_report_cost.assert_not_called()

  @patch('sc_cost_meter.utils.get_marketplace_synapse_ids')
  @patch('sc_cost_meter.utils.get_marketplace_customer_id')
  @patch('sc_cost_meter.utils.get_marketplace_product_code')
  @patch('sc_cost_meter.utils.get_customer_cost_yesterday')
  @patch('sc_cost_meter.utils.report_cost')
  def test_report_cost_multiple_customers(self,
                              mock_report_usage,
                              mock_get_cusomter_cost_yesterday,
                              mock_get_marketplace_product_code,
                              mock_get_marketplace_customer_id,
                              mock_get_marketplace_synapse_ids):
    mock_get_marketplace_synapse_ids.return_value = ["11111", "22222"]
    mock_get_marketplace_customer_id.return_value = "cust-1111"
    mock_get_marketplace_product_code.return_value = "prod-1234"
    mock_get_cusomter_cost_yesterday.return_value = ["2.1111", "USD"]
    app.lambda_handler(None, None)
    self.assertEqual(mock_report_usage.call_count, 2)
