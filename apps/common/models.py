from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Flight:
    id: str
    departure_time: datetime
    arrival_time: datetime
    bags: List[str]

@dataclass
class Bag:
    id: str
    flights: List[str]

@dataclass
class ArrivingFlightWork:
    id: str
    arrival_time: datetime
    bags: Dict[str, datetime]  # bag_id -> next_flight_departure_time 