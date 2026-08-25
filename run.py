"""Development entrypoint: python run.py -> http://127.0.0.1:5000"""

from app import create_app
from config import DevConfig

app = create_app(DevConfig)

if __name__ == "__main__":
    app.run(debug=True)
