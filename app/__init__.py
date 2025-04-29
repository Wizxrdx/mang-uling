import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def database_exists(app):
    db_path = app.instance_path + "/" + app.config.get("SQLALCHEMY_DATABASE_URI").replace("sqlite:///", "")
    return os.path.exists(db_path)

def create_app():
    # Create the Flask app
    app = Flask(__name__)
    
    # Load configurations
    from .config import Config
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Initialize the database
    from .data import initialize_data
    from .populate_data import populate_bag_types, populate_credentials, populate_with_real_data, populate_with_fake_data
    with app.app_context():
        if not database_exists(app):
            print("Database not found. Running flask db upgrade...")
            upgrade()
            print("Database upgrade completed!")
            populate_bag_types(db)
            populate_credentials(db)
            populate_with_real_data(db)
            # populate_with_fake_data(db)

        else:
            print("Database already exists. Skipping upgrade.")
            
        initialize_data()

    # Register blueprints (optional, for modular apps)
    from .routes import main
    app.register_blueprint(main)

    return app
