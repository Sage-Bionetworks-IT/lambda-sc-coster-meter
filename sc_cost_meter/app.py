import logging
import sc_cost_meter.utils as utils

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def meter_instances():
  instances = utils.get_instances(['running'])
  for instance in instances:
    instance_id = instance['InstanceId']
    tags = utils.get_tags(instance_id)
    for tag in tags:
      if tag['Key'] == 'marketplace:customerId':
        customer_id = tag['Value']
        product_code = utils.get_marketplace_product_code(instance)
        if product_code:
          price = utils.get_ec2_on_demand_pricing(instance)
          utils.report_usage(price, customer_id, product_code)
          log.info(f'recorded meter usage for customer {customer_id}')


def lambda_handler(event, context):
  meter_instances()
