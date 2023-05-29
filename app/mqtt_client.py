from flask_mqtt import Mqtt
from .extensions import socketio_server

mqtt_client = Mqtt()

activateESP32 = "/flask/mqtt/ActivarESP32"
receiveDataTopic = "/Max30102FromESP32"
sendDataTopic = '/flask/mqtt/PatientDataFromFlaskApp'
sendHRSpO2DataTopic = "/flask/mqtt/Max30102(1)"
sendEWSDataTopic = "/flask/mqtt/EWS"
sendOxyDemandDataTopic = "flask/mqtt/OxygenDemand"
sendHealthStatusDataTopic = "flask/mqtt/HealthStatus"
sendHealthAdvisorDataTopic = "flask/mqtt/HealthAdvisor"

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully to mqtt broker')
       mqtt_client.subscribe(receiveDataTopic) # subscribe topic
       print(f'Subscribed to {receiveDataTopic}')
       mqtt_client.subscribe(activateESP32) # subscribe topic
       print(f'Subscribed to {activateESP32}')
       mqtt_client.subscribe("xd")
   else:
       print('Bad connection. Code:', rc)

@mqtt_client.on_publish()
def handle_mqtt_publish(client, userdata, mid):
   print('Published message with mid {}.'
          .format(mid))

@mqtt_client.on_message()
def handle_mqtt_message(client, userdata, message):
    data = dict(
       topic=message.topic,
       payload=message.payload.decode()
        )
    print('Received message on topic: {topic} with payload: {payload}'.format(**data))
    if data["topic"] == receiveDataTopic:
        print("¡¡¡TENEMOS QUE PASARLE ESTA INFORMACIÓN IMPORTANTE AL USUARIO!!!")
        print(data["payload"])
        socketio_server.emit("mqtt_message", data=data)
        print("mensaje mqtt enviado por socketIO")
    elif data["topic"] == activateESP32:
        print("Usuario activó ESP32")
        print(data["payload"])
        socketio_server.emit("mqtt_message", data=data)
        print("mensaje mqtt enviado por socketIO")
    elif data["topic"] == "xd":
        print("Le metimos xd")
        socketio_server.emit("xd")


@mqtt_client.on_log()
def handle_mqtt_log(client, userdata, level, buf):
    if buf == "Received PINGRESP" or buf == "Sending PINGREQ":
        pass
    else:
        print("mqtt log:", client, userdata, level, buf)