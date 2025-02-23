import os
from app import create_app, db
from populate_data import populate_data
from flask_migrate import upgrade

def database_exists():
    db_path = app.instance_path + "/" + app.config.get("SQLALCHEMY_DATABASE_URI").replace("sqlite:///", "")
    return os.path.exists(db_path)

app = create_app()

if __name__ == "__main__":    
    with app.app_context():
        if not database_exists():
            print("Database not found. Running flask db upgrade...")
            upgrade()
            print("Database upgrade completed!")
            populate_data(db)
        else:
            print("Database already exists. Skipping upgrade.")

    app.run(debug=True, host='0.0.0.0', port=5000)
