import pytest
import torch
import numpy as np
from src.backend.core.ai.voice_transformer import AdvancedVoiceTransformer, load_audio, save_audio
import tempfile
import os

@pytest.fixture
def voice_transformer():
    """
    Fixture to create a AdvancedVoiceTransformer instance for testing.
    """
    return AdvancedVoiceTransformer()

def test_voice_transformer_initialization(voice_transformer):
    """
    Test that the voice transformer is initialized correctly.
    """
    assert voice_transformer is not None
    assert hasattr(voice_transformer, 'pitch_model')
    assert hasattr(voice_transformer, 'timbre_model')
    assert hasattr(voice_transformer, 'gender_model')

def test_transform_voice(voice_transformer):
    """
    Test voice transformation with various parameters.
    """
    # Create a dummy audio tensor
    audio_tensor = torch.randn(1, 44100)  # 1-second audio at 44.1 kHz
    
    transformation_params = {
        'pitch_shift': 2,
        'timbre_style': 'warm',
        'gender_transform': 'feminine'
    }
    
    result = voice_transformer.transform_voice(audio_tensor, transformation_params)
    
    assert 'transformed_audio' in result
    assert 'transform_id' in result
    assert 'metadata' in result
    
    # Check that transformed audio is not identical to input
    assert not torch.equal(result['transformed_audio'], audio_tensor)

def test_analyze_voice_characteristics(voice_transformer):
    """
    Test voice characteristics analysis.
    """
    # Create a dummy audio tensor
    audio_tensor = torch.randn(1, 44100)  # 1-second audio at 44.1 kHz
    
    analysis = voice_transformer.analyze_voice_characteristics(audio_tensor)
    
    assert 'pitch' in analysis
    assert 'timbre' in analysis
    assert 'gender_characteristics' in analysis
    
    # Check pitch analysis
    assert 'fundamental_frequency' in analysis['pitch']
    assert 'pitch_stability' in analysis['pitch']
    assert 'pitch_range' in analysis['pitch']
    
    # Check timbre analysis
    assert 'brightness' in analysis['timbre']
    assert 'harmonicity' in analysis['timbre']
    assert 'spectral_centroid' in analysis['timbre']
    assert 'dominant_harmonics' in analysis['timbre']
    
    # Check gender characteristics
    assert 'masculine_probability' in analysis['gender_characteristics']
    assert 'feminine_probability' in analysis['gender_characteristics']
    assert 'neutral_probability' in analysis['gender_characteristics']

def test_audio_loading_and_saving():
    """
    Test audio loading and saving utilities.
    """
    # Create a dummy audio tensor
    audio_tensor = torch.randn(1, 44100)  # 1-second audio at 44.1 kHz
    
    # Use a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Save audio
        save_audio(audio_tensor, temp_path)
        
        # Load audio
        loaded_audio = load_audio(temp_path)
        
        # Verify loaded audio
        assert isinstance(loaded_audio, torch.Tensor)
        assert loaded_audio.shape == audio_tensor.shape
    
    finally:
        # Clean up temporary file
        os.unlink(temp_path)

def test_edge_cases(voice_transformer):
    """
    Test edge cases and error handling.
    """
    # Test with empty audio tensor
    with pytest.raises(ValueError):
        voice_transformer.transform_voice(
            torch.tensor([]), 
            {'pitch_shift': 0}
        )
    
    # Test with invalid transformation parameters
    with pytest.raises(ValueError):
        voice_transformer.transform_voice(
            torch.randn(1, 44100), 
            {'invalid_param': 'test'}
        )

def test_performance_and_gpu_support(voice_transformer):
    """
    Test performance and GPU support.
    """
    # Check device
    assert hasattr(voice_transformer, 'device')
    
    # Performance test for multiple transformations
    start_time = torch.cuda.Event(enable_timing=True)
    end_time = torch.cuda.Event(enable_timing=True)
    
    start_time.record()
    
    for _ in range(10):
        audio_tensor = torch.randn(1, 44100)
        voice_transformer.transform_voice(
            audio_tensor, 
            {'pitch_shift': 2, 'timbre_style': 'warm'}
        )
    
    end_time.record()
    torch.cuda.synchronize()
    
    # Ensure multiple transformations complete within a reasonable time
    total_time = start_time.elapsed_time(end_time) / 1000  # Convert to seconds
    assert total_time < 5.0  # Should complete in less than 5 seconds
