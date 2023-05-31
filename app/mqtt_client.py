from flask_mqtt import Mqtt
from .extensions import socketio_server

mqtt_client = Mqtt()

activateESP32 = "/flask/mqtt/ActivarESP32"
receiveDataTopic = "/Max30102FromESP32"
#sendHRSpO2DataTopic = "/flask/mqtt/Max30102(1)"
#sendEWSDataTopic = "/flask/mqtt/EWS"
#sendOxyDemandDataTopic = "flask/mqtt/OxygenDemand"
#sendHealthStatusDataTopic = "flask/mqtt/HealthStatus"
#sendHealthAdvisorDataTopic = "flask/mqtt/HealthAdvisor"
sendHRSpO2DataTopic = "/Max30102(1)"
sendEWSDataTopic = "/EWS"
sendOxyDemandDataTopic = "/OxygenDemand"
sendHealthStatusDataTopic = "/HealthStatus"
sendHealthAdvisorDataTopic = "/HealthAdvisor"
receiveHRSpO2ResponseStatusTopic = "/Max30102(1)ResponseStatus"
receiveEWSResponseStatusTopic = "/EWSResponseStatus"
receiveOxyDemandResponseStatusTopic = "/OxygenDemandResponseStatus"
receiveHealthStatusResponseStatusTopic = "/HealthStatusResponseStatus"
receiveHealthAdvisorResponseStatusTopic = "/HealthAdvisorResponseStatus"


mqtt_msgs = []

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print('Connected successfully to mqtt broker')
       mqtt_client.subscribe(receiveDataTopic) # subscribe topic
       print(f'Subscribed to {receiveDataTopic}')
       mqtt_client.subscribe(activateESP32) # subscribe topic
       print(f'Subscribed to {activateESP32}')
       mqtt_client.subscribe(sendHRSpO2DataTopic) # subscribe topic
       print(f'Subscribed to {sendHRSpO2DataTopic}')
       mqtt_client.subscribe(sendEWSDataTopic) # subscribe topic
       print(f'Subscribed to {sendEWSDataTopic}')
       mqtt_client.subscribe(sendOxyDemandDataTopic) # subscribe topic
       print(f'Subscribed to {sendOxyDemandDataTopic}')
       mqtt_client.subscribe(sendHealthStatusDataTopic) # subscribe topic
       print(f'Subscribed to {sendHealthStatusDataTopic}')
       mqtt_client.subscribe(sendHealthAdvisorDataTopic) # subscribe topic
       print(f'Subscribed to {sendHealthAdvisorDataTopic}')
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
    elif data["topic"] == receiveEWSResponseStatusTopic:
        print("Recibimos el EWS RESPONSE")
        print(data["payload"])
        data["id"] = len(mqtt_msgs) + 1
        data["type"] = "EWSResponseStatus"
        mqtt_msgs.append(data)
        print(mqtt_msgs)
        #socketio_server.emit("mqtt_message", data=data)
    elif data["topic"] == receiveHRSpO2ResponseStatusTopic:
        print("Recibimos el HR&SpO2 RESPONSE")
        print(data["payload"])
        data["id"] = len(mqtt_msgs) + 1
        data["type"] = "HR&SPO2ResponseStatus"
        mqtt_msgs.append(data)
        print(mqtt_msgs)
    elif data["topic"] == receiveOxyDemandResponseStatusTopic:
        print("Recibimos el Oxy demand RESPONSE")
        print(data["payload"])
        data["id"] = len(mqtt_msgs) + 1
        data["type"] = "OxygenDemandResponseStatus"
        mqtt_msgs.append(data)
        print(mqtt_msgs)
    elif data["topic"] == receiveHealthStatusResponseStatusTopic:
        print("Recibimos el Health status RESPONSE")
        print(data["payload"])
        data["id"] = len(mqtt_msgs) + 1
        data["type"] = "HealthStatusResponseStatus"
        mqtt_msgs.append(data)
        print(mqtt_msgs)
    elif data["topic"] == receiveHealthAdvisorResponseStatusTopic:
        print("Recibimos el Health advisor RESPONSE")
        print(data["payload"])
        data["id"] = len(mqtt_msgs) + 1
        data["type"] = "HealthAdvisorResponseStatus"
        mqtt_msgs.append(data)
        print(mqtt_msgs)



@mqtt_client.on_log()
def handle_mqtt_log(client, userdata, level, buf):
    if buf == "Received PINGRESP" or buf == "Sending PINGREQ":
        pass
    else:
        print("mqtt log:", client, userdata, level, buf)