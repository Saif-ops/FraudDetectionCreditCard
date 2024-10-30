import boto3
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import StringType, DoubleType, TimestampType, StructType, StructField



# Create Spark session with the specified configuration
spark = SparkSession.builder \
    .appName("FraudDetectionApp") \
    .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
    .getOrCreate()

# Define schema
schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("user_name", StringType(), True),
    StructField("card_number", StringType(), True),
    StructField("transaction_amount", DoubleType(), True),
    StructField("timestamp_utc", TimestampType(), True),
    StructField("location", StringType(), True)
])

def read_from_kinesis(stream_name, region):

    df = spark.readStream.format("aws-kinesis") \
    .option("kinesis.region", "us-east-1") \
    .option("kinesis.streamName", stream_name) \
    .option("kinesis.consumerType", "GetRecords") \
    .option("kinesis.endpointUrl", "https://kinesis.us-east-1.amazonaws.com") \
    .option("kinesis.startingposition", "LATEST") \
    .load()

    transaction_data = df.select(from_json(col("data").cast('string'), schema).alias("transaction_data"))
    transaction_data = transaction_data.select('transaction_data.*')

    # Set watermark for time-based operations
    transaction_data = transaction_data.withWatermark("timestamp_utc", "2 minutes")

    # Anomaly detection logic
    no_transaction_in_two_minutes = transaction_data.groupBy(
        window("timestamp_utc", "2 minutes"), "card_number", "user_name"
    ).agg(count("transaction_id").alias("transactions_within_two_minutes"))

    no_of_transaction_for_different_locations = transaction_data.groupBy(
        window("timestamp_utc", "2 minutes"), "card_number", "user_name"
    ).agg(approx_count_distinct("location").alias("different_locations"))

    suspicious_transactions_1 = no_of_transaction_for_different_locations \
        .filter(no_of_transaction_for_different_locations.different_locations > 1) \
        .withColumn("suspicion_type", lit(2)) \
        .select("card_number", "user_name", "suspicion_type")

    suspicious_transactions_2 = no_transaction_in_two_minutes \
        .filter(no_transaction_in_two_minutes.transactions_within_two_minutes > 1) \
        .withColumn("suspicion_type", lit(1)) \
        .select("card_number", "user_name", "suspicion_type")

    suspicious_transaction = suspicious_transactions_1.union(suspicious_transactions_2)

    # Grouping and creating a message for each card/user
    suspicious_transaction_1 = suspicious_transaction.groupBy("card_number", "user_name") \
        .agg(collect_set("suspicion_type").alias("suspicion_types"))

    suspicious_transaction_2 = suspicious_transaction_1.withColumn(
        "Message_to_user",
        when(col("suspicion_types") == expr("array(1,2)"),
             lit("Multiple Transactions Detected from different locations within 2 minutes which is not normal")) \
        .otherwise(lit("Multiple Transactions Detected within 2 minutes which is not normal"))
    )

    return suspicious_transaction_2

def send_sns_notification(card_number, message, topic_arn):
    """Send SNS notification."""
    # Initialize SNS client
    sns_client = boto3.client('sns', region_name='us-east-1')
    response = sns_client.publish(TopicArn=topic_arn, Message=f"Anomaly detected for credit card: {card_number}. Reason: {message}")
    return response

if __name__ == "__main__":
    stream_name = 'transaction_stream'
    region = 'us-east-1'
    topic_arn = 'arn:aws:sns:us-east-1:381492121275:Fraud_delivery'

    # Read from Kinesis stream
    suspicious_transactions_df = read_from_kinesis(stream_name, region)

    # Process each batch and send SNS notifications
    query = suspicious_transactions_df.writeStream \
        .foreachBatch(lambda df, epoch_id: df.rdd.foreach(lambda row: send_sns_notification(row['card_number'], row['Message_to_user'], topic_arn))) \
        .outputMode("update") \
        .option("checkpointLocation", "s3://spark-streaming-01/Fraud_detection_codebase/checkpoint_location/") \
        .start()

    # Await termination of the streaming job
    print("Streaming job is now running. Press Ctrl+C to stop...")
    query.awaitTermination()
