from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from common.redis_client import RedisClient
from common.models import Flight
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client.core import CollectorRegistry
import time

class FlightConsumer(BaseApp):
    def __init__(self, prometheus_port: int = 8001):
        super().__init__("flight_consumer", prometheus_port)
        self.kafka_client = KafkaClient(consumer_group="flight-consumer-group")
        self.redis_client = RedisClient()

    def _setup_metrics(self):
        self.processed_messages = Counter(
            'processed_flights_total',
            'Number of flight messages processed'
        )
        self.processing_time = Histogram(
            'flight_processing_seconds',
            'Time spent processing flight messages'
        )
        self.latest_flight_arrival = Gauge(
            'latest_consumed_flight_arrival_timestamp',
            'Timestamp of the latest consumed flight arrival time'
        )

    def process_messages(self, messages):
        flights = [
            Flight(
                id=msg['id'],
                departure_time=datetime.fromtimestamp(msg['departure_time']),
                arrival_time=datetime.fromtimestamp(msg['arrival_time']),
                bags=msg['bags']
            ) for msg in messages
        ]
        self.redis_client.upsert_flights(flights)
        self.processed_messages.inc(len(flights))
        if flights:
            self.latest_flight_arrival.set(max(f.arrival_time.timestamp() for f in flights))

    def run(self):
        self.logger.info("Starting Flight Consumer")
        while True:
            try:
                with self.processing_time.time():
                    self.kafka_client.consume_batch(
                        topic="flights",
                        batch_size=1000,
                        timeout_ms=1000,
                        process_messages=self.process_messages
                    )
            except Exception as e:
                self.logger.error(f"Error processing messages: {e}")
            
            time.sleep(1)

if __name__ == "__main__":
    consumer = FlightConsumer()
    consumer.run() 