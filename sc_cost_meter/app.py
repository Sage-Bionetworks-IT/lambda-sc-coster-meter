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
          cost_tags = {
            "Key": "marketplace:customerId",
                  "Values": [
                     customer_id
                  ]
          }
          cost = utils.get_ec2_cost(cost_tags)
          results = utils.report_usage(cost, customer_id, product_code)
          status = results[0]["Status"]
          if status == 'Success':
            meter_record_id = results[0]["MeteringRecordId"]
            log.info(f'recorded meter usage for customer {customer_id} '
                     f'with meter record id {meter_record_id}')
          else:
            log.info(f'failed to meter usage for customer {customer_id} with status {status}')


def lambda_handler(event, context):
  meter_instances()
