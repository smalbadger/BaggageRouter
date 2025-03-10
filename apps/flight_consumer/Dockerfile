FROM python:3.9-slim

WORKDIR /app

COPY apps/common /app/common
COPY apps/flight_consumer /app/flight_consumer

RUN pip install kafka-python redis prometheus_client

CMD ["python", "-m", "flight_consumer.app"] 