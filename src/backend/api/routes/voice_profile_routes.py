from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm.exc import NoResultFound

from ..controllers.voice_profile_controller import VoiceProfileController
from ..controllers.voice_controller import VoiceController
from ...core.database.session import SessionLocal
from ...core.logging.config import get_logger

voice_profile_bp = Blueprint('voice_profile', __name__, url_prefix='/api/voice-profiles')
voice_profile_controller = VoiceProfileController()
voice_controller = VoiceController()
logger = get_logger(__name__)

@voice_profile_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def manage_voice_profiles():
    """
    Endpoint for creating and retrieving voice profiles.
    Supports GET (list) and POST (create) methods.
    """
    current_user_uuid = get_jwt_identity()
    
    if request.method == 'GET':
        try:
            with SessionLocal() as session:
                profiles = voice_profile_controller.get_user_voice_profiles(
                    session, 
                    current_user_uuid
                )
                
                return jsonify({
                    'status': 'success',
                    'voice_profiles': [profile.to_dict() for profile in profiles]
                }), 200
        
        except Exception as e:
            logger.error(f"Error retrieving voice profiles: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve voice profiles'
            }), 500
    
    elif request.method == 'POST':
        try:
            profile_data = request.get_json()
            
            with SessionLocal() as session:
                new_profile = voice_profile_controller.create_voice_profile(
                    session,
                    current_user_uuid,
                    **profile_data
                )
                
                session.commit()
                
                return jsonify({
                    'status': 'success',
                    'voice_profile': new_profile.to_dict()
                }), 201
        
        except ValueError as ve:
            logger.warning(f"Invalid voice profile creation: {str(ve)}")
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
        except Exception as e:
            logger.error(f"Unexpected error creating voice profile: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to create voice profile'
            }), 500

@voice_profile_bp.route('/<profile_uuid>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def manage_specific_voice_profile(profile_uuid):
    """
    Endpoint for retrieving, updating, and deleting a specific voice profile.
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        with SessionLocal() as session:
            if request.method == 'GET':
                profile = voice_profile_controller.get_voice_profile_by_uuid(
                    session, 
                    current_user_uuid, 
                    profile_uuid
                )
                return jsonify({
                    'status': 'success',
                    'voice_profile': profile.to_dict()
                }), 200
            
            elif request.method == 'PUT':
                profile_data = request.get_json()
                updated_profile = voice_profile_controller.update_voice_profile(
                    session,
                    current_user_uuid,
                    profile_uuid,
                    **profile_data
                )
                
                session.commit()
                
                return jsonify({
                    'status': 'success',
                    'voice_profile': updated_profile.to_dict()
                }), 200
            
            elif request.method == 'DELETE':
                voice_profile_controller.delete_voice_profile(
                    session,
                    current_user_uuid,
                    profile_uuid
                )
                
                session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Voice profile deleted successfully'
                }), 200
    
    except NoResultFound:
        logger.warning(f"Voice profile not found: {profile_uuid}")
        return jsonify({
            'status': 'error',
            'message': 'Voice profile not found'
        }), 404
    
    except ValueError as ve:
        logger.warning(f"Invalid voice profile operation: {str(ve)}")
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error managing voice profile: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process voice profile request'
        }), 500

@voice_profile_bp.route('/community', methods=['GET'])
@jwt_required()
def get_community_voice_profiles():
    """
    Endpoint for retrieving public community voice profiles.
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        with SessionLocal() as session:
            community_profiles = voice_profile_controller.get_community_voice_profiles(
                session, 
                current_user_uuid
            )
            
            return jsonify({
                'status': 'success',
                'community_voice_profiles': [profile.to_dict() for profile in community_profiles]
            }), 200
    
    except Exception as e:
        logger.error(f"Error retrieving community voice profiles: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve community voice profiles'
        }), 500

@voice_profile_bp.route('/transform', methods=['POST'])
def transform_voice():
    """
    Advanced voice transformation endpoint.
    
    Accepts audio file and transformation parameters.
    Returns transformed voice details.
    """
    try:
        # Validate input
        audio_file = request.files.get('audio')
        transformation_params = request.form.get('params', {})
        
        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400
        
        # Save uploaded file temporarily
        temp_input_path = f"/tmp/input_{audio_file.filename}"
        audio_file.save(temp_input_path)
        
        # Transform voice
        result = voice_controller.transform_voice(
            temp_input_path, 
            transformation_params
        )
        
        return jsonify({
            "message": "Voice transformation successful",
            "data": result
        }), 200
    
    except Exception as e:
        logger.error(f"Voice transformation error: {e}")
        return jsonify({"error": str(e)}), 500

@voice_profile_bp.route('/analyze', methods=['POST'])
def analyze_voice_characteristics():
    """
    Advanced voice characteristics analysis endpoint.
    
    Accepts audio file and returns comprehensive analysis.
    """
    try:
        # Validate input
        audio_file = request.files.get('audio')
        
        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400
        
        # Save uploaded file temporarily
        temp_input_path = f"/tmp/input_{audio_file.filename}"
        audio_file.save(temp_input_path)
        
        # Analyze voice characteristics
        analysis = voice_controller.analyze_voice_characteristics(temp_input_path)
        
        return jsonify({
            "message": "Voice analysis successful",
            "data": analysis
        }), 200
    
    except Exception as e:
        logger.error(f"Voice analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@voice_profile_bp.route('/recommend', methods=['GET'])
def recommend_voice_profiles():
    """
    Recommend voice profiles based on user characteristics.
    """
    try:
        user_uuid = request.args.get('user_uuid')
        max_recommendations = int(request.args.get('max_recommendations', 10))
        
        if not user_uuid:
            return jsonify({"error": "User UUID is required"}), 400
        
        # Get recommendations
        recommendations = voice_controller.recommend_voice_profiles(
            user_uuid, 
            max_recommendations
        )
        
        return jsonify({
            "message": "Voice profile recommendations retrieved",
            "data": recommendations
        }), 200
    
    except Exception as e:
        logger.error(f"Voice profile recommendation error: {e}")
        return jsonify({"error": str(e)}), 500

@voice_profile_bp.route('/performance', methods=['GET'])
def get_performance_report():
    """
    Generate performance report for voice services.
    """
    try:
        duration_hours = int(request.args.get('duration_hours', 1))
        
        # Generate performance report
        report = voice_controller.generate_performance_report(duration_hours)
        
        return jsonify({
            "message": "Performance report generated",
            "data": report
        }), 200
    
    except Exception as e:
        logger.error(f"Performance report generation error: {e}")
        return jsonify({"error": str(e)}), 500
