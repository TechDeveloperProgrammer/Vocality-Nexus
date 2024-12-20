from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Basic configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'development_secret_key')
    app.config['ENV'] = os.getenv('FLASK_ENV', 'development')
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', app.config['SECRET_KEY'])
    jwt = JWTManager(app)

    # Import and register blueprints
    from .api.routes.voice_routes import voice_bp
    from .api.routes.auth_routes import auth_bp
    from .api.routes.voice_profile_routes import voice_profile_bp
    from .api.routes.social_routes import social_bp
    from .api.routes.community_event_routes import community_event_bp
    
    app.register_blueprint(voice_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(voice_profile_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(community_event_bp)

    # Health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'environment': app.config['ENV']
        }), 200

    # Basic error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        logger.error(f'Not Found: {error}')
        return jsonify({'error': 'Not Found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal Server Error'}), 500

    return app

# Application entry point
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
