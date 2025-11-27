"""
Kafka Producer for Real-Time Event Streaming
Produces high-volume events to Kafka topics with schema validation
"""

import json
import time
import random
from datetime import datetime
try:
    from confluent_kafka import avro
    from confluent_kafka.avro import AvroProducer
    CONFLUENT_AVAILABLE = True
except ImportError:
    CONFLUENT_AVAILABLE = False

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

class EventProducer:
    """High-performance Kafka event producer"""
    
    def __init__(self, bootstrap_servers='localhost:9092', schema_registry_url='http://localhost:8081'):
        self.bootstrap_servers = bootstrap_servers
        self.schema_registry_url = schema_registry_url
        self.producer = None
        
    def create_producer(self, use_avro=True):
        """Initialize Kafka producer"""
        if use_avro and CONFLUENT_AVAILABLE:
            # Avro producer with schema registry
            value_schema = self._load_schema()
            self.producer = AvroProducer(
                {'bootstrap.servers': self.bootstrap_servers,
                 'schema.registry.url': self.schema_registry_url},
                default_value_schema=value_schema
            )
        elif KAFKA_AVAILABLE:
            # JSON producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,
                enable_idempotence=True
            )
        else:
            raise ImportError("Neither confluent-kafka nor kafka-python is installed")
    
    def _load_schema(self):
        """Load Avro schema"""
        schema_str = """
        {
            "type": "record",
            "name": "Event",
            "fields": [
                {"name": "event_id", "type": "string"},
                {"name": "timestamp", "type": "long"},
                {"name": "event_type", "type": "string"},
                {"name": "user_id", "type": "string"},
                {"name": "properties", "type": {"type": "map", "values": "string"}}
            ]
        }
        """
        return avro.loads(schema_str)
    
    def generate_event(self):
        """Generate sample event"""
        return {
            'event_id': f"evt_{int(time.time() * 1000)}_{random.randint(1000, 9999)}",
            'timestamp': int(time.time() * 1000),
            'event_type': random.choice(['page_view', 'click', 'purchase', 'signup']),
            'user_id': f"user_{random.randint(1, 10000)}",
            'properties': {
                'page': f"/page/{random.randint(1, 100)}",
                'source': random.choice(['web', 'mobile', 'api'])
            }
        }
    
    def produce_events(self, topic='events', num_events=1000, rate=100):
        """Produce events at specified rate"""
        if not self.producer:
            self.create_producer()
        
        success_count = 0
        error_count = 0
        
        for i in range(num_events):
            event = self.generate_event()
            
            try:
                # Produce with callback
                future = self.producer.produce(
                    topic=topic,
                    value=event,
                    callback=self._delivery_callback
                )
                
                # Flush periodically
                if i % 100 == 0:
                    self.producer.flush()
                
                success_count += 1
                
                # Rate limiting
                time.sleep(1.0 / rate)
                
            except Exception as e:
                error_count += 1
                print(f"Error producing event: {e}")
        
        # Final flush
        self.producer.flush()
        
        print(f"Produced {success_count} events, {error_count} errors")
    
    def _delivery_callback(self, err, msg):
        """Delivery callback for async produces"""
        if err:
            print(f"Message delivery failed: {err}")
        else:
            pass  # Success - can log if needed

if __name__ == "__main__":
    producer = EventProducer()
    producer.produce_events(num_events=10000, rate=1000)

