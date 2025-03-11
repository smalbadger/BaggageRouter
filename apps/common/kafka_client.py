from kafka import KafkaConsumer, KafkaProducer
import json
from typing import List, Callable, Any
from datetime import datetime
import time

class KafkaClient:
    def __init__(
        self,
        bootstrap_servers: List[str] = ['kafka:29092'],
        consumer_group: str = None
    ):
        self.bootstrap_servers = bootstrap_servers
        self.consumer_group = consumer_group
        self.producer = None
        self.consumer = None

    def _connect_with_retry(self, connect_func, max_retries=5, retry_interval=5):
        for i in range(max_retries):
            try:
                return connect_func()
            except Exception as e:
                if i == max_retries - 1:
                    raise e
                time.sleep(retry_interval)

    def get_consumer(self, topic: str) -> KafkaConsumer:
        if not self.consumer:
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.consumer_group,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                auto_offset_reset='earliest'
            )
        return self.consumer

    def get_producer(self) -> KafkaProducer:
        if not self.producer:
            self.producer = self._connect_with_retry(
                lambda: KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                    buffer_memory=67108864 * 4,  # 256MB buffer (4x default)
                    batch_size=16384 * 4,  # 64KB batches (4x default)
                    linger_ms=100,  # Wait up to 100ms for batches to fill
                    compression_type='gzip'  # Enable compression
                )
            )
        return self.producer

    def consume_batch(
        self,
        topic: str,
        batch_size: int,
        timeout_ms: int,
        process_messages: Callable[[List[Any]], None]
    ):
        consumer = self.get_consumer(topic)
        messages = consumer.poll(timeout_ms=timeout_ms, max_records=batch_size)
        
        batch = []
        for topic_partition, records in messages.items():
            for record in records:
                batch.append(record.value)
        
        if batch:
            process_messages(batch) 