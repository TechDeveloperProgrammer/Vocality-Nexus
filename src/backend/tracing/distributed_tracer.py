import os
import time
import uuid
import json
import logging
from typing import Dict, Any, Optional, Callable
import asyncio
import contextvars
import opentelemetry
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

class AdvancedDistributedTracer:
    """
    Comprehensive distributed tracing system
    Supports multiple instrumentation strategies and exporters
    """
    
    def __init__(self, 
                 service_name: str = 'vocality_nexus',
                 jaeger_host: str = 'localhost',
                 jaeger_port: int = 6831,
                 log_dir: Optional[str] = None):
        """
        Initialize distributed tracer
        
        :param service_name: Name of the service
        :param jaeger_host: Jaeger collector host
        :param jaeger_port: Jaeger collector port
        :param log_dir: Optional directory for local trace logs
        """
        # Logging configuration
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Trace context
        self.trace_context = contextvars.ContextVar('trace_context', default={})
        
        # Log directory
        self.log_dir = log_dir or os.path.join(os.path.dirname(__file__), 'traces')
        os.makedirs(self.log_dir, exist_ok=True)
        
        # OpenTelemetry tracer setup
        resource = Resource(attributes={
            SERVICE_NAME: service_name
        })
        
        trace_provider = TracerProvider(resource=resource)
        
        # Jaeger exporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=jaeger_host,
            agent_port=jaeger_port
        )
        
        # Span processor
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(trace_provider)
        
        # Create tracer
        self.tracer = trace.get_tracer(__name__)

    def instrument_flask(self, app):
        """
        Instrument Flask application
        
        :param app: Flask application
        """
        FlaskInstrumentor().instrument_app(app)

    def instrument_sqlalchemy(self, engine):
        """
        Instrument SQLAlchemy engine
        
        :param engine: SQLAlchemy engine
        """
        SQLAlchemyInstrumentor().instrument(engine=engine)

    def instrument_redis(self, redis_client):
        """
        Instrument Redis client
        
        :param redis_client: Redis client
        """
        RedisInstrumentor().instrument(redis_client=redis_client)

    def instrument_psycopg2(self):
        """
        Instrument Psycopg2 PostgreSQL driver
        """
        Psycopg2Instrumentor().instrument()

    def start_trace(self, 
                    name: str, 
                    trace_id: Optional[str] = None, 
                    parent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a new distributed trace
        
        :param name: Name of the trace
        :param trace_id: Optional custom trace ID
        :param parent_id: Optional parent span ID
        :return: Trace context
        """
        trace_id = trace_id or str(uuid.uuid4())
        
        # Start span
        span = self.tracer.start_span(name)
        
        # Create trace context
        context = {
            'trace_id': trace_id,
            'span_id': span.get_span_context().span_id,
            'parent_id': parent_id,
            'start_time': time.time(),
            'name': name
        }
        
        # Set context
        self.trace_context.set(context)
        
        return context

    def end_trace(self, status: str = 'success'):
        """
        End current trace
        
        :param status: Trace completion status
        """
        context = self.trace_context.get()
        
        if context:
            # End span
            span = self.tracer.start_span(context['name'])
            span.set_attribute('status', status)
            span.end()
            
            # Log trace details
            self._log_trace(context)

    def add_trace_attribute(self, key: str, value: Any):
        """
        Add attribute to current trace
        
        :param key: Attribute key
        :param value: Attribute value
        """
        context = self.trace_context.get()
        
        if context:
            span = self.tracer.start_span(context['name'])
            span.set_attribute(key, str(value))

    def _log_trace(self, context: Dict[str, Any]):
        """
        Log trace details to file
        
        :param context: Trace context
        """
        try:
            log_file = os.path.join(
                self.log_dir, 
                f"trace_{context['trace_id']}.json"
            )
            
            with open(log_file, 'w') as f:
                json.dump({
                    **context,
                    'end_time': time.time(),
                    'duration': time.time() - context['start_time']
                }, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Trace logging error: {e}")

    def trace_function(self, 
                       func: Optional[Callable] = None, 
                       name: Optional[str] = None):
        """
        Decorator to trace function execution
        
        :param func: Function to trace
        :param name: Optional custom trace name
        :return: Traced function
        """
        def decorator(f):
            def wrapper(*args, **kwargs):
                trace_name = name or f.__name__
                
                with self.tracer.start_as_current_span(trace_name):
                    try:
                        result = f(*args, **kwargs)
                        self.add_trace_attribute('status', 'success')
                        return result
                    except Exception as e:
                        self.add_trace_attribute('status', 'error')
                        self.add_trace_attribute('error_message', str(e))
                        raise
            return wrapper
        
        return decorator(func) if func else decorator

    async def trace_async_function(self, 
                                   func: Optional[Callable] = None, 
                                   name: Optional[str] = None):
        """
        Decorator to trace async function execution
        
        :param func: Async function to trace
        :param name: Optional custom trace name
        :return: Traced async function
        """
        def decorator(f):
            async def wrapper(*args, **kwargs):
                trace_name = name or f.__name__
                
                async with self.tracer.start_as_current_span(trace_name):
                    try:
                        result = await f(*args, **kwargs)
                        self.add_trace_attribute('status', 'success')
                        return result
                    except Exception as e:
                        self.add_trace_attribute('status', 'error')
                        self.add_trace_attribute('error_message', str(e))
                        raise
            return wrapper
        
        return decorator(func) if func else decorator

def create_distributed_tracer(
    service_name: str = 'vocality_nexus',
    jaeger_host: str = 'localhost',
    jaeger_port: int = 6831,
    log_dir: Optional[str] = None
) -> AdvancedDistributedTracer:
    """
    Factory method to create distributed tracer
    
    :param service_name: Name of the service
    :param jaeger_host: Jaeger collector host
    :param jaeger_port: Jaeger collector port
    :param log_dir: Optional directory for local trace logs
    :return: Configured distributed tracer
    """
    return AdvancedDistributedTracer(
        service_name, 
        jaeger_host, 
        jaeger_port, 
        log_dir
    )
