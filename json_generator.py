import json
import random
#import boto3
from datetime import datetime, timedelta

# Initialize the Kinesis client
#kinesis_client = boto3.client('kinesis')

# Define the Kinesis stream name
#KINESIS_STREAM_NAME = "transaction_stream"

def generate_random_transaction():
    # Randomly generated transaction data
    transaction = {
        "transaction_id": random.randint(100000, 999999),
        "user_name": random.choice(["Alice", "Bob", "Charlie"]),
        "card_number": f"{random.randint(1,20)}",
        "transaction_amount": round(random.uniform(10.0, 500.0), 2),
        "timestamp_utc": str(datetime.now()),
        "location": random.choice(["New York", "Delhi", "Kolkata"])
    }
    return transaction

def main():
    # Generate a mock transaction
    for i in range(50):
        transaction = generate_random_transaction()
        # Convert transaction to JSON format
        data = json.dumps(transaction)
        print(data)

if __name__ == "__main__":
    main()
        
       