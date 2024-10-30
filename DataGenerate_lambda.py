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
        "user_name": random.choice(["Alice", "Bob", "Charlie", "David", "Eve"]),
        "card_number": f"{random.randint(4000, 4999)}-****-****-{random.randint(1000, 9999)}",
        "transaction_amount": round(random.uniform(10.0, 500.0), 2),
        "timestamp_utc": datetime.now(),
        "location": random.choice(["New York", "Delhi", "Kolkata", "London", "Tokyo"])
    }
    return transaction

def lambda_handler(event, context):
    # Generate a mock transaction
    for i in range(50):
        transaction = generate_random_transaction()
        
        # Convert transaction to JSON format
        data = json.dumps(transaction)
        
        try:
            # Send data to Kinesis stream
            response = kinesis_client.put_record(
                StreamName=KINESIS_STREAM_NAME,
                Data=data,
                PartitionKey=str(transaction["transaction_id"])
            )
            print(f"Transaction sent to Kinesis: {transaction}")
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Transaction sent successfully",
                    "transaction_id": transaction["transaction_id"],
                    "kinesis_response": response
                })
            }
        except Exception as e:
            print(f"Error sending transaction to Kinesis: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "message": "Error sending transaction",
                    "error": str(e)
                })
            }
