#!/usr/bin/env python

import os
import json
from dotenv import load_dotenv
from confluent_kafka import Producer
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
        
        if topic not in metadata.topics:
            print(f"Topic '{topic}' not found.")
            return False       
        return True
    except Exception as e:
        # Log the specific exception for easier troubleshooting
        print(f"⚠️ Kafka connection error: {e}")
        return False


def delivery_callback(err, msg):
    if err:
        print(f"ERROR: Message failed delivery: {err}")


if __name__ == "__main__":
    load_dotenv()

    topic = os.getenv("CC_TOPIC")
    bootstrap_server = os.getenv("CC_BOOTSTRAP_SERVER")

    # Check for local environments including Docker
    is_local = any(local_indicator in bootstrap_server for local_indicator in 
                  ["localhost", "127.0.0.1", "kafka:"])

    kafka_config = {
        "bootstrap.servers": bootstrap_server,
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

    if verify_kafka_setup(kafka_config, topic, is_local) is False:
        print(f"❌ Kafka configuration error - Exiting")
        raise RuntimeError("Failed to verify Kafka setup")
    print(f"✅ Connected to Kafka ({bootstrap_server})")
    
    # Initialize producer
    producer = Producer(kafka_config)

    serializer = None
    print("⚠️ Using basic JSON serialization (no Schema Registry)")
    
    print(f"Producing to topic '{topic}'...")

    # Read sample_data.json and send each order as a message
    with open("sample_data.json", "r") as f:
        orders = json.load(f)

    message_count = len(orders)
    for i, order in enumerate(orders):
        key = str(order.get("orderid", ""))
        serialized_value = json.dumps(order).encode('utf-8')

        producer.produce(topic, key=key, value=serialized_value, callback=delivery_callback)
        producer.poll(100)

        print(f"Produced message {i+1}/{message_count}: {json.dumps(order)}")

    producer.flush()
    print(f"✅ Successfully produced {message_count} messages to topic {topic}")
    