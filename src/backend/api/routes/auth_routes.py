from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, 
    jwt_required, 
    get_jwt_identity,
    create_refresh_token
)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from ..controllers.auth_controller import AuthController
from ...core.database.session import SessionLocal

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
auth_controller = AuthController()

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    
    Expected JSON payload:
    {
        "username": "unique_username",
        "email": "user@example.com",
        "password": "secure_password",
        "pronouns": "optional",
        "display_name": "optional"
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        if not all(key in data for key in ['username', 'email', 'password']):
            return jsonify({
                'status': 'error',
                'message': 'Missing required registration fields'
            }), 400
        
        # Create user
        with SessionLocal() as session:
            user = auth_controller.register_user(
                session, 
                data['username'], 
                data['email'], 
                data['password'],
                pronouns=data.get('pronouns'),
                display_name=data.get('display_name')
            )
            
            # Generate tokens
            access_token = create_access_token(identity=user.uuid)
            refresh_token = create_refresh_token(identity=user.uuid)
            
            return jsonify({
                'status': 'success',
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 201
    
    except IntegrityError:
        return jsonify({
            'status': 'error',
            'message': 'Username or email already exists'
        }), 409
    
    except ValueError as ve:
        return jsonify({
            'status': 'error',
            'message': str(ve)
        }), 400

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint.
    
    Expected JSON payload:
    {
        "username": "user_identifier",
        "password": "user_password"
    }
    """
    try:
        data = request.get_json()
        
        with SessionLocal() as session:
            user = auth_controller.authenticate_user(
                session, 
                data['username'], 
                data['password']
            )
            
            # Generate tokens
            access_token = create_access_token(identity=user.uuid)
            refresh_token = create_refresh_token(identity=user.uuid)
            
            return jsonify({
                'status': 'success',
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }), 200
    
    except NoResultFound:
        return jsonify({
            'status': 'error',
            'message': 'Invalid username or password'
        }), 401

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Token refresh endpoint for maintaining user sessions.
    """
    current_user = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user)
    
    return jsonify({
        'status': 'success',
        'access_token': new_access_token
    }), 200

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@jwt_required()
def manage_profile():
    """
    Get or update user profile.
    """
    current_user_uuid = get_jwt_identity()
    
    with SessionLocal() as session:
        if request.method == 'GET':
            # Retrieve user profile
            user = auth_controller.get_user_by_uuid(session, current_user_uuid)
            return jsonify({
                'status': 'success',
                'user': user.to_dict()
            }), 200
        
        elif request.method == 'PUT':
            # Update user profile
            data = request.get_json()
            user = auth_controller.update_user_profile(
                session, 
                current_user_uuid, 
                data
            )
            
            return jsonify({
                'status': 'success',
                'user': user.to_dict()
            }), 200
