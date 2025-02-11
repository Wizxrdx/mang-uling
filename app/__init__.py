from flask import Flask
from .config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    # Create the Flask app
    app = Flask(__name__)
    
    # Load configurations
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints (optional, for modular apps)
    from .routes import main
    app.register_blueprint(main)

    return app
