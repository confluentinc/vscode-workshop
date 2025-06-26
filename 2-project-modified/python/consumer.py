#!/usr/bin/env python

import os
import json
from dotenv import load_dotenv
from confluent_kafka import Consumer, KafkaError
from confluent_kafka.admin import AdminClient


def verify_kafka_setup(kafka_config, topic, is_local):
    if topic is None or topic == "":
        print("⚠️ No topic specified")
        return False
    
    # Local mode still needs to verify topic existence, but no credential check
    if is_local:
        return True
    try:
        admin_client = AdminClient(kafka_config)
        metadata = admin_client.list_topics(timeout=5)
        return topic in metadata.topics
    except Exception as e:
        print(f"⚠️ Kafka connection error: {e}")
        return False


def get_field(data, field):
    snake = ''.join(['_' + c.lower() if c.isupper() else c for c in field]).lstrip('_')
    return data.get(field) or data.get(snake) or f"<missing {field}>"


if __name__ == "__main__":
    load_dotenv()

    topic = os.getenv("CC_TOPIC")
    bootstrap_server = os.getenv("CC_BOOTSTRAP_SERVER")

    is_local = any(local_indicator in bootstrap_server for local_indicator in 
                  ["localhost", "127.0.0.1", "kafka:"])

    kafka_config = {
        "bootstrap.servers": bootstrap_server,
        "group.id": os.getenv("GROUP_ID", "python-consumer-group-id"),
        "auto.offset.reset": "earliest",
        "client.id": os.getenv("CLIENT_ID"),
    }

    # Configure security based on environment
    if is_local:
        kafka_config["security.protocol"] = "PLAINTEXT"
        print("🧪 Using PLAINTEXT protocol for local broker")
    else:
        kafka_config.update({
            "security.protocol": "SASL_SSL",
            "sasl.mechanisms": "PLAIN",
            "sasl.username": os.getenv("CC_API_KEY"),
            "sasl.password": os.getenv("CC_API_SECRET"),
        })
        print("☁️ Using SASL_SSL protocol for cloud broker")

    # Verify Kafka setup before proceeding
    if verify_kafka_setup(kafka_config, topic, is_local) is False:
        print(f"❌ Kafka configuration error - Exiting")
        raise RuntimeError("Failed to verify Kafka setup")
    print(f"✅ Connected to Kafka ({bootstrap_server})")
    
    deserializer = None

    # Initialize and configure consumer
    consumer = Consumer(kafka_config)
    consumer.subscribe([topic])
    
    print("⚠️ Using basic JSON deserialization (no Schema Registry)")
    
    print(f"Listening on topic: {topic}")

    # Consume messages
    message_count = 10
    try:
        count = 0
        while count < message_count:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"ERROR: {msg.error()}")
                continue

            count += 1
            value = msg.value()

            try:
                print(f"Message {count}/{message_count}: ", end="")
                try:
                    decoded = json.loads(value.decode("utf-8"))
                    print(json.dumps(decoded))
                except UnicodeDecodeError:
                    print(f"Binary message, size: {len(value)} bytes")
            except Exception as e:
                print(f"⚠️ Error processing message: {e}")

        print(f"✅ Consumed {count} messages from {topic}")
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        consumer.close()
        print("Consumer closed")
