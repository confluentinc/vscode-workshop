import json

def produce_from_json(json_file, producer, topic):
    with open(json_file, 'r') as f:
        data = json.load(f)
        for record in data:
            producer.produce(topic, value=json.dumps(record))
            producer.flush()

if __name__ == "__main__":
    # Replace the random data generation with reading from sample_data.json
    produce_from_json("sample_data.json", producer, topic)