FROM python:3.9-slim

WORKDIR /app

COPY apps/common /app/common
COPY apps/test_producers /app/test_producers

RUN pip install kafka-python[admin] redis prometheus_client

CMD ["python", "-m", "test_producers.app"] 