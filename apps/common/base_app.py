from prometheus_client import start_http_server
import logging
import json
import sys
from datetime import datetime
import uuid

class JsonFormatter(logging.Formatter):
    def format(self, record):
        record_dict = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if record.exc_info:
            record_dict['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(record_dict)

class BaseApp:
    def __init__(self, name: str, prometheus_port: int):
        self.name = name
        self.prometheus_port = prometheus_port
        self.instance_id = str(uuid.uuid4())[:8]  # Use first 8 chars of UUID
        self._setup_logging()
        self._setup_metrics()
        self._setup_metrics_server()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            handlers=[logging.StreamHandler(sys.stdout)],
            format='%(message)s'
        )
        for handler in logging.getLogger().handlers:
            handler.setFormatter(JsonFormatter())
        self.logger = logging.getLogger(self.name)
        self.logger.info("Setting up logging (after handlers)")

    def _setup_metrics_server(self):
        self.logger.info("Setting up metrics")
        start_http_server(self.prometheus_port)
        self.logger.info(f"Started Prometheus metrics server on port {self.prometheus_port}")

    def _setup_metrics(self):
        raise NotImplementedError("Subclasses must implement _setup_metrics()")

    def run(self):
        raise NotImplementedError("Subclasses must implement run()") 