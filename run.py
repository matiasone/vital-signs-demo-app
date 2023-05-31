from app import create_app, socketio_server, mqtt_client
from flask_cors import CORS, cross_origin

if __name__ == '__main__':
    app = create_app()
    CORS(app, supports_credentials=True)
    mqtt_client.app = app
    socketio_server.run(app)