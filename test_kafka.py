#!/usr/bin/env python3
"""Test script for Kafka producer and consumer"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kafka'))

from producer import EventProducer
from kafka import KafkaConsumer
import json
import time

def test_producer():
    """Test Kafka producer"""
    print("Testing producer...")
    producer = EventProducer()
    producer.create_producer(use_avro=False)
    event = producer.generate_event()
    print(f'Generated event: {event}')
    
    try:
        producer.producer.send('test-events', event)
        producer.producer.flush()
        print('✓ Event sent successfully')
        return True
    except Exception as e:
        print(f'✗ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_consumer():
    """Test Kafka consumer"""
    print("Testing consumer...")
    consumer = KafkaConsumer(
        'test-events',
        bootstrap_servers=['localhost:9092'],
        auto_offset_reset='earliest',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        consumer_timeout_ms=10000
    )
    
    messages = []
    for message in consumer:
        messages.append(message.value)
        if len(messages) >= 1:
            break
    
    consumer.close()
    
    if messages:
        print(f'✓ Received message: {messages[0]}')
        return True
    else:
        print('✗ No messages received')
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'consumer':
        success = test_consumer()
    else:
        success = test_producer()
    
    sys.exit(0 if success else 1)

