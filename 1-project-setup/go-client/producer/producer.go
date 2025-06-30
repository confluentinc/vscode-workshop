package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math"
	"math/rand"
	"os"	
	"strings"
	"time"
	"github.com/bxcodec/faker/v3"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/joho/godotenv"
)

// Transaction represents our business data model
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

	fmt.Printf("✅ Connected to Kafka (%s)\n", conf["bootstrap.servers"])
	return nil
}

func main() {
	err := godotenv.Load()
	if err != nil {
		log.Printf("Warning: Error loading .env file: %v", err)
	}

	bootstrapServer := os.Getenv("CC_BOOTSTRAP_SERVER")
	topic := os.Getenv("CC_TOPIC")

	conf := kafka.ConfigMap{
		"bootstrap.servers": bootstrapServer,
	}

	isLocal := isLocalKafka(bootstrapServer)

	if isLocal {
		conf["security.protocol"] = "PLAINTEXT"
		conf["client.id"] = "go-client"
		fmt.Println("🐳 Local broker detected: using PLAINTEXT")
	} else {
		conf["security.protocol"] = "SASL_SSL"
		conf["sasl.mechanisms"] = "PLAIN"
		conf["sasl.username"] = os.Getenv("CC_API_KEY")
		conf["sasl.password"] = os.Getenv("CC_API_SECRET")
		conf["client.id"] = os.Getenv("CLIENT_ID")
		fmt.Println("☁️ Non-local broker detected: using SASL_SSL")
	}

	// Verify Kafka connection and topic
	if err := verifyKafkaSetup(conf, topic, isLocal); err != nil {
		fmt.Printf("❌ Kafka configuration error - Exiting: %v\n", err)
		os.Exit(1)
	}

	// Create Kafka producer
	p, err := kafka.NewProducer(&conf)
	if err != nil {
		fmt.Printf("❌ Failed to create producer: %s\n", err)
		os.Exit(1)
	}
	defer p.Close()

	fmt.Println("🔄 Using plain JSON serialization (no Schema Registry)")

	fmt.Printf("Producing to topic '%s'...\n", topic)
	messageCount := 10
	deliveryChannel := make(chan kafka.Event, messageCount)

	// Start producing messages
	transactionTypes := []string{"deposit", "withdrawal", "transfer", "payment"}
	statuses := []string{"pending", "completed", "failed"}

	for i := 0; i < messageCount; i++ {
		// Create a transaction message
		txnID := faker.UUIDDigit()
		transaction := Transaction{
			TransactionId:   txnID,
			AccountNumber:   faker.CCNumber(),
			Amount:          math.Round(float64(rand.Intn(10000))+rand.Float64()*100) / 100,
			Currency:        "USD",
			Timestamp:       time.Now().Format(time.RFC3339),
			TransactionType: transactionTypes[rand.Intn(len(transactionTypes))],
			Status:          statuses[rand.Intn(len(statuses))],
		}

		var value []byte
		var serErr error

		// Use plain JSON serialization
		value, serErr = json.Marshal(transaction)
		if serErr != nil {
			log.Fatalf("Failed to serialize message to JSON: %s", serErr)
		}

		err = p.Produce(&kafka.Message{
			TopicPartition: kafka.TopicPartition{Topic: &topic, Partition: kafka.PartitionAny},
			Key:            []byte(txnID),
			Value:          value,
		}, deliveryChannel)

		if err != nil {
			fmt.Printf("❌ Failed to produce message: %s\n", err)
			os.Exit(1)
		}

		// Print message details
		fmt.Printf("Produced message %d/%d: ", i+1, messageCount)
		
		// When Schema Registry is not used, print the full JSON on one line
		fmt.Printf("%s\n", string(value))
	}

	// Wait for message deliveries
	p.Flush(5000)
	fmt.Printf("✅ Successfully produced %d messages to topic %s\n", messageCount, topic)
}
