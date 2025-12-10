# Python Client

This project contains Python applications and Flink SQL statements for populating and analyzing topic information across a number of data systems listening to said topic.

## Getting Started

### Prerequisites
- Python 3 (tested with 3.12.2)
- virtualenv (or similar, like `venv`)
- confluent CLI

### Installation

Create and activate a Python environment, so that you have an isolated workspace:

```shell
virtualenv env
source env/bin/activate
```

Install the dependencies of this application:

```shell
pip install -r requirements.txt
```

Make the scripts executable:

```shell
chmod u+x producer.py tableflow.py
```

Ensure the confluent cli is installed to the latest version (v4.45.1 as of this page being written). Use [confluent-cli install](https://docs.confluent.io/confluent-cli/current/install.html) instructions based on your operating system.

### Configuration
Set environment variables in `.env` -- there's more than prior projects because of the number of systems we are using:
- `CC_TOPIC` -- The topic name we're using (`sales_orders` in live example)
- `CC_API_KEY` -- Kafka producer API key
- `CC_API_SECRET` -- Kafka producer API secret
- `CC_BOOTSTRAP_SERVER` -- Kafka server URI
- `CC_API_BASE_URL`
- `CC_SR_API_KEY` -- Kafka producer Schema Registry key
- `CC_SR_API_SECRET` -- Kafka producer Schema Registry key
- `CC_SCHEMA_REGISTRY_URL`
- `CC_TABLEFLOW_API_KEY` -- Tableflow API key separate from Kafka
- `CC_TABLEFLOW_API_SECRET` -- Tableflow API secret separate from Kafka
- `CC_ORG_ID` -- Makes the scripting more general, not needed if you want to hardcode
- `CC_REGION` -- Makes the scripting more general, not needed if you want to hardcode
- `CC_ENV_ID` -- Makes the scripting more general, not needed if you want to hardcode
- `CC_KAFKA_CLUSTER` -- Makes the scripting more general, not needed if you want to hardcode

### Producer Usage

You can execute the producer script by running:

```shell
./producer.py
```

Unlike in the prior steps, this script is modified to repeat data forever with increasing ids to better emulate live data streams.

Once you are done with the walkthrough, enter `ctrl+C` to terminate the producer application.

### Docker

Make sure you have your [Docker desktop app](https://www.docker.com/products/docker-desktop/) installed and running.

From the root directory of the generated project, run:

```
docker compose build --no-cache
docker compose up
```

### Flink Queries



## Troubleshooting

### Package Installation
If `pip install` fails with librdkafka error, check Python version compatibility.

For more details, check the [Confluent Cloud documentation](https://docs.confluent.io/cloud/current/overview.html).
