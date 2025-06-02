# This file contains the WSGI configuration required to serve up your
# web application at http://<your-username>.pythonanywhere.com/
# It works by setting the variable 'application' to a WSGI handler

import sys
import os

# Add your project directory to the sys.path
path = '/home/YourUsername'
if path not in sys.path:
    sys.path.append(path)

from app import app as application  # noqa
application.secret_key = 'Add your secret key here'

# Import environment variables
os.environ['GOOGLE_API_KEY'] = 'your-api-key-here'
