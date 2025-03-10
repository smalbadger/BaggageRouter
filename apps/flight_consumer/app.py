from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from common.redis_client import RedisClient
from common.models import Flight
from datetime import datetime
from prometheus_client import Counter, Histogram
import time

class FlightConsumer(BaseApp):
    def __init__(self, prometheus_port: int = 8001):
        super().__init__("flight_consumer", prometheus_port)
        self.kafka_client = KafkaClient(consumer_group="flight-consumer-group")
        self.redis_client = RedisClient()
        self._setup_metrics()

    def _setup_metrics(self):
        self.processed_messages = Counter(
            'processed_flights_total',
            'Number of flight messages processed'
        )
        self.processing_time = Histogram(
            'flight_processing_seconds',
            'Time spent processing flight messages'
        )

    def process_message(self, message):
        flight = Flight(
            id=message['id'],
            departure_time=datetime.fromtimestamp(message['departure_time']),
            arrival_time=datetime.fromtimestamp(message['arrival_time']),
            bags=message['bags']
        )
        self.redis_client.upsert_flights([flight])
        self.processed_messages.inc()

    def run(self):
        self.logger.info("Starting Flight Consumer")
        while True:
            try:
                with self.processing_time.time():
                    self.kafka_client.consume_batch(
                        topic="flights",
                        batch_size=100,
                        timeout_ms=1000,
                        process_message=self.process_message
                    )
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
                time.sleep(1)

if __name__ == "__main__":
    consumer = FlightConsumer()
    consumer.run() 