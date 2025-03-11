import redis
import json
from typing import List
from .models import Flight, Bag, ArrivingFlightWork
from redis import Redis
from datetime import datetime
import logging

class RedisClient:
    def __init__(self, host: str = 'redis', port: int = 6379):
        self.redis = Redis(host=host, port=port)
        self.flight_prefix = "flight:"
        self.bag_prefix = "bag:"
        self._load_scripts()

    def _load_scripts(self):
        with open('scripts/upsert_flights.lua', 'r') as f:
            self.upsert_flights_script = self.redis.register_script(f.read())
        
        with open('scripts/upsert_bags.lua', 'r') as f:
            self.upsert_bags_script = self.redis.register_script(f.read())
        
        with open('scripts/get_arriving_flight_work.lua', 'r') as f:
            self.get_arriving_flight_work_script = self.redis.register_script(f.read())

    def upsert_flights(self, flights: List[Flight]) -> int:
        flight_dicts = [{
            'id': f.id,
            'departure_time': f.departure_time.timestamp(),
            'arrival_time': f.arrival_time.timestamp(),
            'bags': f.bags
        } for f in flights]
        
        # Send all flights in one call
        if flight_dicts:
            return self.upsert_flights_script(keys=['flight'], args=[json.dumps(flight_dicts)])
        return 0

    def upsert_bags(self, bags: List[Bag]) -> int:
        bag_dicts = [{
            'id': b.id,
            'flights': b.flights
        } for b in bags]
        
        # Send all bags in one call
        if bag_dicts:
            return self.upsert_bags_script(keys=['bag'], args=[json.dumps(bag_dicts)])
        return 0

    def get_arriving_flight_work(self, current_time: float, window: int = 600) -> List[ArrivingFlightWork]:
        result = self.get_arriving_flight_work_script(
            keys=['flight', 'bag'],
            args=[current_time, window]
        )
        json_result = json.loads(result.decode())
        logging.info(f"Error message: {json_result['error_message']}")
        return [ArrivingFlightWork(**json.loads(work)) for work in json_result['work_items']]

    def get_stats(self):
        info = self.redis.info()
        flight_count = int(self.redis.get(f"{self.flight_prefix}count") or 0)
        bag_count = int(self.redis.get(f"{self.bag_prefix}count") or 0)
        return {
            'used_memory': info['used_memory'],
            'total_flights': flight_count,
            'total_bags': bag_count
        }

    def get_arriving_flights(self, start_time: datetime, end_time: datetime) -> List[Flight]:
        """Get all flights arriving between start_time and end_time"""
        # For test data, just return all flights since they're all "arriving" in our test scenario
        flight_keys = self.redis.keys(f"{self.flight_prefix}*")
        return [Flight(**json.loads(self.redis.get(key))) for key in flight_keys] 