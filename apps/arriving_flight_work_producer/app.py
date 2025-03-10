from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from common.redis_client import RedisClient
from prometheus_client import Counter, Histogram
import time
from datetime import datetime

class ArrivingFlightWorkProducer(BaseApp):
    def __init__(self, prometheus_port: int = 8003):
        super().__init__("arriving_flight_work_producer", prometheus_port)
        self.kafka_client = KafkaClient()
        self.redis_client = RedisClient()
        self.producer = self.kafka_client.get_producer()
        self._setup_metrics()

    def _setup_metrics(self):
        self.produced_messages = Counter(
            'produced_arriving_flight_work_total',
            'Number of arriving flight work messages produced'
        )
        self.processing_time = Histogram(
            'arriving_flight_work_processing_seconds',
            'Time spent processing arriving flight work'
        )

    def produce_work(self):
        current_time = datetime.now().timestamp()
        work_items = self.redis_client.get_arriving_flight_work(current_time)
        
        for work in work_items:
            self.producer.send('arriving_flight_work', {
                'id': work.id,
                'arrival_time': work.arrival_time.timestamp(),
                'bags': {bag_id: departure_time.timestamp() 
                        for bag_id, departure_time in work.bags.items()}
            })
            self.produced_messages.inc()

    def run(self):
        self.logger.info("Starting Arriving Flight Work Producer")
        while True:
            try:
                with self.processing_time.time():
                    self.produce_work()
                time.sleep(1)  # Run every second
            except Exception as e:
                self.logger.error(f"Error producing messages: {e}")
                time.sleep(1)

if __name__ == "__main__":
    producer = ArrivingFlightWorkProducer()
    producer.run() 