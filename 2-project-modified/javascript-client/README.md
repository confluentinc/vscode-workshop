# JavaScript Client

This project contains JavaScript applications for both producing to and consuming from a topic on Kafka (including Confluent Cloud), with optional Schema Registry support.

## Getting Started

### Prerequisites
- Node.js (tested with v14 or later)
- npm (included with Node.js)

### Installation

Install the dependencies of this application:

```shell
npm install
```

### Configuration

Set environment variables in `.env`:

- Required for authenticating with Kafka in Confluent Cloud: `CC_API_KEY`, `CC_API_SECRET`
- For connecting to the Kafka cluster: `CC_BOOTSTRAP_SERVER` 
- For the topic name: `CC_TOPIC`
- Optional client identification: `CLIENT_ID`
- Optional consumer group: `GROUP_ID` (defaults to "js-consumer-group-id")

#### Schema Registry (Optional)

To enable [Schema Registry](https://docs.confluent.io/cloud/current/get-started/schema-registry.html) support, you must select this option when generating the project template. Schema Registry support cannot be enabled after generation.

If Schema Registry was enabled during project generation:
- Set these environment variables: `CC_SCHEMA_REGISTRY_URL`, `CC_SR_API_KEY`, `CC_SR_API_SECRET`
- The application will use Avro serialization with Schema Registry

If Schema Registry was not enabled during project generation:
- The application will use JSON serialization without Schema Registry
- Setting Schema Registry environment variables will have no effect

## Usage

### Running Locally

You can run the producer:

```shell
node producer.js
```

Then run the consumer to see your produced messages:

```shell
node consumer.js
```

Once you are done with the consumer, enter `ctrl+C` to terminate the consumer application.

### Docker

Make sure you have your [Docker desktop app](https://www.docker.com/products/docker-desktop/) installed and running.

From the root directory of the generated project, run:

```shell
docker compose build --no-cache
docker compose up
```

This will start Kafka, Schema Registry (if enabled), producer and consumer services as defined in the [docker-compose.yml](./docker-compose.yml) file.

## Troubleshooting

If you encounter issues with Kafka connections:
- Verify your credentials in the `.env` file
- Ensure your Confluent Cloud cluster is running
- Check network connectivity to the bootstrap servers

For more details, refer to the [Confluent Kafka JavaScript client documentation](https://github.com/confluentinc/confluent-kafka-javascript) and [Confluent Cloud documentation](https://docs.confluent.io/cloud/current/overview.html).
