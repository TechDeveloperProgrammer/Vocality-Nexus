import pytest
import time
from datetime import timedelta
import torch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.backend.core.monitoring.performance_tracker import PerformanceTracker
from src.backend.api.models.user_model import User

@pytest.fixture(scope='module')
def test_engine():
    """
    Create a test database engine.
    """
    return create_engine('sqlite:///:memory:')

@pytest.fixture(scope='module')
def TestSession(test_engine):
    """
    Create a test session factory.
    """
    # Create tables
    User.metadata.create_all(test_engine)
    
    # Create session
    return sessionmaker(bind=test_engine)

@pytest.fixture
def session(TestSession):
    """
    Create a new session for each test.
    """
    session = TestSession()
    yield session
    session.close()

@pytest.fixture
def performance_tracker(session):
    """
    Create a performance tracker for testing.
    """
    return PerformanceTracker(session)

def test_performance_tracker_initialization(performance_tracker):
    """
    Test that the performance tracker is initialized correctly.
    """
    assert performance_tracker is not None
    assert hasattr(performance_tracker, 'session')
    assert hasattr(performance_tracker, 'start_time')
    assert hasattr(performance_tracker, 'performance_metrics')

def test_track_system_resources(performance_tracker):
    """
    Test system resource tracking.
    """
    resources = performance_tracker.track_system_resources()
    
    assert 'timestamp' in resources
    assert 'cpu_usage' in resources
    assert 'memory' in resources
    
    # Optional: Check GPU metrics if available
    if torch.cuda.is_available():
        assert 'gpu_metrics' in resources

def test_track_ai_model_performance(performance_tracker):
    """
    Test tracking AI model performance.
    """
    # Simulate an AI model inference
    start_time = time.time()
    input_tensor = torch.randn(1, 100)  # Dummy input
    output_tensor = input_tensor * 2  # Dummy processing
    inference_time = time.time() - start_time
    
    performance_tracker.track_ai_model_performance(
        model_name='test_model',
        inference_time=inference_time,
        input_size=input_tensor.numel(),
        output_size=output_tensor.numel()
    )
    
    # Check that the performance metric was recorded
    ai_inferences = performance_tracker.performance_metrics['ai_inference_times']
    assert len(ai_inferences) > 0
    
    last_inference = ai_inferences[-1]
    assert last_inference['model_name'] == 'test_model'
    assert 'timestamp' in last_inference

def test_generate_performance_report(performance_tracker):
    """
    Test generating a performance report.
    """
    # Track some metrics first
    performance_tracker.track_ai_model_performance(
        model_name='test_model_1',
        inference_time=0.1,
        input_size=1000,
        output_size=1000
    )
    performance_tracker.track_ai_model_performance(
        model_name='test_model_2',
        inference_time=0.2,
        input_size=2000,
        output_size=2000
    )
    
    # Generate report
    report = performance_tracker.generate_performance_report(
        duration=timedelta(hours=1)
    )
    
    assert 'timestamp' in report
    assert 'uptime' in report
    assert 'system_resources' in report
    assert 'ai_performance' in report
    assert 'performance_bottlenecks' in report

def test_detect_performance_bottlenecks(performance_tracker):
    """
    Test performance bottleneck detection.
    """
    # Simulate performance tracking
    performance_tracker.track_ai_model_performance(
        model_name='slow_model',
        inference_time=1.0,  # Deliberately slow
        input_size=5000,
        output_size=5000
    )
    
    # Generate report and check bottlenecks
    report = performance_tracker.generate_performance_report(
        duration=timedelta(hours=1)
    )
    
    bottlenecks = report.get('performance_bottlenecks', [])
    
    # Check that bottlenecks are detected and have expected structure
    assert isinstance(bottlenecks, list)
    for bottleneck in bottlenecks:
        assert 'type' in bottleneck
        assert 'severity' in bottleneck
        assert 'description' in bottleneck

def test_multiple_performance_tracking(performance_tracker):
    """
    Test tracking multiple performance metrics.
    """
    # Track multiple AI model performances
    models = [
        ('model_1', 0.05, 1000, 1000),
        ('model_2', 0.1, 2000, 2000),
        ('model_3', 0.2, 3000, 3000)
    ]
    
    for model_name, inference_time, input_size, output_size in models:
        performance_tracker.track_ai_model_performance(
            model_name=model_name,
            inference_time=inference_time,
            input_size=input_size,
            output_size=output_size
        )
    
    # Generate report
    report = performance_tracker.generate_performance_report(
        duration=timedelta(hours=1)
    )
    
    # Verify AI performance metrics
    ai_performance = report.get('ai_performance', {})
    assert 'total_inferences' in ai_performance
    assert 'average_inference_time' in ai_performance
    assert 'model_performance' in ai_performance
