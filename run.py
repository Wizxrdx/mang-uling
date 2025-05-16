import os
from app import create_app
# from machine.main_button import Machine

# os.system('sudo ntpdate time.google.com')
app = create_app()

if __name__ == "__main__":
    # Machine()
    app.run(debug=False, host='0.0.0.0', port=5000)
