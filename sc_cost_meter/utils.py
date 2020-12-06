import boto3
import logging
import os

from datetime import datetime

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def get_ec2_client():
  return boto3.client('ec2')

def get_ssm_client():
  return boto3.client('ssm')

def get_ce_client():
  return boto3.client('ce')

def get_meteringmarketplace_client():
  return boto3.client('meteringmarketplace')

def get_dynamo_client():
  return boto3.client('dynamodb')

def get_env_var_value(env_var):
  '''Get the value of an environment variable
  :param env_var: the environment variable
  :returns: the environment variable's value, None if env var is not found
  '''
  value = os.getenv(env_var)
  if not value:
    log.warning(f'cannot get environment variable: {env_var}')

  return value

def get_marketplace_synapse_ids():
  '''Get Synapse IDs from the Marketplace Dynamo DB, these are the Marketplace customers.
  Assumes that there is a Dynamo DB with a table containing a mapping of Synapse
  IDs to SC subscriber data
  :return a list of synapse IDs, otherwise return empty list if no customers are in DB
  '''
  synapse_ids = []
  ddb_marketplace_table_name = get_env_var_value('MARKETPLACE_ID_DYNAMO_TABLE_NAME')
  ddb_marketplace_synapse_user_id_attribute = "SynapseUserId"
  if ddb_marketplace_table_name:
    client = get_dynamo_client()
    response = client.scan(
      TableName=ddb_marketplace_table_name,
      ProjectionExpression=ddb_marketplace_synapse_user_id_attribute,
    )

    if "Items" in response.keys():
      for item in response["Items"]:
        synapse_ids.append(item[ddb_marketplace_synapse_user_id_attribute]["S"])

  return synapse_ids

def get_marketplace_customer_info(synapse_id):
  '''Get the Service Catalog customer info.
  Assumes that there is a Dynamo DB with a table containing a mapping of Synapse IDs
  to SC subscriber customer IDs
  :param synapse_id: synapse user id
  :return a dict containing the customer info
  '''
  customer_info = {}
  ddb_marketplace_table_name = get_env_var_value('MARKETPLACE_ID_DYNAMO_TABLE_NAME')
  if ddb_marketplace_table_name:
    client = get_dynamo_client()
    response = client.get_item(
      Key={
        'SynapseUserId': {
          'S': synapse_id,
        }
      },
      TableName=ddb_marketplace_table_name,
      ConsistentRead=True,
    )

    if "Item" in response.keys():
      customer_attribute = response['Item']
      for key, value in customer_attribute.items():
        customer_info[key] = value['S']
    else:
      log.info(f'cannot find registration for synapse user: {synapse_id}')

  return customer_info

def get_customer_cost(customer_id, time_period, granularity):
  '''
  Get the total cost of all resources tagged with the customer_id for a given
  time_period.  The time_period and time granularity must match.
  :param customer_id: the Marketplace customer ID
  :param time_period: the cost time period
  :param granularity: the granularity of time HOURLY|DAILY|MONTHLY
  :return: the total cost of all resources and the currency unit
  '''
  client = get_ce_client()

  response = client.get_cost_and_usage(
    TimePeriod=time_period,
    Granularity=granularity,
    Filter={
      "Tags": {
        "Key": "marketplace:customerId",
        "Values": [
          customer_id
        ]
      }
    },
    Metrics=["UnblendedCost"]
  )

  results_by_time = response['ResultsByTime']
  cost = results_by_time[0]["Total"]["UnblendedCost"]["Amount"]
  unit = results_by_time[0]["Total"]["UnblendedCost"]["Unit"]
  return float(cost), unit

def report_cost(cost, customer_id, product_code):
  '''
  Report the incurred cost of the customer's resources to the AWS Marketplace
  :param cost: the cost (as a float value)
  :param customer_id: the Marketplace customer ID
  :param product_code: the Marketplace product code
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
  log.debug(f'batch_meter_usage response: {response}')
  results = response["Results"][0]
  status = results["Status"]
  if status == 'Success':
    log.info(f'usage record: {results}')
  else:
    # TODO: need to add a retry mechanism for failed reports
    unprocessed_records = response["UnprocessedRecords"][0]
    log.error(f'unprocessed record: {unprocessed_records}')
