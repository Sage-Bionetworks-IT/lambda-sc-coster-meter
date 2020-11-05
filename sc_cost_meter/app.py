import logging
import sc_cost_meter.utils as utils

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def meter_instances():
  '''
  Send EC2 cost info to the AWS Marketplace
  '''
  instances = utils.get_instances(['running'])
  for instance in instances:
    instance_id = instance['InstanceId']
    tags = utils.get_tags(instance_id)
    for tag in tags:
      if tag['Key'] == 'marketplace:customerId':
        customer_id = tag['Value']
        product_code = utils.get_marketplace_product_code(tags)
        if product_code:
          price = utils.get_ec2_on_demand_pricing(instance)
          status = utils.report_usage(price, customer_id, product_code)
          if status == 'Success':
            log.info(f'recorded meter usage for customer {customer_id}')
          else:
            log.info(f'failed to meter usage for customer {customer_id} with status {status}')


def lambda_handler(event, context):
  meter_instances()
