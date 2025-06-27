# .NET Client

This project contains .NET applications for both producing to and consuming from a topic on Kafka (including Confluent Cloud), with optional Schema Registry support.

## Getting Started

### Prerequisites

We assume that you already have .NET SDK (>= 8.0) installed. The template was last tested against .NET 8.0.

### Installation

To restore and build the project, run the following command in the root directory:

```shell
dotnet build
```

### Configuration

Set environment variables in `.env`:

- Required for authenticating with Kafka in Confluent Cloud: `CC_API_KEY`, `CC_API_SECRET`
- For connecting to the Kafka cluster: `CC_BOOTSTRAP_SERVER` 
- For the topic name: `CC_TOPIC`
- Optional client identification: `CLIENT_ID`
- Optional consumer group: `GROUP_ID` (defaults to "dotnet-consumer-group-id")

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
dotnet run --project ./dotnet-client.csproj Producer
```

Then run the consumer to see your produced messages:

```shell
dotnet run --project ./dotnet-client.csproj Consumer
```


### Docker

Make sure you have your [Docker desktop app](https://www.docker.com/products/docker-desktop/) installed and running.

From the root directory of the project, run:

```shell
docker compose build --no-cache
docker compose up
```

This will start Kafka, Schema Registry (if enabled), producer and consumer services as defined in the [docker-compose.yml](./docker-compose.yml) file.

## Troubleshooting

For more details, check the [Confluent documentation](https://docs.confluent.io/kafka-clients/dotnet/current/overview.html) and the [Confluent.Kafka .NET client](https://github.com/confluentinc/confluent-kafka-dotnet) repository.

