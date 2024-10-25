import faker
from datetime import datetime
import random
import os
import boto3
import json

fake = faker.Faker()
kinesis_client = boto3.client('kinesis')

def generate_data():
    """
    Generates random transactions using faker module.
    Return : A JSON object
    """
    transaction_data = {
        "transaction_id" : fake.uuid4(),
        "user_name": fake.name(),
        "location": fake.city_name(),
        "timestamp_utc": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        "transaction_amount": round(random.uniform(1.0, 1000.0), 2)
    }
    return transaction_data

def lambda_handler(event,context):
    stream_name = os.environ['STREAM_NAME']
    transaction_data = generate_data()
    try:
        response = kinesis_client.put_record(StreamName=stream_name,Data=json.dumps(transaction_data),partitionKey=transaction_data['transaction_id'])
        print("Data Delivered to kinesis")
    except Exception as e:
        print(f"Error sending data to kinesis : {e}")


