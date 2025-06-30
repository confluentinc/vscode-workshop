package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"strings"
	"syscall"

	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/joho/godotenv"
)

type Transaction struct {
	TransactionId   string  `json:"TransactionId" avro:"TransactionId"`
	AccountNumber   string  `json:"AccountNumber" avro:"AccountNumber"`
	Amount          float64 `json:"Amount" avro:"Amount"`
	Currency        string  `json:"Currency" avro:"Currency"`
	Timestamp       string  `json:"Timestamp" avro:"Timestamp"`
	TransactionType string  `json:"TransactionType" avro:"TransactionType"`
	Status          string  `json:"Status" avro:"Status"`
}


func isLocalKafka(bootstrapServer string) bool {
	return strings.Contains(bootstrapServer, "localhost") ||
		strings.Contains(bootstrapServer, "127.0.0.1") ||
		strings.Contains(bootstrapServer, "kafka:")
}

// verifyKafkaSetup checks Kafka connection and topic
func verifyKafkaSetup(conf kafka.ConfigMap, topic string, isLocal bool) error {
	if isLocal {
		fmt.Println("✅ Kafka connection assumed available for local environment")
		return nil
	}

	adminClient, err := kafka.NewAdminClient(&conf)
	if err != nil {
		return fmt.Errorf("Kafka configuration error: %w", err)
	}
	defer adminClient.Close()

	metadata, err := adminClient.GetMetadata(&topic, false, 5000)
	if err != nil {
		return fmt.Errorf("Kafka connection error: %w", err)
	}

	if _, exists := metadata.Topics[topic]; !exists {
		return fmt.Errorf("Topic '%s' does not exist", topic)
	}

	return nil
}

// handleJSONMessage processes a message as plain JSON
func handleJSONMessage(value []byte, messageCount, maxMessages int) {
	var txn Transaction
	if err := json.Unmarshal(value, &txn); err != nil {
		fmt.Printf("❌ Error processing message: %v\n", err)
		fmt.Printf("Binary message, size: %d bytes\n", len(value))
		return
	}

	// Print message details
	fmt.Printf("Consumed message %d/%d: ", messageCount, maxMessages)

	// Print the raw JSON
	jsonOutput, _ := json.Marshal(txn)
	fmt.Printf("%s\n", string(jsonOutput))
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Printf("Warning: Error loading .env file: %v", err)
	}

	bootstrapServer := os.Getenv("CC_BOOTSTRAP_SERVER")
	topic := os.Getenv("CC_TOPIC")
	groupID := os.Getenv("GROUP_ID")
	if groupID == "" {
		groupID = "go-client-consumer-group"
	}

	conf := kafka.ConfigMap{
		"bootstrap.servers": bootstrapServer,
		"group.id":          groupID,
		"auto.offset.reset": "earliest",
	}

	// Detect if using local Kafka
	isLocal := isLocalKafka(bootstrapServer)

	if isLocal {
		conf["security.protocol"] = "PLAINTEXT"
		conf["client.id"] = os.Getenv("CLIENT_ID")
		fmt.Println("🐳 Using PLAINTEXT protocol for local broker")
	} else {
		conf["security.protocol"] = "SASL_SSL"
		conf["sasl.mechanisms"] = "PLAIN"
		conf["sasl.username"] = os.Getenv("CC_API_KEY")
		conf["sasl.password"] = os.Getenv("CC_API_SECRET")
		conf["client.id"] = os.Getenv("CLIENT_ID")
		fmt.Println("☁️ Using SASL_SSL protocol for cloud broker")
	}

	// Verify Kafka setup before proceeding
	if err := verifyKafkaSetup(conf, topic, isLocal); err != nil {
		fmt.Printf("❌ Kafka configuration error - Exiting: %v\n", err)
		os.Exit(1)
	}
	fmt.Printf("✅ Connected to Kafka (%s)\n", bootstrapServer)

	fmt.Println("🔄 Using plain JSON deserialization (no Schema Registry)")

	// Create consumer
	consumer, err := kafka.NewConsumer(&conf)
	if err != nil {
		fmt.Printf("Failed to create consumer: %s\n", err)
		os.Exit(1)
	}
	defer consumer.Close()

	// Subscribe to topic
	err = consumer.SubscribeTopics([]string{topic}, nil)
	if err != nil {
		fmt.Printf("Failed to subscribe to topic %s: %s\n", topic, err)
		os.Exit(1)
	}

	fmt.Printf("Listening on topic: %s\n", topic)

	// Set up a channel for handling signals to terminate
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGINT, syscall.SIGTERM)

	// Process messages or terminate
	run := true
	messageCount := 0
	maxMessages := 10

	for run && messageCount < maxMessages {
		select {
		case sig := <-sigchan:
			fmt.Printf("Caught signal %v: terminating\n", sig)
			run = false
		default:
			ev := consumer.Poll(100)
			if ev == nil {
				continue
			}

			switch e := ev.(type) {
			case *kafka.Message:
				messageCount++
				value := e.Value

				// Process as JSON
				handleJSONMessage(value, messageCount, maxMessages)

			case kafka.Error:
				fmt.Fprintf(os.Stderr, "ERROR: %v\n", e)
				if e.Code() == kafka.ErrAllBrokersDown {
					run = false
				}
			default:
				// Ignore other event types
			}
		}
	}

	fmt.Printf("✅ Consumed %d messages from %s\n", messageCount, topic)
	fmt.Println("Consumer closed")
}
