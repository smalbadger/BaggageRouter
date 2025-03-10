from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from common.redis_client import RedisClient
from common.models import Bag
from prometheus_client import Counter, Histogram
import time

class BagConsumer(BaseApp):
    def __init__(self, prometheus_port: int = 8002):
        super().__init__("bag_consumer", prometheus_port)
        self.kafka_client = KafkaClient(consumer_group="bag-consumer-group")
        self.redis_client = RedisClient()
        self._setup_metrics()

    def _setup_metrics(self):
        self.processed_messages = Counter(
            'processed_bags_total',
            'Number of bag messages processed'
        )
        self.processing_time = Histogram(
            'bag_processing_seconds',
            'Time spent processing bag messages'
        )

    def process_message(self, message):
        bag = Bag(
            id=message['id'],
            flights=message['flights']
        )
        self.redis_client.upsert_bags([bag])
        self.processed_messages.inc()

    def run(self):
        self.logger.info("Starting Bag Consumer")
        while True:
            try:
                with self.processing_time.time():
                    self.kafka_client.consume_batch(
                        topic="bags",
                        batch_size=100,
                        timeout_ms=1000,
                        process_message=self.process_message
                    )
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
                time.sleep(1)

if __name__ == "__main__":
    consumer = BagConsumer()
    consumer.run() 