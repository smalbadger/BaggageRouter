import redis
import json
from typing import List
from .models import Flight, Bag, ArrivingFlightWork

class RedisClient:
    def __init__(self, host: str = 'redis', port: int = 6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        self._load_scripts()

    def _load_scripts(self):
        with open('/scripts/upsert_flights.lua', 'r') as f:
            self.upsert_flights_script = self.redis.register_script(f.read())
        
        with open('/scripts/upsert_bags.lua', 'r') as f:
            self.upsert_bags_script = self.redis.register_script(f.read())
        
        with open('/scripts/get_arriving_flight_work.lua', 'r') as f:
            self.get_arriving_flight_work_script = self.redis.register_script(f.read())

    def upsert_flights(self, flights: List[Flight]) -> int:
        flight_jsons = [json.dumps({
            'id': f.id,
            'departure_time': f.departure_time.timestamp(),
            'arrival_time': f.arrival_time.timestamp(),
            'bags': f.bags
        }) for f in flights]
        
        return self.upsert_flights_script(keys=['flight'], args=flight_jsons)

    def upsert_bags(self, bags: List[Bag]) -> int:
        bag_jsons = [json.dumps({
            'id': b.id,
            'flights': b.flights
        }) for b in bags]
        
        return self.upsert_bags_script(keys=['bag'], args=bag_jsons)

    def get_arriving_flight_work(self, current_time: float, window: int = 600) -> List[ArrivingFlightWork]:
        result = self.get_arriving_flight_work_script(
            keys=['flight', 'bag'],
            args=[current_time, window]
        )
        return [ArrivingFlightWork(**json.loads(work)) for work in result] 