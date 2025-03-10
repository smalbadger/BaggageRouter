from prometheus_client import start_http_server
from prometheus_client.core import REGISTRY
import logging
import json
import sys
from datetime import datetime

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
        self._registry = None
        self._setup_logging()
        self._setup_metrics()

    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            handlers=[logging.StreamHandler(sys.stdout)],
            format='%(message)s'
        )
        for handler in logging.getLogger().handlers:
            handler.setFormatter(JsonFormatter())
        self.logger = logging.getLogger(self.name)

    def _setup_metrics(self):
        start_http_server(self.prometheus_port, registry=self._registry or REGISTRY)
        self.logger.info(f"Started Prometheus metrics server on port {self.prometheus_port}")

    def run(self):
        raise NotImplementedError("Subclasses must implement run()") 