FROM python:3.9-slim

WORKDIR /app

COPY apps/common common/
COPY apps/arriving_flight_work_producer arriving_flight_work_producer/
COPY docker/redis/scripts scripts/

RUN pip install kafka-python redis prometheus_client

CMD ["python", "-m", "arriving_flight_work_producer.app"] 