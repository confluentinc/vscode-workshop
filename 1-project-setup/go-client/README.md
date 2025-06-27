# Go Client

This project contains Go applications for both producing to and consuming from a topic on Kafka (including Confluent Cloud), with optional Schema Registry support.

## Getting Started

### Prerequisites

We assume that you already have Go installed. The template was last tested against Go 1.22.2.

### Installation

To install the dependencies defined in `go.mod`, run the following command in the root directory of this project:

```bash
go mod tidy
go mod vendor
```

### Configuration

Set environment variables in `.env`:

- Required for authenticating with Kafka in Confluent Cloud: `CC_API_KEY`, `CC_API_SECRET`
- For connecting to the Kafka cluster: `CC_BOOTSTRAP_SERVER` 
- For the topic name: `CC_TOPIC`
- Optional client identification: `CLIENT_ID`
- Optional consumer group: `GROUP_ID` (defaults to "go-consumer-group")

#### Schema Registry (Optional)

To enable [Schema Registry](https://docs.confluent.io/cloud/current/get-started/schema-registry.html) support, create it on Confluent Cloud "Schema Registry" section and set the following variables:
- `CC_SCHEMA_REGISTRY_URL`, `CC_SR_API_KEY`, `CC_SR_API_SECRET`

## Usage

### Running Locally

You can build and run the producer:

```bash
go run producer/producer.go
```

Then build and run the consumer to see your produced messages:

```bash
go run consumer/consumer.go
```


### Docker

Make sure you have your [Docker desktop app](https://www.docker.com/products/docker-desktop/) installed and running.

From the project directory, run:

```bash
docker compose build --no-cache
docker compose up
```

This will start Kafka, Schema Registry (if enabled), producer and consumer services as defined in the [docker-compose.yml](./docker-compose.yml) file.

## Troubleshooting

For more details, refer to the [Confluent Kafka Go client documentation](https://github.com/confluentinc/confluent-kafka-go).
