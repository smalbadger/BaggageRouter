from common.base_app import BaseApp
from common.kafka_client import KafkaClient
from datetime import datetime, timedelta
import random
import uuid
import time
from kafka.admin import KafkaAdminClient, NewTopic
from prometheus_client import Counter, Gauge

class TestProducers(BaseApp):
    def __init__(self, prometheus_port: int = 8004):
        super().__init__("test_producers", prometheus_port)
        self.kafka_client = KafkaClient()
        self.producer = self.kafka_client.get_producer()
        self._init_topics()
        self.start_date = datetime.now() - timedelta(days=30)  # 30 days ago
        self.current_date = self.start_date

    def _init_topics(self):
        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.kafka_client.bootstrap_servers
            )
            
            topic_names = ["flights", "bags", "arriving_flight_work"]
            
            # Delete topics if they exist
            existing_topics = admin_client.list_topics()
            
            # Create topics that don't exist
            topics_to_create = [
                NewTopic(name=name, num_partitions=1, replication_factor=1)
                for name in topic_names if name not in existing_topics
            ]
            
            if topics_to_create:
                self.logger.info(f"Creating topics: {[t.name for t in topics_to_create]}")
                admin_client.create_topics(topics_to_create)
            else:
                self.logger.info("All required topics already exist")
            
            admin_client.close()
        except Exception as e:
            self.logger.error(f"Error managing topics: {e}")
            # Continue even if topic creation fails - they might already exist

    def _setup_metrics(self):
        self.produced_flights = Counter(
            'produced_test_flights_total',
            'Number of test flight messages produced'
        )
        self.produced_bags = Counter(
            'produced_test_bags_total',
            'Number of test bag messages produced'
        )
        self.latest_flight_arrival = Gauge(
            'latest_produced_flight_arrival_timestamp',
            'Timestamp of the latest produced flight arrival time'
        )

    def generate_id(self, prefix: str) -> str:
        return f"{prefix}_{str(uuid.uuid4())}"

    def generate_flights_for_hour(self):
        flights = []
        for _ in range(1000):  # Generate 100,000 flights per day
            flight_id = self.generate_id("FL")
            arrival_time = self.current_date + timedelta(minutes=random.randint(0, 60))
            departure_time = arrival_time - timedelta(minutes=random.randint(30, 240))
            
            flights.append({
                'id': flight_id,
                'departure_time': departure_time.timestamp(),
                'arrival_time': arrival_time.timestamp(),
                'bags': []
            })
        return flights

    def generate_bags_for_hour(self, flights):
        bags = []
        flight_bag_mapping = {flight['id']: [] for flight in flights}
        
        for _ in range(300000):  # Generate 30,000,000 unique bags per day
            bag_id = self.generate_id("BAG")
            num_flights = random.randint(1, 3)
            
            # Select random flights for this bag
            selected_flights = sorted(
                random.sample(flights, min(num_flights, len(flights))),
                key=lambda x: x['departure_time']
            )
            selected_flight_ids = [f['id'] for f in selected_flights]
            
            bags.append({
                'id': bag_id,
                'flights': selected_flight_ids
            })
            
            # Update flight-bag mapping
            for flight_id in selected_flight_ids:
                flight_bag_mapping[flight_id].append(bag_id)
        
        return bags, flight_bag_mapping

    def publish_hour_data(self, flights, bags, flight_bag_mapping):
        # First publish all bags
        for bag in bags:
            self.producer.send('bags', bag)
        self.produced_bags.inc(len(bags))

        # Then publish flights in descending arrival time order
        for flight in sorted(flights, key=lambda x: x['arrival_time'], reverse=True):
            flight['bags'] = flight_bag_mapping[flight['id']]
            self.producer.send('flights', flight)
            self.latest_flight_arrival.set(flight['arrival_time'])
        self.produced_flights.inc(len(flights))

    def run(self):
        self.logger.info("Starting Test Producers")
        
        while self.current_date < datetime.now() + timedelta(days=1):
            try:
                # Generate all flights for the day
                flights = self.generate_flights_for_hour()
                
                # Generate all bags and create mappings
                bags, flight_bag_mapping = self.generate_bags_for_hour(flights)
                
                # Publish all data
                self.publish_hour_data(flights, bags, flight_bag_mapping)
                
                # Move to next day
                self.current_date += timedelta(minutes=60)
                self.logger.info(f"Completed processing for {self.current_date.date()}")
                
            except Exception as e:
                self.logger.error(f"Error producing test messages: {e}")
            
            time.sleep(1)

        while True: # Never kill the program so that metrics are still available
            time.sleep(10)

if __name__ == "__main__":
    producer = TestProducers()
    producer.run()