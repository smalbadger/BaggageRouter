from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from common.redis_client import RedisClient
from common.models import Bag
from prometheus_client import Counter, Histogram
from prometheus_client.core import CollectorRegistry
import time

class BagConsumer(BaseApp):
    def __init__(self, prometheus_port: int = 8002):
        super().__init__("bag_consumer", prometheus_port)
        self.kafka_client = KafkaClient(consumer_group="bag-consumer-group")
        self.redis_client = RedisClient()

    def _setup_metrics(self):
        self.processed_messages = Counter(
            'processed_bags_total',
            'Number of bag messages processed'
        )
        self.processing_time = Histogram(
            'bag_processing_seconds',
            'Time spent processing bag messages'
        )

    def process_messages(self, messages):
        bags = [
            Bag(
                id=msg['id'],
                flights=msg['flights']
            ) for msg in messages
        ]
        self.redis_client.upsert_bags(bags)
        self.processed_messages.inc(len(bags))

    def run(self):
        self.logger.info("Starting Bag Consumer")
        while True:
            try:
                with self.processing_time.time():
                    self.kafka_client.consume_batch(
                        topic="bags",
                        batch_size=1000,
                        timeout_ms=1000,
                        process_messages=self.process_messages
                    )
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
            
            time.sleep(1)

if __name__ == "__main__":
    consumer = BagConsumer()
    consumer.run() 