import boto3
import logging
import os

from datetime import datetime, timedelta

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
  '''Get Synapse IDs from the Marketplace Dynamo DB, these are the Service Catalog customers.
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

def get_marketplace_customer_id(synapse_id):
  '''Get the Service Catalog customer ID from the Marketplace Dynamo DB.
  Assumes that there is a Dynamo DB with a table containing a mapping of Synapse
  IDs to SC subscriber data
  :param synapse_id: synapse user id
  :return the Marketplace customer ID, otherwise return None if cannot find an
          associated customer ID
  '''
  customer_id = None
  ddb_marketplace_table_name = get_env_var_value('MARKETPLACE_ID_DYNAMO_TABLE_NAME')
  if ddb_marketplace_table_name:
    ddb_customer_id_attribute = 'MarketplaceCustomerId'
    client = get_dynamo_client()
    response = client.get_item(
      Key={
        'SynapseUserId': {
          'S': synapse_id,
        }
      },
      TableName=ddb_marketplace_table_name,
      ConsistentRead=True,
      AttributesToGet=[
        ddb_customer_id_attribute
      ]
    )

    if "Item" in response.keys():
      customer_id = response["Item"][ddb_customer_id_attribute]["S"]
    else:
      log.info(f'cannot find registration for synapse user: {synapse_id}')

  return customer_id

def get_marketplace_product_code(synapse_id):
  '''Get the registered Service Catalog customer product code.
  Assumes that there is a Dynamo DB with a table containing a mapping of Synapse
  IDs to SC subscriber data
  :param synapse_id: synapse user id
  :return the Marketplace product code, None if cannot find customer ID
  '''
  product_code = None
  ddb_marketplace_table_name = get_env_var_value('MARKETPLACE_ID_DYNAMO_TABLE_NAME')
  if ddb_marketplace_table_name:
    ddb_product_code_attribute = 'ProductCode'
    client = get_dynamo_client()
    response = client.get_item(
      Key={
        'SynapseUserId': {
          'S': synapse_id,
        }
      },
      TableName=ddb_marketplace_table_name,
      ConsistentRead=True,
      AttributesToGet=[
        ddb_product_code_attribute
      ]
    )

    if "Item" in response.keys():
      product_code = response["Item"][ddb_product_code_attribute]["S"]
      log.debug(f'marketplace product code: {product_code}')
    else:
      log.info(f'cannot find registration for synapse user: {synapse_id}')

  return product_code


def get_customer_cost_yesterday(customer_id):
  '''
  Get the total cost of all resources tagged with the customer_id from
  yestereday.
  :param customer_id: the Marketplace customer ID
  :return: the total cost of all resouurces and the currency unit
  '''
  client = get_ce_client()

  current_time = datetime.utcnow()
  start_time = current_time - timedelta(days=2)
  end_time = current_time - timedelta(days=1)

  response = client.get_cost_and_usage_with_resources(
    TimePeriod={
      "Start": start_time.strftime('%Y-%m-%d'),
      "End": end_time.strftime('%Y-%m-%d')
    },
    Granularity="DAILY",
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
  return cost, unit

def report_cost(cost, customer_id, product_code):
  '''
  Report the incurred cost of the customer's resources to the AWS Marketplace
  :param cost: the cost
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

  status = response[0]["Status"]
  if status == 'Success':
    meter_record_id = response[0]["MeteringRecordId"]
    log.info(f'recorded meter usage for customer {customer_id} '
             f'with meter record id {meter_record_id}')
  else:
    # TODO: need to add a retry mechanism for failed reports
    log.error(f'failed to meter usage for customer {customer_id} with status {status}')
