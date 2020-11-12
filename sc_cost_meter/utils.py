import awspricing
import boto3
import logging
import os

from datetime import datetime, timedelta

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

os.environ["AWSPRICING_USE_CACHE"] = "1"  # enable cache for awspricing

def get_ec2_client():
  return boto3.client('ec2')

def get_ssm_client():
  return boto3.client('ssm')

def get_ce_client():
  return boto3.client('ce')

def get_meteringmarketplace_client():
  return boto3.client('meteringmarketplace')

def get_instances(states):
  '''
  Get all EC2 instances in the specfied states
  :param states: list of states (['pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'])
         https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_InstanceState.html
  :return: list of instances in the state specified by states, empty list if none are
           found in the specified states
  '''
  client = get_ec2_client()
  response = client.describe_instances(
    Filters=[
       {
          'Name': 'instance-state-name',
          'Values': states
       }
    ]
  )

  instances = []
  reservations = response["Reservations"]
  if reservations:
    for reservation in reservations:
        for instance in reservation["Instances"]:
          instances.append(instance)

  return instances

def get_ec2_on_demand_pricing(instance):
  '''
  Get the on demand pricing for an instance
  :param instance: an EC2 in the AWS account
  :return: on demand price of the instance (https://aws.amazon.com/ec2/pricing/on-demand/)
  '''
  instance_region = instance['Placement']['AvailabilityZone'][0:-1]
  instance_id = instance['InstanceId']
  instance_type = instance['InstanceType']

  client = get_ssm_client()
  response = client.describe_instance_information(
    Filters=[
       {
          'Key': 'InstanceIds',
          'Values': [instance_id]
       }
    ]
  )
  ssm_instance_info = response['InstanceInformationList'][0]
  instance_platform = ssm_instance_info['PlatformType']

  ec2_offer = awspricing.offer('AmazonEC2')
  price = ec2_offer.ondemand_hourly(
    instance_type,
    operating_system=instance_platform,
    region=instance_region
  )

  log.debug(f'price for {instance_id} is {price}')
  return price

def get_ec2_cost(tags):
  '''
  Get the total cost of all EC2s with an attached set of tags.
  :param tags: a dictionary of tags (i.e. {"Key": "customerId", "Values": ["1234ABCD"]})
  :return: the total cost of all EC2s
          Note: AWS billing history shows that cost data is only updated every 24 hours
          therefore the response from get_cost_and_usage API may lag up to one day.
          This means that the only way to get consistent billing info is to query the
          previous day's billing.
  '''
  client = get_ce_client()

  # Get the cost from the previous day
  current_time = datetime.utcnow()
  start_time = current_time - timedelta(days=2)
  end_time = current_time - timedelta(days=1)

  result = client.get_cost_and_usage(
    TimePeriod={
      "Start": start_time.strftime('%Y-%m-%d'),
      "End": end_time.strftime('%Y-%m-%d')
    },
    Granularity="DAILY",
    Filter={
      "And": [
        {
          "Dimensions": {
            "Key": "SERVICE",
            "Values": [
              "Amazon Elastic Compute Cloud - Compute",  # instance cost
              "EC2 - Other"   # EB Volume, data transfer, elastic IP, etc..
            ]
          }
        },
        {
          "Tags": tags
        },
      ]
    },
    Metrics=["UnblendedCost"]
  )

  cost = result[0]["Total"]["UnblendedCost"]["Amount"]   # total cost (EC2 instance + EC2-other)

  return cost


def get_tags(instance):
  '''
  Get all tags for an instance
  :param instance: EC2 instance
  :return: list of tags
  '''
  client = get_ec2_client()
  response = client.describe_tags(
    Filters = [
       {
          'Name': 'resource-id',
          'Values': [
             instance,
          ]
       }
    ]
  )
  tags = response['Tags']
  log.debug(f'instance tags = {tags}')
  return tags


def get_instance_product_code(instance):
  '''
  Get the Marketplace product code from the instance
  :param instance: an EC2 instance
  :return: product code
  '''
  product_codes = instance['ProductCodes']
  if len(product_codes) >= 1:
    for product_code in product_codes:
       if product_code['ProductCodeType'] == 'marketplace':
         product_code_id = product_code['ProductCodeId']
         log.debug(f'Product Code ID = {product_code_id}')
         return product_code_id

  return None

def get_marketplace_product_code(tags):
  '''
  Get the Marketplace product code for the Service Catalog SaaS service
  that we apply as a tag to the resource when we provision it.
  :param tags: list of tags
  :return: Marketplace product code if a tag exists, otherwise None
  '''
  product_code = None
  for tag in tags:
    if tag['Key'] == 'marketplace:productCode':
      product_code = tag['Value']

  return product_code

def report_usage(cost, customer_id, product_code):
  '''
  Report cost information to the Marketplace
  :param cost: the product cost
  :param customer_id: the customer identifier
  :param product_code: the product code
  :return: reporting status ('Success'|'CustomerNotSubscribed'|'DuplicateRecord')
  '''
  cost_accrued_rate = 0.001  # TODO: use mareketplace get_dimension API to get this info
  quantity = int(cost / cost_accrued_rate)

  mrktpl_client = get_meteringmarketplace_client()
  response = mrktpl_client.batch_meter_usage(
    UsageRecords=[
      {
        'Timestamp': datetime.utcnow(),
        'CustomerIdentifier': customer_id,
        'Dimension': 'costs_accrued',
        'Quantity': quantity
      }
    ],
    ProductCode=product_code
  )

  return response["Results"]
