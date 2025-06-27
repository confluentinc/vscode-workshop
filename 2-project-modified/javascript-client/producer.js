const { Kafka, logLevel } = require("@confluentinc/kafka-javascript").KafkaJS;
const { faker } = require("@faker-js/faker");
require("dotenv").config();

// Parse brokers into array first
const brokersList = process.env.CC_BOOTSTRAP_SERVER ? process.env.CC_BOOTSTRAP_SERVER.split(',') : [];

const kafkaConfig = {
  clientId: process.env.CLIENT_ID,
  brokers: brokersList,
  logLevel: logLevel.ERROR // Reduce logging to only errors
};

const topic = process.env.CC_TOPIC;

if (!topic) {
  console.error("⚠️ No topic specified");
  process.exit(1);
}

// Check for local environment
const isLocal = brokersList.some(broker => 
  broker.includes('localhost') || broker.includes('127.0.0.1') || broker.includes('kafka:')
);

if (isLocal) {
  console.log("🐳 Local broker detected: using PLAINTEXT");
  console.log("🔄 Using topic: " + topic + " (will be auto-created if it doesn't exist)");
} else {
  console.log("☁️ Non-local broker detected: using SASL_SSL");
  kafkaConfig.ssl = true;
  kafkaConfig.sasl = {
    mechanism: "PLAIN",
    username: process.env.CC_API_KEY,
    password: process.env.CC_API_SECRET
  };
}


const kafka = new Kafka({ kafkaJS: kafkaConfig });
const producer = kafka.producer();
const admin = kafka.admin();

async function connectProducer() {
  try {
    await producer.connect();
    const mode = isLocal ? "local" : "Confluent Cloud";
    console.log(`✅ Connected to Kafka broker in ${mode}`);
    console.log("⚠️ Not using Schema Registry");

    // Only perform topic check in non-local environments
    if (!isLocal) {
      await admin.connect();
      const topics = await admin.listTopics();
      
      if (!topics.includes(topic)) {
        console.error(`❌ Error: Topic '${topic}' does not exist.`);
        await producer.disconnect();
        await admin.disconnect();
        process.exit(1);
      }
      
      await admin.disconnect();
    }
  } catch (error) {
    if (!isLocal) {
      console.error(`❌ Error connecting to Kafka: ${error.message}`);
      process.exit(1);
    } else {
      throw error; // Re-throw for local environments
    }
  }
}

// Produce messages
async function run() {
  const MAX_MESSAGES = 10;
  try {
    console.log(`Publishing to topic: ${topic}`);
    // Produce messages
    for (let i = 0; i < MAX_MESSAGES; i++) {
      const transactionId = faker.string.uuid();
      const messageValue = {
        TransactionId: transactionId,
        AccountNumber: faker.finance.iban(),
        Amount: parseFloat((faker.number.float({ min: 10, max: 10000, multipleOf: 0.01 })).toFixed(2)),
        Currency: faker.finance.currencyCode(),
        Timestamp: faker.date.recent().toISOString(),
        TransactionType: faker.helpers.arrayElement(["deposit", "withdrawal", "transfer", "payment"]),
        Status: faker.helpers.arrayElement(["pending", "completed", "failed"])
      };
      
      try {
        // Serialize with JSON
        const serializedValue = JSON.stringify(messageValue);
        
        await producer.send({
          topic,
          messages: [{ 
            key: transactionId,
            value: serializedValue 
          }]
        });
        
        console.log(`Produced message ${i + 1}/${MAX_MESSAGES}: ${JSON.stringify(messageValue)}`);
      } catch (serializationError) {
        console.error(`⚠️ Error serializing/sending message: ${serializationError.message}`);
        console.error(serializationError.stack);
        
      }
      
      await new Promise((resolve) => setTimeout(resolve, 100)); 
    }
    console.log(`✅ Successfully produced ${MAX_MESSAGES} messages to topic ${topic}`);
  } catch (err) {
    console.error("Error during message production:", err);
  } finally {
    await producer.disconnect();
    console.log("Producer closed");
  }
}

// Main execution
(async () => {
  await connectProducer();
  await run();
})();

// Graceful shutdown
const shutdown = async () => {
  try {
    await producer.disconnect();
    console.log("Producer disconnected successfully");
    process.exit(0);
  } catch (error) {
    console.error("Error during shutdown:", error);
    process.exit(1);
  }
};

// Signal handlers
const signalTraps = ["SIGTERM", "SIGINT", "SIGUSR2"];
signalTraps.forEach((type) => {
  process.once(type, shutdown);
});

process.on("unhandledRejection", shutdown);
process.on("uncaughtException", shutdown);

module.exports = { producer };