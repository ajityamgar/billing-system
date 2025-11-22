Render Deployment Notes (auto-generated)

What's included/changed:
- Created/updated requirements.txt with detected packages.
- Added Procfile to start gunicorn: 'web: gunicorn wsgi:app'
- Added wsgi.py that imports Flask app from detected module 'app' if applicable.
- If your Flask app variable is named something else than 'app', edit wsgi.py accordingly.

How to deploy on Render:
1. Create a new Web Service on Render.
2. Connect your GitHub repo (or drag & drop your zip).
3. Set Environment: Python 3 (auto-detected), Build Command: (leave default), Start Command: use the Procfile or set 'gunicorn wsgi:app'.
4. Ensure PORT environment variable is allowed (Render sets $PORT).
5. If using a database, add environment variables via Render dashboard.

If anything failed during automatic detection, open wsgi.py and Procfile and correct the module name.

