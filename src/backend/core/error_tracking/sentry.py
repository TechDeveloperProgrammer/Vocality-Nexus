import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration

def initialize_sentry(app):
    """
    Initialize Sentry error tracking and performance monitoring.
    
    :param app: Flask application instance
    :return: Configured Flask application
    """
    sentry_sdk.init(
        dsn=app.config.get('SENTRY_DSN', ''),
        integrations=[
            FlaskIntegration(),
            SqlAlchemyIntegration()
        ],
        traces_sample_rate=0.5,  # Capture 50% of transactions for performance monitoring
        send_default_pii=False,  # Respect user privacy
        environment=app.config.get('ENV', 'development'),
        release=app.config.get('APP_VERSION', 'unknown')
    )

    return app
