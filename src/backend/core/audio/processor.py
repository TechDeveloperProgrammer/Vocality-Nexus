import numpy as np
import soundfile as sf
import librosa
from typing import Tuple, List, Optional
import io
import base64

class AudioProcessor:
    """
    Advanced audio processing utilities for Vocality Nexus.
    Handles audio loading, preprocessing, and conversion.
    """
    
    @staticmethod
    def load_audio(file_path: str, 
                   target_sr: int = 22050, 
                   mono: bool = True) -> np.ndarray:
        """
        Load audio file with optional resampling and channel conversion.
        
        :param file_path: Path to audio file
        :param target_sr: Target sample rate
        :param mono: Convert to mono if True
        :return: Processed audio numpy array
        """
        try:
            audio, sr = librosa.load(file_path, sr=target_sr, mono=mono)
            return audio
        except Exception as e:
            raise ValueError(f"Error loading audio file: {e}")
    
    @staticmethod
    def save_audio(audio: np.ndarray, 
                   file_path: str, 
                   sr: int = 22050) -> None:
        """
        Save audio numpy array to file.
        
        :param audio: Audio numpy array
        :param file_path: Output file path
        :param sr: Sample rate
        """
        try:
            sf.write(file_path, audio, sr)
        except Exception as e:
            raise ValueError(f"Error saving audio file: {e}")
    
    @staticmethod
    def audio_to_base64(audio: np.ndarray, sr: int = 22050) -> str:
        """
        Convert audio numpy array to base64 encoded string.
        
        :param audio: Audio numpy array
        :param sr: Sample rate
        :return: Base64 encoded audio
        """
        byte_io = io.BytesIO()
        sf.write(byte_io, audio, sr, format='wav')
        byte_io.seek(0)
        return base64.b64encode(byte_io.read()).decode('utf-8')
    
    @staticmethod
    def base64_to_audio(base64_string: str) -> Tuple[np.ndarray, int]:
        """
        Convert base64 encoded audio to numpy array.
        
        :param base64_string: Base64 encoded audio
        :return: Tuple of (audio numpy array, sample rate)
        """
        try:
            audio_bytes = base64.b64decode(base64_string)
            byte_io = io.BytesIO(audio_bytes)
            audio, sr = sf.read(byte_io)
            return audio, sr
        except Exception as e:
            raise ValueError(f"Error decoding base64 audio: {e}")
    
    @staticmethod
    def extract_features(audio: np.ndarray) -> dict:
        """
        Extract audio features for analysis.
        
        :param audio: Input audio numpy array
        :return: Dictionary of audio features
        """
        return {
            'rms': np.sqrt(np.mean(audio**2)),  # Root Mean Square
            'zero_crossing_rate': np.mean(librosa.zero_crossings(audio)),
            'spectral_centroid': np.mean(librosa.feature.spectral_centroid(y=audio)[0]),
            'spectral_bandwidth': np.mean(librosa.feature.spectral_bandwidth(y=audio)[0]),
            'spectral_rolloff': np.mean(librosa.feature.spectral_rolloff(y=audio)[0])
        }
    
    @staticmethod
    def normalize_audio(audio: np.ndarray, 
                        target_level: float = -20.0) -> np.ndarray:
        """
        Normalize audio to target decibel level.
        
        :param audio: Input audio numpy array
        :param target_level: Target RMS level in decibels
        :return: Normalized audio
        """
        rms = np.sqrt(np.mean(audio**2))
        current_level = 20 * np.log10(rms)
        gain = 10 ** ((target_level - current_level) / 20)
        return audio * gain
