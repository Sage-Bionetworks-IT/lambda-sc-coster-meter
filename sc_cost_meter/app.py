import logging
import sc_cost_meter.utils as utils

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
    cost, unit = utils.get_customer_cost_yesterday(customer_id)
    utils.report_cost(cost, customer_id, product_code)
