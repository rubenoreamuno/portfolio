"""
Apache Spark Streaming Job
Processes real-time events from Kafka with windowed aggregations
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json

class StreamingProcessor:
    """Real-time event stream processor"""
    
    def __init__(self):
        self.spark = self._create_spark_session()
    
    def _create_spark_session(self):
        """Create Spark session with Kafka integration"""
        return SparkSession.builder \
            .appName("RealTimeStreamingPipeline") \
            .config("spark.sql.streaming.checkpointLocation", "/tmp/checkpoint") \
            .config("spark.sql.streaming.schemaInference", "true") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .getOrCreate()
    
    def read_from_kafka(self, bootstrap_servers, topic):
        """Read stream from Kafka"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", bootstrap_servers) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .option("failOnDataLoss", "false") \
            .load()
    
    def parse_events(self, kafka_df):
        """Parse JSON events from Kafka"""
        schema = StructType([
            StructField("event_id", StringType()),
            StructField("timestamp", LongType()),
            StructField("event_type", StringType()),
            StructField("user_id", StringType()),
            StructField("properties", MapType(StringType(), StringType()))
        ])
        
        return kafka_df.select(
            from_json(col("value").cast("string"), schema).alias("data"),
            col("timestamp").alias("kafka_timestamp")
        ).select(
            "data.*",
            "kafka_timestamp"
        ).withColumn(
            "event_time", from_unixtime(col("timestamp") / 1000)
        )
    
    def aggregate_by_window(self, events_df, window_duration="1 minute"):
        """Windowed aggregations"""
        return events_df \
            .withWatermark("event_time", "10 minutes") \
            .groupBy(
                window(col("event_time"), window_duration),
                col("event_type")
            ) \
            .agg(
                count("*").alias("event_count"),
                countDistinct("user_id").alias("unique_users"),
                max("timestamp").alias("latest_timestamp")
            ) \
            .select(
                col("window.start").alias("window_start"),
                col("window.end").alias("window_end"),
                col("event_type"),
                col("event_count"),
                col("unique_users")
            )
    
    def write_to_console(self, df):
        """Write results to console (for development)"""
        return df.writeStream \
            .outputMode("update") \
            .format("console") \
            .option("truncate", "false") \
            .trigger(processingTime='10 seconds') \
            .start()
    
    def write_to_parquet(self, df, output_path):
        """Write results to Parquet (for production)"""
        return df.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", f"{output_path}/checkpoint") \
            .partitionBy("event_type", "window_start") \
            .trigger(processingTime='1 minute') \
            .start()
    
    def process_stream(self, bootstrap_servers, topic, output_path=None):
        """Main processing pipeline"""
        # Read from Kafka
        kafka_df = self.read_from_kafka(bootstrap_servers, topic)
        
        # Parse events
        events_df = self.parse_events(kafka_df)
        
        # Aggregate
        aggregated_df = self.aggregate_by_window(events_df)
        
        # Write results
        if output_path:
            query = self.write_to_parquet(aggregated_df, output_path)
        else:
            query = self.write_to_console(aggregated_df)
        
        query.awaitTermination()

if __name__ == "__main__":
    processor = StreamingProcessor()
    processor.process_stream(
        bootstrap_servers="localhost:9092",
        topic="events",
        output_path="/tmp/streaming_output"
    )

