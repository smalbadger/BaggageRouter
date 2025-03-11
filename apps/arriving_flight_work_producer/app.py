from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from common.redis_client import RedisClient
from prometheus_client import Counter, Histogram, Gauge
from prometheus_client.core import CollectorRegistry
import time
from datetime import datetime, timedelta

class ArrivingFlightWorkProducer(BaseApp):
    def __init__(self, prometheus_port: int = 8003):
        super().__init__("arriving_flight_work_producer", prometheus_port)
        self.kafka_client = KafkaClient()
        self.redis_client = RedisClient()
        self.producer = self.kafka_client.get_producer()

    def _setup_metrics(self):
        self.produced_messages = Counter(
            'produced_arriving_flight_work_total',
            'Number of arriving flight work messages produced'
        )
        self.processing_time = Histogram(
            'arriving_flight_work_processing_seconds',
            'Time spent processing arriving flight work'
        )
        self.latest_work_arrival = Gauge(
            'latest_work_arrival_timestamp',
            'Timestamp of the latest work item arrival time'
        )
        self.stored_flights = Gauge(
            'redis_stored_flights_total',
            'Number of flights stored in Redis'
        )
        self.stored_bags = Gauge(
            'redis_stored_bags_total',
            'Number of bags stored in Redis'
        )

    def produce_work(self):
        current_time = datetime.now().timestamp()

        work_items = self.redis_client.get_arriving_flight_work(current_time)
        
        # Update Redis stats
        stats = self.redis_client.get_stats()
        self.stored_flights.set(stats['total_flights'])
        self.stored_bags.set(stats['total_bags'])
        
        for work in work_items:
            arrival_time = work.arrival_time
            self.producer.send('arriving_flight_work', {
                'id': work.id,
                'arrival_time': arrival_time,
                'bags': {bag_id: departure_time 
                        for bag_id, departure_time in work.bags.items()}
            })
            self.produced_messages.inc()
            self.latest_work_arrival.set(arrival_time)

    def run(self):
        self.logger.info("Starting Arriving Flight Work Producer")
        while True:
            try:
                with self.processing_time.time():
                    self.produce_work()
            except Exception as e:
                self.logger.exception(f"Error producing messages.")
                
            time.sleep(1)

if __name__ == "__main__":
    producer = ArrivingFlightWorkProducer()
    producer.run() 