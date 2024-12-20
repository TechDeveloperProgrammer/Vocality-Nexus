from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import logging

from ..controllers.voice_controller import VoiceController
from ...core.ai.voice_modulator import VoiceModulator
from ...core.audio.processor import AudioProcessor

voice_bp = Blueprint('voice', __name__, url_prefix='/api/voice')
voice_controller = VoiceController()
voice_modulator = VoiceModulator()

@voice_bp.route('/effects', methods=['GET'])
def get_available_effects():
    """
    Retrieve list of available voice effects.
    
    :return: JSON response with available effects
    """
    try:
        effects = voice_modulator.get_available_effects()
        return jsonify({
            'status': 'success',
            'effects': effects
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving voice effects: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Unable to retrieve voice effects'
        }), 500

@voice_bp.route('/modulate', methods=['POST'])
def modulate_voice():
    """
    Modulate voice with specified effect and parameters.
    
    Expected JSON payload:
    {
        'audio': base64_encoded_audio,
        'effect_type': 'pitch_shift',
        'intensity': 0.5
    }
    
    :return: JSON response with modulated audio
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not all(key in data for key in ['audio', 'effect_type']):
            return jsonify({
                'status': 'error',
                'message': 'Missing required parameters'
            }), 400
        
        # Decode audio
        audio_array, sr = AudioProcessor.base64_to_audio(data['audio'])
        
        # Apply effect
        intensity = data.get('intensity', 0.5)
        modulated_audio = voice_modulator.apply_effect(
            audio_array, 
            data['effect_type'], 
            intensity
        )
        
        # Normalize and convert back to base64
        normalized_audio = AudioProcessor.normalize_audio(modulated_audio)
        base64_audio = AudioProcessor.audio_to_base64(normalized_audio, sr)
        
        return jsonify({
            'status': 'success',
            'modulated_audio': base64_audio,
            'features': AudioProcessor.extract_features(modulated_audio)
        }), 200
    
    except ValueError as ve:
        logging.error(f"Validation error: {ve}")
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    
    except Exception as e:
        logging.error(f"Voice modulation error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during voice modulation'
        }), 500

@voice_bp.route('/upload', methods=['POST'])
def upload_audio():
    """
    Upload audio file for processing.
    
    :return: JSON response with upload status
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No selected file'
            }), 400
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Process uploaded file
        audio = AudioProcessor.load_audio(filepath)
        features = AudioProcessor.extract_features(audio)
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'audio_features': features
        }), 200
    
    except Exception as e:
        logging.error(f"Audio upload error: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error processing uploaded audio'
        }), 500
