FROM python:3.9-slim

WORKDIR /app

COPY apps/common /app/common
COPY apps/bag_consumer /app/bag_consumer

RUN pip install kafka-python redis prometheus_client

CMD ["python", "-m", "bag_consumer.app"] 