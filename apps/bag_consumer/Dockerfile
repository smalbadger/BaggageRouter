FROM python:3.9-slim

WORKDIR /app

COPY apps/common common/
COPY apps/bag_consumer bag_consumer/
COPY docker/redis/scripts scripts/

RUN pip install kafka-python redis prometheus_client

CMD ["python", "-m", "bag_consumer.app"] 