from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..controllers.social_connection_controller import SocialConnectionController
from ..models.social_connection_model import ConnectionStatus
from ...core.database.session import SessionLocal

social_bp = Blueprint('social', __name__, url_prefix='/api/social')
social_controller = SocialConnectionController()

@social_bp.route('/connect', methods=['POST'])
@jwt_required()
def create_connection():
    """
    Create a new connection request.
    
    Expected JSON payload:
    {
        "recipient_username": "target_username",
        "connection_type": "friend"
    }
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            connection = social_controller.create_connection_request(
                session,
                current_user_uuid,
                data['recipient_username'],
                data.get('connection_type', 'friend')
            )
            
            return jsonify({
                'status': 'success',
                'connection': connection.to_dict()
            }), 201
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400

@social_bp.route('/connections', methods=['GET'])
@jwt_required()
def get_connections():
    """
    Retrieve user's social connections.
    
    Query Parameters:
    - status: Filter by connection status (optional)
    """
    current_user_uuid = get_jwt_identity()
    status = request.args.get('status')
    
    try:
        with SessionLocal() as session:
            # Convert status to enum if provided
            connection_status = (
                ConnectionStatus(status) if status 
                else None
            )
            
            connections = social_controller.get_user_connections(
                session, 
                current_user_uuid, 
                status=connection_status
            )
            
            return jsonify({
                'status': 'success',
                'connections': [conn.to_dict() for conn in connections]
            }), 200
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400

@social_bp.route('/connections/<connection_uuid>', methods=['PUT'])
@jwt_required()
def update_connection_status(connection_uuid):
    """
    Update the status of a social connection.
    
    Expected JSON payload:
    {
        "status": "accepted" / "rejected" / "blocked"
    }
    """
    current_user_uuid = get_jwt_identity()
    
    try:
        data = request.get_json()
        status = ConnectionStatus(data['status'])
        
        with SessionLocal() as session:
            connection = social_controller.update_connection_status(
                session, 
                current_user_uuid, 
                connection_uuid, 
                status
            )
            
            return jsonify({
                'status': 'success',
                'connection': connection.to_dict()
            }), 200
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400

@social_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """
    Search for users by username or display name.
    
    Query Parameters:
    - q: Search query
    """
    current_user_uuid = get_jwt_identity()
    search_query = request.args.get('q', '')
    
    if not search_query:
        return jsonify({
            'status': 'error',
            'message': 'Search query is required'
        }), 400
    
    try:
        with SessionLocal() as session:
            users = social_controller.search_users(
                session, 
                search_query, 
                current_user_uuid
            )
            
            return jsonify({
                'status': 'success',
                'users': users
            }), 200
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400
