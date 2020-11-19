import logging
import sc_cost_meter.utils as utils

from datetime import datetime, timedelta

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def lambda_handler(event, context):
  synapse_ids = utils.get_marketplace_synapse_ids()
  log.debug(f'customers list: {synapse_ids}')
  for synapse_id in synapse_ids:
    customer_id = utils.get_marketplace_customer_id(synapse_id)
    log.debug(f'marketplace customer ID: {customer_id}')
    product_code = utils.get_marketplace_product_code(synapse_id)
    log.debug(f'marketplace product code: {product_code}')

    current_time = datetime.utcnow()
    start_time = current_time - timedelta(days=2)
    end_time = current_time - timedelta(days=1)
    yesterday = {
      "Start": start_time.strftime('%Y-%m-%d'),
      "End": end_time.strftime('%Y-%m-%d')
    }

    cost, unit = utils.get_customer_cost(customer_id, yesterday, "DAILY")
    utils.report_cost(cost, customer_id, product_code)
