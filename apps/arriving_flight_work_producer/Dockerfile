FROM python:3.9-slim

WORKDIR /app

COPY apps/common /app/common
COPY apps/arriving_flight_work_producer /app/arriving_flight_work_producer

RUN pip install kafka-python redis prometheus_client

CMD ["python", "-m", "arriving_flight_work_producer.app"] 