# lambda-sc-cost-meter
Lambda to report Service Catalog costs to the AWS Marketplace

## Description

This app will look for resources in an AWS account that contains tags indicating that
the resources were provisioned by a Service Catalog subscriber.  SC subscriber resources
typically contain `marketplace:productCode` and `marketplace:customerId` tags.  This
app will report the total cost of all those resources to the AWS Marketplace every hour.

## Prerequisites

This application only works when used with the following:
* [synapse-login-aws-infra](https://github.com/Sage-Bionetworks/synapse-login-aws-infra)
* [synapse-login-scippol](https://github.com/Sage-Bionetworks/synapse-login-scipool)
* [Cloudformation custom resource tagger](https://github.com/Sage-Bionetworks-IT/cfn-cr-synapse-tagger)
* [AWS Service Catalog](https://aws.amazon.com/servicecatalog)

The synapse-login-aws-infra will create a dynamo database.  The synapse-login-scipool
will populate the database with Service Catalog subscriber (or customer)
info (synpase id, customer id,product code, etc..)

This app depends on an existing dynamo db with valid customer data.

## Development

### Contributions
Contributions are welcome.

### Requirements
Run `pipenv install --dev` to install both production and development
requirements, and `pipenv shell` to activate the virtual environment. For more
information see the [pipenv docs](https://pipenv.pypa.io/en/latest/).

After activating the virtual environment, run `pre-commit install` to install
the [pre-commit](https://pre-commit.com/) git hook.

### Create a local build

```shell script
$ sam build
```

### Run unit tests
Tests are defined in the `tests` folder in this project. Use PIP to install the
[pytest](https://docs.pytest.org/en/latest/) and run unit tests.

```shell script
$ python -m pytest tests/ -v
```

### Run integration tests
Running integration tests
[requires docker](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-local-start-api.html)

```shell script
$ sam local invoke MeterFunction --event events/event.json
```

## Deployment

### Deploy Lambda to S3
Deployments are sent to the
[Sage cloudformation repository](https://bootstrap-awss3cloudformationbucket-19qromfd235z9.s3.amazonaws.com/index.html)
which requires permissions to upload to Sage
`bootstrap-awss3cloudformationbucket-19qromfd235z9` and
`essentials-awss3lambdaartifactsbucket-x29ftznj6pqw` buckets.

```shell script
sam package --template-file .aws-sam/build/template.yaml \
  --s3-bucket essentials-awss3lambdaartifactsbucket-x29ftznj6pqw \
  --output-template-file .aws-sam/build/lambda-sc-cost-meter.yaml

aws s3 cp .aws-sam/build/lambda-sc-cost-meter.yaml s3://bootstrap-awss3cloudformationbucket-19qromfd235z9/lambda-sc-cost-meter/master/
```

## Publish Lambda

### Private access
Publishing the lambda makes it available in your AWS account.  It will be accessible in
the [serverless application repository](https://console.aws.amazon.com/serverlessrepo).

```shell script
sam publish --template .aws-sam/build/lambda-sc-cost-meter.yaml
```

### Public access
Making the lambda publicly accessible makes it available in the
[global AWS serverless application repository](https://serverlessrepo.aws.amazon.com/applications)

```shell script
aws serverlessrepo put-application-policy \
  --application-id <lambda ARN> \
  --statements Principals=*,Actions=Deploy
```

## Install Lambda into AWS

### Sceptre
Create the following [sceptre](https://github.com/Sceptre/sceptre) file
config/prod/lambda-sc-cost-meter.yaml

```yaml
template_path: "remote/lambda-sc-cost-meter.yaml"
stack_name: "lambda-sc-cost-meter"
stack_tags:
  Department: "Platform"
  Project: "Infrastructure"
  OwnerEmail: "it@sagebase.org"
hooks:
  before_launch:
    - !cmd "curl https://bootstrap-awss3cloudformationbucket-19qromfd235z9.s3.amazonaws.com/lambda-sc-cost-meter/master/lambda-sc-cost-meter.yaml --create-dirs -o templates/remote/lambda-sc-cost-meter.yaml"
```

Install the lambda using sceptre:
```shell script
sceptre --var "profile=my-profile" --var "region=us-east-1" launch prod/lambda-sc-cost-meter.yaml
```

### AWS Console
Steps to deploy from AWS console.

1. Login to AWS
2. Access the
[serverless application repository](https://console.aws.amazon.com/serverlessrepo)
-> Available Applications
3. Select application to install
4. Enter Application settings
5. Click Deploy

## Releasing

We have setup our CI to automate a releases.  To kick off the process just create
a tag (i.e 0.0.1) and push to the repo.  The tag must be the same number as the current
version in [template.yaml](template.yaml).  Our CI will do the work of deploying and publishing
the lambda.
