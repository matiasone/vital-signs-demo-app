from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from markupsafe import escape
from flask_cors import CORS, cross_origin
import requests
from .mqtt_client import mqtt_client, receiveEWSResponseStatusTopic, sendEWSDataTopic, receiveHRSpO2ResponseStatusTopic, sendHRSpO2DataTopic
from .mqtt_client import sendOxyDemandDataTopic, receiveOxyDemandResponseStatusTopic, sendHealthAdvisorDataTopic
from .mqtt_client import receiveHealthAdvisorResponseStatusTopic, sendHealthStatusDataTopic, receiveHealthStatusResponseStatusTopic

main = Blueprint("main", __name__)
CORS(main)
msg = []

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/sentData")
def viewData():
    return render_template("msgsIndex.html", messages=msg)

@main.route("/sentData/<rut>")
def viewDataByRut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    return render_template("msgsIndex.html", messages=msgByRut)

@main.route("/sentData/<id>")
def viewDataById(id):
    msgById = []
    for i in msg:
        if i["rut"] == id:
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/sendPatientData/HR&SpO2/', methods=('GET', 'POST'))
def create_HRSpO2():
    if request.method == 'POST':
        mqtt_client.subscribe(receiveHRSpO2ResponseStatusTopic) # subscribe topic
        print(f'Subscribed to {receiveHRSpO2ResponseStatusTopic}')
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
            msg.append({'type': "HR&SPO2", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2})
            req_data = {
                "topic": sendHRSpO2DataTopic,
                "msg": f'DateTime=;rut={rut};hr={hr};spo2={spo2}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHR&SPO2.html')

@main.route('/results/HR&SpO2/byRut/<rut>/')
def max30102_results_by_rut(rut):
    """Este hay que revisarlo bien pq todavía no recibimos HR y SPO2 por rut"""
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    return render_template("msgsIndex.html", messages=msgByRut)


@main.route('/results/HR&SpO2/byId/<id>/')
def max30102_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    print(mqtt_msgs)
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    print(msgById)
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/results/HR&SpO2/<rut>/<id>')
def max30102_results_by_rut_and_id(rut, id):
    pass

@main.route('/sendPatientData/EWS/', methods=('GET', 'POST'))
def create_EWS():
    if request.method == 'POST':
        mqtt_client.subscribe(receiveEWSResponseStatusTopic) # subscribe topic
        print(f'Subscribed to {receiveEWSResponseStatusTopic}')
        rut = request.form['rut']
        name = request.form['name']
        hr = request.form['hr']
        spo2 = request.form['spo2']
        t = request.form['t']
        sbp = request.form['sbp']
        rr = request.form['rr']
        so = request.form['so']
        loc = request.form['loc']
        if not rut:
            flash('Rut is requiered!')
        elif not name:
            flash('Name is required!')
        elif not hr:
            flash('Heart rate is required!')
        elif not spo2:
            flash('Oxygen saturation is required!')    
        else:
            msg.append({'type': "EWS", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "t": t, "sbp": sbp, "rr": rr, "so": so, "loc": loc})
            req_data = {
                "topic": sendEWSDataTopic,
                "msg": f'DateTime=;rut={rut};hr={hr};spo2={spo2};rr={rr};so={so};t={t};sbp={sbp};loc={loc}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormEWS.html')

@main.route('/results/EWS/byRut/<rut>/')
def ews_results_by_rut(rut):
    """Este hay que revisarlo bien pq todavía no recibimos EWS por rut"""
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    return render_template("msgsIndex.html", messages=msgByRut)

@main.route('/results/EWS/byId/<id>/')
def ews_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/results/EWS/<rut>/<id>')
def ews_results_by_rut_and_id(rut, id):
    pass

