const { Kafka, logLevel } = require("@confluentinc/kafka-javascript").KafkaJS;
require("dotenv").config();

// Parse brokers into array first
const brokersList = process.env.CC_BOOTSTRAP_SERVER ? process.env.CC_BOOTSTRAP_SERVER.split(',') : [];

// Kafka configuration
const kafkaConfig = {
  clientId: process.env.CLIENT_ID,
  brokers: brokersList,
  logLevel: logLevel.ERROR // Reduce logging to only errors
};

// Topic to use
const topic = process.env.CC_TOPIC;
const MAX_MESSAGES = 10;

// Check if topic is specified
if (!topic) {
  console.error("⚠️ No topic specified");
  process.exit(1);
}

// Check for local environment
const isLocal = brokersList.some(broker => 
  broker.includes('localhost') || broker.includes('127.0.0.1') || broker.includes('kafka:')
);

// Configure security based on environment
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
const admin = kafka.admin();

const consumerConfig = {
  groupId: process.env.GROUP_ID || "js-consumer-group-id",
  fromBeginning: true
};

const consumer = kafka.consumer({ kafkaJS: consumerConfig });

async function consumerStart() {
  try {
    await consumer.connect();
    const mode = isLocal ? "local" : "Confluent Cloud";
    console.log(`✅ Connected to Kafka broker in ${mode}`);

    // Check if topic exists in non-local environments
    if (!isLocal) {
      try {
        await admin.connect();
        const topics = await admin.listTopics();
        
        if (!topics.includes(topic)) {
          console.error(`❌ Error: Topic '${topic}' does not exist in the Kafka cluster`);
          await consumer.disconnect();
          await admin.disconnect();
          process.exit(1);
        }
        
        await admin.disconnect();
      } catch (adminError) {
        console.error(`❌ Error checking topics: ${adminError.message}`);
        await consumer.disconnect();
        process.exit(1);
      }
    }
    
    // For local environments, add retry logic for non-existing topic subscription
    if (isLocal) {
      let retries = 5;
      let subscribed = false;
      
      while (retries > 0 && !subscribed) {
        try {
          await consumer.subscribe({ topic });
          subscribed = true;
          console.log(`Listening on topic: ${topic}`);
        } catch (subscribeError) {
          retries--;
          if (retries > 0) {
            console.log(`Topic '${topic}' not ready yet. Retrying in 2 seconds... (${retries} attempts left)`);
            await new Promise(resolve => setTimeout(resolve, 2000));
          } else {
            throw subscribeError;
          }
        }
      }
    } else {
      // Non-local environment - normal subscription
      await consumer.subscribe({ topic });
      console.log(`Listening on topic: ${topic}`);
    }
    
    let messageCount = 0;
    
    // Using the format from the official reference
    await consumer.run({
      eachMessage: async ({ topic, message }) => {
        messageCount++;
        
        try {
          const value = message.value.toString();
          JSON.parse(value);
          console.log(`Consumed message ${messageCount}/${MAX_MESSAGES}: ${value}`);
        } catch (error) {
          console.error(`⚠️ Error parsing message as JSON: ${error.message}`);
          console.error(`Raw message content: ${message.value.toString()}`);
        }
        
        if (messageCount >= MAX_MESSAGES) {
          console.log(`✅ Consumed ${messageCount} messages from ${topic}`);
          console.log("Consumer closed");
          await consumer.disconnect();
          process.exit(0);
        }
      }
    });
  } catch (error) {
    console.error(`⚠️ Consumer error: ${error.message}`);
  }
}

consumerStart();

// Graceful shutdown handling
const signalTraps = ["SIGTERM", "SIGINT", "SIGUSR2"];

// Handle process signals
signalTraps.forEach((type) => {
  process.once(type, async () => {
    try {
      console.log(`Received ${type}, shutting down...`);
      await consumer.disconnect();
      console.log("Consumer closed");
      process.exit(0);
    } catch (error) {
      console.error(`Error during shutdown: ${error.message}`);
      process.exit(1);
    }
  });
});

// Handle unhandled errors
process.on('unhandledRejection', async (error) => {
  console.error(`Unhandled Rejection: ${error.message}`);
  await consumer.disconnect();
  console.log("Consumer closed");
  process.exit(1);
});

process.on('uncaughtException', async (error) => {
  console.error(`Uncaught Exception: ${error.message}`);
  await consumer.disconnect();
  console.log("Consumer closed");
  process.exit(1);
});

module.exports = { consumer };