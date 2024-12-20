import logging
from typing import Dict, Any, List
from ...core.ai.voice_modulator import VoiceModulator
from ...core.audio.processor import AudioProcessor
from ...core.ai.voice_transformer import AdvancedVoiceTransformer, load_audio, save_audio
from ...core.analytics.recommendation_engine import RecommendationEngine
from ...core.monitoring.performance_tracker import PerformanceTracker
from ..models.voice_profile_model import VoiceProfile
from ..database import SessionLocal
import time
from datetime import timedelta

class VoiceController:
    """
    Controller for managing voice modulation operations.
    Handles business logic and coordinates between routes and core modules.
    """
    
    def __init__(self):
        """
        Initialize voice controller with modulator, processor, and AI services.
        """
        self.session = SessionLocal()
        self.modulator = VoiceModulator()
        self.processor = AudioProcessor
        self.voice_transformer = AdvancedVoiceTransformer()
        self.recommendation_engine = RecommendationEngine(self.session)
        self.performance_tracker = PerformanceTracker(self.session)
    
    def process_voice_request(self, 
                               audio_data: bytes, 
                               effect_type: str, 
                               intensity: float = 0.5) -> Dict[str, Any]:
        """
        Process a voice modulation request.
        
        :param audio_data: Base64 encoded audio data
        :param effect_type: Type of voice effect to apply
        :param intensity: Intensity of the effect
        :return: Dictionary with modulation results
        """
        try:
            # Convert base64 to numpy array
            audio_array, sr = self.processor.base64_to_audio(audio_data)
            
            # Apply voice effect
            modulated_audio = self.modulator.apply_effect(
                audio_array, 
                effect_type, 
                intensity
            )
            
            # Normalize audio
            normalized_audio = self.processor.normalize_audio(modulated_audio)
            
            # Extract features
            features = self.processor.extract_features(normalized_audio)
            
            # Convert back to base64
            base64_audio = self.processor.audio_to_base64(normalized_audio, sr)
            
            return {
                'status': 'success',
                'modulated_audio': base64_audio,
                'audio_features': features
            }
        
        except Exception as e:
            logging.error(f"Voice processing error: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_available_effects(self) -> Dict[str, str]:
        """
        Retrieve available voice effects.
        
        :return: Dictionary of available effects
        """
        return self.modulator.get_available_effects()
    
    def transform_voice(
        self, 
        audio_file_path: str, 
        transformation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transform voice using advanced AI techniques.
        
        :param audio_file_path: Path to input audio file
        :param transformation_params: Voice transformation configuration
        :return: Transformed voice details
        """
        start_time = time.time()
        
        try:
            # Load audio tensor
            audio_tensor = load_audio(audio_file_path)
            
            # Apply voice transformation
            result = self.voice_transformer.transform_voice(
                audio_tensor, 
                transformation_params
            )
            
            # Save transformed audio
            output_file_path = f"/app/transformed_voices/{result['transform_id']}.wav"
            save_audio(result['transformed_audio'], output_file_path)
            
            # Track AI model performance
            inference_time = time.time() - start_time
            self.performance_tracker.track_ai_model_performance(
                model_name='voice_transformer',
                inference_time=inference_time,
                input_size=audio_tensor.numel(),
                output_size=result['transformed_audio'].numel()
            )
            
            return {
                'transform_id': result['transform_id'],
                'output_file_path': output_file_path,
                'metadata': result['metadata']
            }
        
        except Exception as e:
            # Log error and raise
            raise ValueError(f"Voice transformation failed: {e}")
    
    def analyze_voice_characteristics(
        self, 
        audio_file_path: str
    ) -> Dict[str, Any]:
        """
        Analyze detailed voice characteristics.
        
        :param audio_file_path: Path to audio file
        :return: Comprehensive voice analysis
        """
        start_time = time.time()
        
        try:
            # Load audio tensor
            audio_tensor = load_audio(audio_file_path)
            
            # Analyze voice characteristics
            analysis = self.voice_transformer.analyze_voice_characteristics(audio_tensor)
            
            # Track AI model performance
            inference_time = time.time() - start_time
            self.performance_tracker.track_ai_model_performance(
                model_name='voice_analyzer',
                inference_time=inference_time,
                input_size=audio_tensor.numel(),
                output_size=len(str(analysis))
            )
            
            return analysis
        
        except Exception as e:
            raise ValueError(f"Voice analysis failed: {e}")
    
    def recommend_voice_profiles(
        self, 
        user_uuid: str, 
        max_recommendations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend voice profiles based on user characteristics.
        
        :param user_uuid: UUID of the user
        :param max_recommendations: Maximum number of recommendations
        :return: List of recommended voice profiles
        """
        try:
            return self.recommendation_engine.recommend_voice_profiles(
                user_uuid, 
                max_recommendations
            )
        
        except Exception as e:
            raise ValueError(f"Voice profile recommendations failed: {e}")
    
    def generate_performance_report(
        self, 
        duration_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        
        :param duration_hours: Duration for performance analysis
        :return: Performance report
        """
        try:
            return self.performance_tracker.generate_performance_report(
                duration=timedelta(hours=duration_hours)
            )
        
        except Exception as e:
            raise ValueError(f"Performance report generation failed: {e}")
    
    def __del__(self):
        """
        Cleanup resources when controller is destroyed.
        """
        if hasattr(self, 'session'):
            self.session.close()