@main.route('/sendPatientData/oxygenDemand/', methods=('GET', 'POST'))
@cross_origin(origin='*')
def create_oxy_demand():
    """data = request.get_json(force=True)
    url = "http://localhost:52773/api/oximetry-ml/predictions/oxygen-demand"
    req_data = {
        "Age": data["Age"],
        "Blood oxygen": data["Blood oxygen"],
        "Heart rate": data["Heart rate"],
        "HadCovid": data["HadCovid"],
        "Gender": data["Gender"]
    }
    hdrs = {
        "Cookie": "CSPSESSIONID-SP-52773-UP-api-oximetry-ml-=001000000000Juz34LtA4t00zD5FomzZwrgkD$c9xlG3kyLP13; CSPWSERVERID=E33cVBPL",
        "Content-Type": "application/json",
        "User-Agent": "PostmanRuntime/7.32.2",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": '*',
        "Access-Control-Allow-Methods": 'PUT, GET, POST, DELETE, OPTIONS',
        "Access-Control-Allow-Headers": 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'
    }
    resp = requests.post(url=url, json=req_data, headers=hdrs)
    print(resp)"""
    if request.method == 'POST':
        mqtt_client.subscribe(receiveOxyDemandResponseStatusTopic) # subscribe topic
        print(f'Subscribed to {receiveOxyDemandResponseStatusTopic}')
        print(request.form)
        rut = request.form['rut']
        name = request.form['name']
        hr = request.form['hr']
        spo2 = request.form['spo2']
        age = request.form['age']
        hadCovid = request.form['hadCovid']
        gender = request.form['gender']
        if not rut:
            flash('Rut is requiered!')
        elif not name:
            flash('Name is required!')
        elif not hr:
            flash('Heart rate is required!')
        elif not spo2:
            flash('Oxygen saturation is required!')
        elif not age:
            flash('Age is required!')
        elif not hadCovid:
            flash('information on whether the patient had covid is required!')
        else:
            msg.append({'type': "OxygenDemand", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "age": age, "hadCovid": hadCovid, "gender": gender})
            req_data = {
                "topic": sendOxyDemandDataTopic,
                "msg": f'Datetime=;rut={rut};age={age};gender={gender};spo2={spo2};hr={hr};C/NC={hadCovid}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormOxyDemand.html')

@main.route('/results/oxygenDemand/<id>')
def oxy_demand_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/sendPatientData/healthStatus/', methods=('GET', 'POST'))
@cross_origin(origin='*')
def create_health_status():
    if request.method == 'POST':
        mqtt_client.subscribe(receiveHealthStatusResponseStatusTopic) # subscribe topic
        print(f'Subscribed to {receiveHealthStatusResponseStatusTopic}')
        print(request.form)
        rut = request.form['rut']
        name = request.form['name']
        hr = request.form['hr']
        spo2 = request.form['spo2']
        t = request.form['t']
        if not rut:
            flash('Rut is requiered!')
        elif not name:
            flash('Name is required!')
        elif not hr:
            flash('Heart rate is required!')
        elif not spo2:
            flash('Oxygen saturation is required!')
        elif not t:
            flash('Temperature is required!')
        else:
            msg.append({'type': "HealthStatus", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "t": t})
            req_data = {
                "topic": sendHealthStatusDataTopic,
                "msg": f'DateTime=;Rut={rut};HR={hr};T={t};SPO2={spo2}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHealthStatus.html')

@main.route('/results/healthStatus/<id>')
def health_status_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/sendPatientData/healthAdvisor/', methods=('GET', 'POST'))
@cross_origin(origin='*')
def create_health_advisor():
    if request.method == 'POST':
        mqtt_client.subscribe(receiveHealthAdvisorResponseStatusTopic) # subscribe topic
        print(f'Subscribed to {receiveHealthAdvisorResponseStatusTopic}')
        print(request.form)
        rut = request.form['rut']
        name = request.form['name']
        hr = request.form['hr']
        spo2 = request.form['spo2']
        t = request.form['t']
        age = request.form['age']
        glucose = request.form['glucose']
        gender = request.form['gender']
        sbp = request.form['sbp']
        dbp = request.form['dbp']
        if not rut:
            flash('Rut is requiered!')
        elif not name:
            flash('Name is required!')
        elif not hr:
            flash('Heart rate is required!')
        elif not spo2:
            flash('Oxygen saturation is required!')
        elif not t:
            flash('Temperature is required!')
        elif not age:
            flash('Age is required!')
        elif not glucose:
            flash("Glucose level is required")
        else:
            msg.append({'type': "HealthAdvisor", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "t": t, 'glucose': glucose, 'gender': gender, 'sbp': sbp, 'dbp': dbp})
            req_data = {
                "topic": sendHealthAdvisorDataTopic,
                "msg": f'DateTime=;Rut={rut};HR={hr};T={t};SPO2={spo2};Gender={gender};Age={age};SBP={sbp};DBP={dbp};Glucose={glucose}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHealthAdvisor.html')

@main.route('/results/healthAdvisor/<id>')
def health_advisor_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   print(publish_result)
   return jsonify({'code': publish_result[0]})

@main.route('/about/')
def about():
    return render_template("about.html", messages=msg)