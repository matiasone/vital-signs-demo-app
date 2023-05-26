from flask import Flask, abort, request, jsonify, render_template, url_for, flash, redirect
from markupsafe import escape
from flask_mqtt import Mqtt
from flask_socketio import SocketIO
import eventlet

#eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = '9a6212f13d2370e87d273e56d418630f6e60ccc1748e1e06'

app.config['MQTT_BROKER_URL'] = "broker.hivemq.com"
app.config['MQTT_BROKER_PORT'] = 1883
app.config['MQTT_USERNAME'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_PASSWORD'] = ''  # Set this item when you need to verify username and password
app.config['MQTT_KEEPALIVE'] = 5  # Set KeepAlive time in seconds
app.config['MQTT_TLS_ENABLED'] = False  # If your broker supports TLS, set it True
activateESP32 = "/flask/mqtt/ActivarESP32"
receiveDataTopic = "/Max30102FromESP32"
sendDataTopic = '/flask/mqtt/PatientDataFromFlaskApp'
sendHRSpO2DataTopic = "/flask/mqtt/Max30102(1)"
sendEWSDataTopic = "/flask/mqtt/EWS"
sendOxyDemandDataTopic = "flask/mqtt/OxygenDemand"
sendHealthStatusDataTopic = "flask/mqtt/HealthStatus"
sendHealthAdvisorDataTopic = "flask/mqtt/HealthAdvisor"

mqtt_client = Mqtt(app)
socketio_server = SocketIO(app)

msg = []

@mqtt_client.on_connect()
def handle_connect(client, userdata, flags, rc):
   if rc == 0:
       print(f'Connected successfully to {app.config["MQTT_BROKER_URL"]}')
       mqtt_client.subscribe(receiveDataTopic) # subscribe topic
       print(f'Subscribed to {receiveDataTopic}')
   else:
       print('Bad connection. Code:', rc)

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

@mqtt_client.on_log()
def handle_mqtt_log(client, userdata, level, buf):
    if buf == "Received PINGRESP" or buf == "Sending PINGREQ":
        pass
    else:
        print("mqtt log:", client, userdata, level, buf)

@app.route("/")
def index():
    return "Hello World!"

@app.route("/sentData")
def viewData():
    return render_template("msgsIndex.html", messages=msg)

@app.route('/sendPatientData/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        rut = request.form['rut']
        name = request.form['name']
        hr = request.form['hr']
        spo2 = request.form['spo2']

        print(rut, name, hr, spo2)
        if not rut:
            flash('Rut is requiered!')
        elif not name:
            flash('Name is required!')
        elif not hr:
            flash('Heart rate is required!')
        elif not spo2:
            flash('Oxygen saturation is required!')    
        else:
            msg.append({'rut': rut, 'name': name, "hr": hr, "spo2": spo2})
            return redirect(url_for('viewData'))
    return render_template('postDataForm.html')

@app.route("/getPatientData/")
def getPatientData():
    return render_template("getMax30102Data.html", messages=msg)


@app.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   print(publish_result)
   return jsonify({'code': publish_result[0]})

@app.route('/about/')
def about():
    return '<h3>This is a Flask web application for Matías Fernández Titulation Project.</h3>'

@app.route('/capitalize/<word>/')
def capitalize(word):
    return '<h1>{}</h1>'.format(escape(word.capitalize()))

@app.route('/add/<int:n1>/<int:n2>/')
def add(n1, n2):
    return '<h1>{}</h1>'.format(n1 + n2)

@app.route('/users/<int:user_id>/')
def greet_user(user_id):
    users = ['Bob', 'Jane', 'Adam']
    try:
        return '<h2>Hi {}</h2>'.format(users[user_id])
    except IndexError:
        abort(404)

socketio_server.run(app, host='localhost', port=5000, use_reloader=True, debug=True)