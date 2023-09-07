from app import create_app, socketio_server, mqtt_client
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_cors import CORS, cross_origin

if __name__ == '__main__':
    app = create_app()
    CORS(app, supports_credentials=True)
    db = SQLAlchemy(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    mqtt_client.app = app
    socketio_server.run(app)