# Go Kafka Client - Development Guide

This template provides a Go-based Kafka client application with both producer and consumer functionality.

## Project Structure

- `producer.go` - Produces sample transaction events to Kafka
- `consumer.go` - Consumes transaction events from Kafka
- `Dockerfile.producer/consumer` - Docker setup for each component
- `.env` - Configuration for Confluent Cloud credentials

## Configuration

Some Kafka connection settings are in the `.env` file:
- `CC_API_KEY` - Confluent Cloud API key
- `CC_API_SECRET` - Confluent Cloud API secret

## Development Workflow

1. **Setup Environment**:
   - Ensure `.env` file has valid Confluent Cloud credentials
   - Install dependencies: `go mod download`

2. **Run Locally**:
   - Producer: `go run producer/producer.go`
   - Consumer: `go run consumer/consumer.go `

3. **Using Docker**:
   - Build and run producer and consumer: 
   `docker compose build --no-cache
    docker compose up`

## Common Tasks

- **Adding a new message type**:
  1. Define the struct in a new file (e.g., `models.go`)
  2. Update the producer logic in producer.go to serialize and send the new message type.
  3. Modify consumer.go to deserialize and process the new message type.
  4. Ensure tests are updated or added for the new message format.

- **Modifying configuration**:
  1. Add new variables to `.env`
  2. Load them in the code using `os.Getenv()`

- **Changing connection settings**:
  1. Modify the Kafka configuration in the .env or in the `kafka.ConfigMap{}` in both producer.go and consumer.go

## Advanced Configuration

- Consumer group management is handled in `consumer.go`
- Producer delivery reports are configured in `producer.go`
- Modify Docker containers in `docker-compose.yml` to update dependencies or service configurations.

## Troubleshooting
- Message not appearing in Kafka topic:
  - Ensure the producer is sending messages to the correct topic (topic in producer.go and consumer.go).
  - Check Confluent Cloud logs for message delivery status.
  - Verify that the Kafka cluster is reachable from the application.

- Consumer not receiving messages:
  - Confirm that the consumer group ID is correctly set.
  - Ensure the topic has messages by checking Confluent Cloud UI or CLI.
  - Check if the consumer has committed offsets past available messages.
  - Verify consumer subscription by adding debug logs: `fmt.Printf("Subscribed to: %v\n", topic)`
  - Check consumer configuration parameters, especially:
    - `auto.offset.reset` (should be "earliest" for testing)
    - `group.id` must be consistent across restarts to maintain offset position
    - `enable.auto.commit` settings
  - Inspect consumer logs for error messages or warnings
  - Add more detailed error handling to consumer code:
    ```go
    msg, err := c.ReadMessage(time.Second * 5)
    if err != nil {
        if !err.(kafka.Error).IsTimeout() {
            fmt.Printf("Consumer error: %v\n", err)
        }
        continue
    }
    ```
  - For local development, try accessing Confluent Cloud through a different network
  - Verify that there are no network issues between the consumer and Confluent Cloud
  - Check consumer processing logic for any blocking operations that might prevent the poll loop
  - Ensure proper deserialization of messages matches how they were produced
  - Check consumer lag using Confluent Cloud monitoring tools to see if consumer is falling behind
  - Monitor for consumer rebalancing issues in logs, which could indicate instability
  - Verify message size is within limits (default max.message.bytes is 1MB)
  - Use command-line tools to check topic contents:
    ```bash
    # Using Confluent CLI
    confluent kafka topic consume <topic-name> --from-beginning
    ```
  - Try a different consumer implementation (e.g., command-line consumer) to isolate application-specific issues
  - Adjust consumer timeout settings if your network has high latency:
    ```go
    conf := kafka.ConfigMap{
        // ...existing configuration...
        "session.timeout.ms": 60000,
        "max.poll.interval.ms": 300000,
    }
    ```
  - Check for topic-level access control limitations in Confluent Cloud

- Authentication failures:
  - Double-check API key and secret in .env.
  - Double-check cc_bootstrap_server
  - Verify that the credentials have the required ACL permissions.
  - Look for specific errors in logs that indicate auth problems:
    - `SASL authentication failed`
    - `Invalid credentials`
    - `Broker connection failed`
  - Ensure credentials don't have special characters causing parsing issues
  - Check for whitespace or newlines in your copied API key/secret
  - Verify API key hasn't been disabled or expired in Confluent Cloud
  - Confirm the correct SASL mechanism is configured (typically PLAIN for Confluent Cloud)
  - Check if your IP address is allowed by Confluent Cloud network policies
  - Try regenerating the API key if all else fails
  - Ensure the client has the correct time set - authentication can fail if clocks are skewed
  - Review your Kafka configuration to ensure it includes all required authentication parameters:
    ```go
    conf := kafka.ConfigMap{
        "bootstrap.servers":       bootstrapServers,
        "security.protocol":       "SASL_SSL",
        "sasl.mechanisms":         "PLAIN",
        "sasl.username":           apiKey,
        "sasl.password":           apiSecret,
    }
    ```

- Docker-related issues:
  - **Run docker desktop to check if containers are running.**

  - **Restart the setup using docker compose down && docker compose up --build.**
  
  - **Missing environment variables in Docker**:
    - Verify the `.env` file exists and has proper permissions: `ls -la .env`
    - Check if the file is correctly mounted in the container
    - Run `docker compose config` to see if variables are properly referenced
  
  - **Container crashes or exits immediately**:
    - Check container logs: `docker compose logs [service]`
    - Look for connection errors or authentication failures
    - Verify that .env file is properly mounted with `docker compose exec producer ls -la /app`
  
  - **Network connectivity issues**:
    - Check if containers can reach Confluent Cloud: `docker compose exec producer ping <bootstrap-server-host>`
    - Verify network configuration in the Docker Compose file
    - Try rebuilding the network: `docker compose down && docker network prune && docker compose up`
  
  - **Volume mounting issues**:
    - Ensure the local path to .env is correct
    - Try using absolute paths in the docker-compose.yml file
    - Check Docker Desktop settings for file sharing permissions
  
  - **Build failures**:
    - Clean Docker cache: `docker system prune -a`
    - Check for errors in the Dockerfile
    - Ensure Go dependencies are available and properly referenced
