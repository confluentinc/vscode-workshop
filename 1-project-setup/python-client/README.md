# Python Client

This project contains Python applications for both writing to and consuming from a topic on Confluent Cloud, with Schema Registry support.

## Getting Started

### Prerequisites
- Python 3 (tested with 3.12.2)
- virtualenv (or similar, like `venv`)

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
chmod u+x producer.py consumer.py
```

### Configuration
Set environment variables in `.env`:
- Required for authenticating with Kafka in Confluent Cloud: `CC_API_KEY`, `CC_API_SECRET`, for connecting to the Kafka cluster: `CC_BOOTSTRAP_SERVER`
- Optional environment variables related to the Schema Registry: `CC_SR_API_KEY`, `CC_SR_API_SECRET`, `CC_SCHEMA_REGISTRY_URL`

### Schema Registry
Schema Registry support is available but optional:
- Sample schema in `/schema-registry-data`
- When enabled, both the consumer and the producer will use the Schema Registry for the (de)serialization of record values
- When disabled, applications fall back to using JSON without a Schema Registry

### Usage

You can execute the producer script by running:

```shell
./producer.py
```

Once you have produced all messages, start the consumer to see your produced messages coming in.

```shell
./consumer.py
```

Once you are done with the consumer, enter `ctrl+C` to terminate the consumer application.

### Docker

Make sure you have your [Docker desktop app](https://www.docker.com/products/docker-desktop/) installed and running.

From the root directory of the generated project, run:

```
docker compose build --no-cache
docker compose up
```

## Troubleshooting

### Package Installation
If `pip install` fails with librdkafka error, check Python version compatibility.

For more details, check the [Confluent Cloud documentation](https://docs.confluent.io/cloud/current/overview.html).