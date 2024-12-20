import pytest
import numpy as np
import base64
import io
import soundfile as sf

from src.backend.core.ai.voice_modulator import VoiceModulator
from src.backend.core.audio.processor import AudioProcessor

@pytest.fixture
def voice_modulator():
    """Fixture to create a VoiceModulator instance."""
    return VoiceModulator()

@pytest.fixture
def sample_audio():
    """Create a sample audio numpy array."""
    # Generate a simple sine wave
    sr = 22050
    duration = 3  # seconds
    freq = 440  # A4 note
    t = np.linspace(0, duration, num=sr*duration, endpoint=False)
    audio = 0.5 * np.sin(2 * np.pi * freq * t)
    return audio

def test_voice_modulator_initialization(voice_modulator):
    """Test VoiceModulator initialization."""
    assert voice_modulator is not None
    assert len(voice_modulator.EFFECT_TYPES) > 0

def test_pitch_shift(voice_modulator, sample_audio):
    """Test pitch shifting functionality."""
    # Shift pitch up by 2 semitones
    shifted_audio = voice_modulator.pitch_shift(sample_audio, semitones=2.0)
    
    assert shifted_audio is not None
    assert shifted_audio.shape == sample_audio.shape
    assert not np.array_equal(shifted_audio, sample_audio)

def test_gender_morph(voice_modulator, sample_audio):
    """Test gender morphing functionality."""
    # Morph to feminine voice
    feminine_audio = voice_modulator.gender_morph(sample_audio, target_gender='feminine')
    
    assert feminine_audio is not None
    assert feminine_audio.shape == sample_audio.shape
    assert not np.array_equal(feminine_audio, sample_audio)

def test_apply_effect(voice_modulator, sample_audio):
    """Test applying various voice effects."""
    effects = voice_modulator.EFFECT_TYPES.keys()
    
    for effect in effects:
        modulated_audio = voice_modulator.apply_effect(sample_audio, effect, intensity=0.5)
        
        assert modulated_audio is not None
        assert modulated_audio.shape == sample_audio.shape

def test_audio_processor_base64_conversion(sample_audio):
    """Test audio to base64 and back conversion."""
    sr = 22050
    
    # Convert to base64
    base64_audio = AudioProcessor.audio_to_base64(sample_audio, sr)
    
    # Convert back to numpy array
    decoded_audio, decoded_sr = AudioProcessor.base64_to_audio(base64_audio)
    
    assert decoded_sr == sr
    assert np.allclose(decoded_audio, sample_audio, atol=1e-5)

def test_audio_normalization(sample_audio):
    """Test audio normalization."""
    target_level = -20.0
    normalized_audio = AudioProcessor.normalize_audio(sample_audio, target_level)
    
    rms = np.sqrt(np.mean(normalized_audio**2))
    current_level = 20 * np.log10(rms)
    
    assert np.isclose(current_level, target_level, atol=1.0)

def test_audio_feature_extraction(sample_audio):
    """Test audio feature extraction."""
    features = AudioProcessor.extract_features(sample_audio)
    
    assert isinstance(features, dict)
    expected_keys = ['rms', 'zero_crossing_rate', 'spectral_centroid', 
                     'spectral_bandwidth', 'spectral_rolloff']
    
    for key in expected_keys:
        assert key in features
        assert isinstance(features[key], float)
