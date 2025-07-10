#!/usr/bin/env python

import os
import json
from dotenv import load_dotenv
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
import requests
from confluent_kafka.schema_registry import Schema
from confluent_kafka.schema_registry.avro import AvroSerializer
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.serialization import SerializationContext, MessageField


def verify_schema_registry(sr_url, sr_key, sr_secret, is_local):        
    try:
        auth = (sr_key, sr_secret) if is_local is False and sr_key and sr_secret else None
        response = requests.get(f"{sr_url}/subjects", auth=auth, timeout=5)
        return 200 <= response.status_code < 300
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Schema Registry connection error: {e}")
        return False


def create_serializer(sr_url, sr_key, sr_secret, is_local):
    # Always read schema from local file
    schema_file_path = os.path.join(os.path.dirname(__file__), "schema-registry-data", "sample-schema.avsc")
    with open(schema_file_path, 'r') as schema_file:
        schema_str = schema_file.read()
    
    # Configure Schema Registry client - don't pass auth for local mode
    sr_conf = {
        'url': sr_url
    }
    
    if is_local is False and sr_key and sr_secret:
        sr_conf['basic.auth.user.info'] = f"{sr_key}:{sr_secret}"
    
    sr_client = SchemaRegistryClient(sr_conf)
    
    # Register the schema with Schema Registry (both local and cloud)
    schema_subject = os.getenv("CC_TOPIC") + "-value"
    try:
        # Check if schema already exists
        try:
            existing_schema = sr_client.get_latest_version(schema_subject)
            if is_local is False:
                print(f"Schema already exists for subject {schema_subject}")
        except Exception:
            # Register schema if it doesn't exist
            avro_schema = Schema(schema_str, schema_type="AVRO")
            schema_id = sr_client.register_schema(schema_subject, avro_schema)
            print(f"Successfully registered schema (ID: {schema_id}) for subject {schema_subject}")
    except Exception as e:
        print(f"Error interacting with Schema Registry: {e}")
            
    return AvroSerializer(sr_client, schema_str)


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

    sr_url = os.getenv("CC_SCHEMA_REGISTRY_URL")
    sr_key = os.getenv("CC_SR_API_KEY")
    sr_secret = os.getenv("CC_SR_API_SECRET")
    verify_schema_registry(sr_url, sr_key, sr_secret, is_local)
    try:
        serializer = create_serializer(sr_url, sr_key, sr_secret, is_local)
        mode = "local" if is_local else "cloud"
        print(f"✅ Using Schema Registry in {mode} mode at {sr_url}")
    except Exception as e:
        print(f"⚠️ Schema Registry error: {e}")
        print("⚠️ Using basic JSON serialization (no Schema Registry)")
        serializer = None
    
    # Load sample data from JSON file
    sample_data_path = os.path.join(os.path.dirname(__file__), "sample_data.json")
    with open(sample_data_path, 'r') as f:
        sample_orders = json.load(f)
    
    print(f"Producing to topic '{topic}'...")
    print(f"Loaded {len(sample_orders)} sample orders from sample_data.json")

    # Send messages based on sample data
    message_count = len(sample_orders)
    for i, order in enumerate(sample_orders):
        key = str(order['orderid'])
        value = {
            "ordertime": order['ordertime'],
            "orderid": order['orderid'],
            "itemid": order['itemid'],
            "itemName": order['itemName'],
            "orderunits": order['orderunits'],
            "orderAmount": order['orderAmount'],
            "address": {
                "city": order['address']['city'],
                "state": order['address']['state'],
                "zipcode": order['address']['zipcode']
            }
        }

        # Use Confluent Schema Registry serialization for both local and cloud modes
        serialized_value = serializer(value, SerializationContext(topic, MessageField.VALUE))

        producer.produce(topic, key=key, value=serialized_value, callback=delivery_callback)
        producer.poll(100)

        print(f"Produced message {i+1}/{message_count}: ", end="")
        print(f"Order {value['orderid']} - {value['itemName']} (${value['orderAmount']}) to {value['address']['city']}, {value['address']['state']}")

    producer.flush()
    print(f"✅ Successfully produced {message_count} messages to topic {topic}")
    