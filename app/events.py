from .extensions import socketio_server
from .mqtt_client import mqtt_client, activateESP32

@socketio_server.on("connect")
def handle_connect():
    print("SocketIO client connected!")

@socketio_server.on("get_esp32_data")
def handle_get_data():
    print(f'sent data request --> ActivateESP32')
    request_data = {
        "topic": activateESP32,
        "msg": 1
    }
    publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
    print(publish_result)