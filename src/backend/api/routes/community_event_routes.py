from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from ..controllers.community_event_controller import CommunityEventController
from ...core.database.session import SessionLocal
from ...core.logging.config import get_logger

community_event_bp = Blueprint('community_events', __name__, url_prefix='/api/events')
event_controller = CommunityEventController()
logger = get_logger(__name__)

@community_event_bp.route('/', methods=['GET', 'POST'])
@jwt_required()
def manage_events():
    """
    Comprehensive endpoint for creating and retrieving community events.
    Supports filtering, pagination, and event creation.
    """
    current_user_uuid = get_jwt_identity()
    
    if request.method == 'GET':
        try:
            # Collect query parameters for filtering
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            filters = {}
            if request.args.get('event_type'):
                filters['event_type'] = request.args.get('event_type')
            if request.args.get('is_public'):
                filters['is_public'] = request.args.get('is_public', type=bool)
            if request.args.get('start_after'):
                filters['start_after'] = datetime.fromisoformat(request.args.get('start_after'))
            
            with SessionLocal() as session:
                events = event_controller.get_events(
                    session, 
                    page=page, 
                    per_page=per_page, 
                    filters=filters
                )
                
                return jsonify({
                    'status': 'success',
                    'events': [event.to_dict() for event in events],
                    'page': page,
                    'per_page': per_page
                }), 200
        
        except ValueError as ve:
            logger.warning(f"Invalid event filtering parameters: {str(ve)}")
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
        except Exception as e:
            logger.error(f"Error retrieving events: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to retrieve events'
            }), 500
    
    elif request.method == 'POST':
        try:
            event_data = request.get_json()
            
            # Validate required fields
            required_fields = ['title', 'event_type', 'start_time', 'end_time']
            if not all(field in event_data for field in required_fields):
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required event fields'
                }), 400
            
            # Convert timestamps
            start_time = datetime.fromisoformat(event_data['start_time'])
            end_time = datetime.fromisoformat(event_data['end_time'])
            
            with SessionLocal() as session:
                event = event_controller.create_event(
                    session,
                    current_user_uuid,
                    event_data['title'],
                    event_data['event_type'],
                    start_time,
                    end_time,
                    description=event_data.get('description'),
                    location_type=event_data.get('location_type', 'online'),
                    location_details=event_data.get('location_details'),
                    max_participants=event_data.get('max_participants', 50),
                    registration_required=event_data.get('registration_required', False),
                    is_public=event_data.get('is_public', True)
                )
                
                session.commit()
                
                return jsonify({
                    'status': 'success',
                    'event': event.to_dict()
                }), 201
        
        except ValueError as ve:
            logger.warning(f"Invalid event creation: {str(ve)}")
            return jsonify({
                'status': 'error',
                'message': str(ve)
            }), 400
        
        except Exception as e:
            logger.error(f"Unexpected error creating event: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to create event'
            }), 500

@community_event_bp.route('/<event_uuid>', methods=['GET', 'PUT', 'DELETE'])
@jwt_required()
def manage_specific_event(event_uuid):
    """
    Endpoint for retrieving, updating, and deleting a specific event.
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        with SessionLocal() as session:
            if request.method == 'GET':
                event = event_controller.get_event_by_uuid(
                    session, 
                    current_user_uuid, 
                    event_uuid
                )
                return jsonify({
                    'status': 'success',
                    'event': event.to_dict()
                }), 200
            
            elif request.method == 'PUT':
                event_data = request.get_json()
                
                # Handle timestamp conversion if present
                if 'start_time' in event_data:
                    event_data['start_time'] = datetime.fromisoformat(event_data['start_time'])
                if 'end_time' in event_data:
                    event_data['end_time'] = datetime.fromisoformat(event_data['end_time'])
                
                updated_event = event_controller.update_event(
                    session,
                    current_user_uuid,
                    event_uuid,
                    **event_data
                )
                
                session.commit()
                
                return jsonify({
                    'status': 'success',
                    'event': updated_event.to_dict()
                }), 200
            
            elif request.method == 'DELETE':
                event_controller.delete_event(
                    session,
                    current_user_uuid,
                    event_uuid
                )
                
                session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Event deleted successfully'
                }), 200
    
    except NoResultFound:
        logger.warning(f"Event not found: {event_uuid}")
        return jsonify({
            'status': 'error',
            'message': 'Event not found'
        }), 404
    
    except ValueError as ve:
        logger.warning(f"Invalid event operation: {str(ve)}")
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error managing event: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to process event request'
        }), 500

@community_event_bp.route('/<event_uuid>/register', methods=['POST'])
@jwt_required()
def register_for_event(event_uuid):
    """
    Register the current user for a specific event.
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        data = request.get_json() or {}
        
        with SessionLocal() as session:
            registration = event_controller.register_for_event(
                session,
                event_uuid,
                current_user_uuid,
                registration_notes=data.get('registration_notes')
            )
            
            session.commit()
            
            return jsonify({
                'status': 'success',
                'registration': registration.to_dict()
            }), 201
    
    except ValueError as ve:
        logger.warning(f"Event registration error: {str(ve)}")
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error registering for event: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to register for event'
        }), 500

@community_event_bp.route('/<event_uuid>/participants', methods=['GET'])
@jwt_required()
def get_event_participants(event_uuid):
    """
    Retrieve participants for a specific event.
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        with SessionLocal() as session:
            participants = event_controller.get_event_participants(
                session, 
                current_user_uuid,
                event_uuid
            )
            
            return jsonify({
                'status': 'success',
                'participants': participants
            }), 200
    
    except ValueError as ve:
        logger.warning(f"Event participants retrieval error: {str(ve)}")
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
    
    except Exception as e:
        logger.error(f"Unexpected error retrieving event participants: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve event participants'
        }), 500
