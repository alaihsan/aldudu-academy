import os
from urllib.parse import urlparse
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Parse port from APP_URL env var, fallback to 5055
    app_url = os.environ.get('APP_URL', 'http://localhost:5055')
    try:
        port = urlparse(app_url).port or 5055
    except Exception:
        port = 5055
    app.run(debug=True, port=port)
