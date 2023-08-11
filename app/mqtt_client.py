from flask_mqtt import Mqtt
from .extensions import socketio_server
from datetime import datetime

mqtt_client = Mqtt()

#activateESP32 = "/flask/mqtt/ActivarESP32"
receiveDataTopic = "/Max30102FromESP32"
#sendHRSpO2DataTopic = "/flask/mqtt/Max30102(1)"
#sendEWSDataTopic = "/flask/mqtt/EWS"
#sendOxyDemandDataTopic = "flask/mqtt/OxygenDemand"
#sendHealthStatusDataTopic = "flask/mqtt/HealthStatus"
#sendHealthAdvisorDataTopic = "flask/mqtt/HealthAdvisor"
activateESP32 = "/ActivarESP32"
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
    from .routes import msg, contacts_by_rut
    data = dict(
       topic=message.topic,
       payload=message.payload.decode()
    )
    print('Received message on topic: {topic} with payload: {payload}'.format(**data))
    print("MSG:", msg)
    now = datetime.now()
    date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
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
        data["id"] = len(msg)
        data["rut"] = msg[len(msg)-1]["rut"]
        data["name"] = msg[len(msg)-1]["name"]
        data["datetime"] = date_time
        data["type"] = "EWSResponseStatus"
        include = True
        for i in mqtt_msgs:
            if i["id"] == data["id"]:
                print("ESTA ENTRADA YA ESTÁ, NO DEBERÍAMOS DEJARLA PASAR MIERDA")
                include = False
        if include:
            print("La dejamos pasar jiji")
            mqtt_msgs.append(data)
        print(mqtt_msgs)
        socketio_server.emit("mqtt_response_display", data=data)
    elif data["topic"] == receiveHRSpO2ResponseStatusTopic:
        from .notifications import send_email_sms
        print("Recibimos el HR&SpO2 RESPONSE")
        print(data["payload"])
        data["id"] = len(msg)
        data["rut"] = msg[len(msg)-1]["rut"]
        data["name"] = msg[len(msg)-1]["name"]
        data["datetime"] = date_time
        data["type"] = "HR&SPO2ResponseStatus"
        data["input_hr"] = msg[len(msg)-1]["hr"]
        data["input_spo2"] = msg[len(msg)-1]["spo2"]
        include = True
        for i in range(len(mqtt_msgs)):
            if mqtt_msgs[i]["id"] == data["id"]:
                mqtt_msgs[i] = data
                include = False
        if include:
            mqtt_msgs.append(data)
            input_ = [data["input_hr"], data["input_spo2"]]
            send_email_sms(data["name"], data["rut"], data["payload"], input_, data["datetime"], "HR&SpO2", contacts_by_rut)
        print(mqtt_msgs)
        socketio_server.emit("mqtt_response_display", data=data)
    elif data["topic"] == receiveOxyDemandResponseStatusTopic:
        print("Recibimos el Oxy demand RESPONSE")
        print(data["payload"])
        data["id"] = len(msg)
        data["rut"] = msg[len(msg)-1]["rut"]
        data["name"] = msg[len(msg)-1]["name"]
        data["datetime"] = date_time
        data["type"] = "OxygenDemandResponseStatus"
        include = True
        for i in mqtt_msgs:
            if i["id"] == data["id"]:
                print("ESTA ENTRADA YA ESTÁ, NO DEBERÍAMOS DEJARLA PASAR MIERDA")
                include = False
        if include:
            print("La dejamos pasar jiji")
            mqtt_msgs.append(data)
        print(mqtt_msgs)
        socketio_server.emit("mqtt_response_display", data=data)
    elif data["topic"] == receiveHealthStatusResponseStatusTopic:
        print("Recibimos el Health status RESPONSE")
        print(data["payload"])
        data["id"] = len(msg)
        data["rut"] = msg[len(msg)-1]["rut"]
        data["name"] = msg[len(msg)-1]["name"]
        data["datetime"] = date_time
        data["type"] = "HealthStatusResponseStatus"
        include = True
        for i in mqtt_msgs:
            if i["id"] == data["id"]:
                print("ESTA ENTRADA YA ESTÁ, NO DEBERÍAMOS DEJARLA PASAR MIERDA")
                include = False
        if include:
            print("La dejamos pasar jiji")
            mqtt_msgs.append(data)
        print(mqtt_msgs)
        socketio_server.emit("mqtt_response_display", data=data)
    elif data["topic"] == receiveHealthAdvisorResponseStatusTopic:
        print("Recibimos el Health advisor RESPONSE")
        print(data["payload"])
        data["id"] = len(msg)
        data["rut"] = msg[len(msg)-1]["rut"]
        data["name"] = msg[len(msg)-1]["name"]
        data["datetime"] = date_time
        data["type"] = "HealthAdvisorResponseStatus"
        include = True
        for i in mqtt_msgs:
            if i["id"] == data["id"]:
                print("ESTA ENTRADA YA ESTÁ, NO DEBERÍAMOS DEJARLA PASAR MIERDA")
                include = False
        if include:
            print("La dejamos pasar jiji")
            mqtt_msgs.append(data)
        print(mqtt_msgs)
        socketio_server.emit("mqtt_response_display", data=data)


@mqtt_client.on_log()
def handle_mqtt_log(client, userdata, level, buf):
    if buf == "Received PINGRESP" or buf == "Sending PINGREQ":
        pass
    else:
        print("mqtt log:", client, userdata, level, buf)