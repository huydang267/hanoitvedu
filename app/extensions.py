"""Extension singletons, instantiated bare so the app factory owns their lifecycle."""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
