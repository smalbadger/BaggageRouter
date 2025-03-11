FROM python:3.9-slim

WORKDIR /app

COPY apps/common common/
COPY apps/flight_consumer flight_consumer/
COPY docker/redis/scripts scripts/

RUN pip install kafka-python redis prometheus_client

CMD ["python", "-m", "flight_consumer.app"] 