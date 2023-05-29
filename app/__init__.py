from flask import Flask
from .events import socketio_server
from .routes import main
from flask_mqtt import Mqtt
from .mqtt_client import mqtt_client

msg = []

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '9a6212f13d2370e87d273e56d418630f6e60ccc1748e1e06'

    app.config['MQTT_BROKER_URL'] = "broker.hivemq.com"
    app.config['MQTT_BROKER_PORT'] = 1883
    app.config["DEBUG"] = True
    app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
    app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
    app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
    app.config['MQTT_TLS_ENABLED'] = False  # If your broker supports TLS, set it True

    app.register_blueprint(main)
    mqtt_client.init_app(app)
    socketio_server.init_app(app)

    
    return app