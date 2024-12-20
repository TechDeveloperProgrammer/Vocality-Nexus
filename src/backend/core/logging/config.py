import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger

def configure_logging(app):
    """
    Configure comprehensive logging for the application.
    Supports console and file logging with JSON formatting.
    """
    # Ensure logs directory exists
    log_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # JSON Formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s %(exc_info)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(logging.INFO)

    # File Handler (Rotating)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, 'vocality_nexus.log'),
        maxBytes=10_000_000,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler]
    )

    # Configure specific loggers
    loggers = [
        'werkzeug',
        'sqlalchemy',
        'flask_jwt_extended',
        'vocality_nexus'
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return app
