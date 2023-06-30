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

@main.route("/test/")
def test():
    return render_template("test.html")

@main.route("/chartTest")
def showChartTest():
    # Define Plot Data
    labels = [
        'January',
        'February',
        'March',
        'April',
        'May',
        'June',
    ]
 
    loc_data = ["Alert", "Confused", "Unresponsive", "Responsive to pain", "Responsive to voice", "Alert"]
    so_data = ["No SO", "SO", "No SO", "SO", "SO", "No SO"]
 
    # Return the components to the HTML template
    return render_template("chart-example.html", loc_data=loc_data, so_data=so_data, labels=labels)

@main.route("/patientDashboard/<rut>")
def showPatientDashboard(rut):
    from .mqtt_client import mqtt_msgs
    msgs_by_id = []
    results_by_id = []
    # personal data
    name = ""; age = 0; hadCovid = 0; gender = "none"
    for i in mqtt_msgs:
        if i["rut"] == rut:
            results_by_id.append(i)
            name = i["name"]
    for i in msg:
        if i["rut"] == rut:
            msgs_by_id.append(i)
    patient_data = []
    patient_data.append(rut)
    patient_data.append(name)
    # por ahora lo haremos solamente con HR&SpO2
    hr_data=[]; spo2_data=[]; max30102labels=[]; max30102results=[]
    # ahora con EWS0 
    ews_labels =[]; t_data = []; sbp_data = []; rr_data = []; loc_data = []; so_data = []; 
    ews_results = [[],[]]; sbp_labels = []; rr_labels = []; t_labels = []
    dbp_data=[]; glucose_data=[]
    health_advisor_labels=[]; health_status_labels=[]; health_advisor_data=[[],[]]; health_status_data=[[],[]]
    oxygen_demand_labels=[]; oxygen_demand_data=[]
    for i in msgs_by_id:
        for j in results_by_id:
            if i["type"] == "HR&SPO2":
                if i["id"] == j["id"]:
                    max30102labels.append(j["datetime"])
                    hr_data.append(i["hr"])
                    spo2_data.append(i["spo2"])
                    max30102results.append(j["payload"])
            elif i["type"] == "EWS":
                if i["id"] == j["id"]:
                    # agregar datos de HR y SpO2 a dashoard
                    max30102labels.append(j["datetime"])
                    hr_data.append(i["hr"])
                    spo2_data.append(i["spo2"])
                    # agregar datos de EWS a dashboard
                    ews_labels.append(j["datetime"])
                    t_labels.append(j["datetime"])
                    sbp_labels.append(j["datetime"])
                    t_data.append(i["t"]); sbp_data.append(i["sbp"]); rr_data.append(i["rr"])
                    # agregar datos no escalables (loc, so)
                    locToAdd = ""
                    if i["loc"] == "A":
                        locToAdd = "Alert"
                    elif i["loc"] == "C":
                        locToAdd = "Confused"
                    elif i["loc"] == "V":
                        locToAdd = "Responsive to voice"
                    elif i["loc"] == "P":
                        locToAdd = "Responsive to pain"
                    elif i["loc"] == "U":
                        locToAdd = "Unresponsive"
                    loc_data.append(locToAdd)
                    soToAdd = ""
                    print(i["so"], type(i["so"]))
                    if int(i["so"]) == 0:
                        soToAdd = "No SO"
                    elif int(i["so"]) == 1:
                        soToAdd = "SO"
                    so_data.append(soToAdd)
                    # tratar resultado ews
                    res = j["payload"].split(",")
                    res[0] = res[0].replace(" ", "")
                    res[1] = res[1].replace(" ", "")
                    res.append(res[0].split(":")[1])
                    res.append(int(res[1].split(":")[1]))
                    ews_results[0].append(res)
                    ews_results[1].append(int(res[1].split(":")[1]))
            elif i["type"] == "OxygenDemand":
                if i["id"] == j["id"]:
                    # agregar datos de HR y SpO2 a dashoard
                    max30102labels.append(j["datetime"])
                    hr_data.append(i["hr"])
                    spo2_data.append(i["spo2"])
                    # no escalables: age, hadCovid, gender
                    if len(patient_data) <= 2:
                        age = i["age"]; patient_data.append(age)
                        gender = i["gender"]
                        if int(gender) == 1:
                            patient_data.append("Male")
                        elif int(gender) == 0:
                            patient_data.append("Female")
                    hadCovid = i["hadCovid"]
                    if int(hadCovid) == 1:
                        patient_data.append("Positive")
                    elif int(hadCovid) == 0:
                        patient_data.append("Negative")
                    # resultado
                    print(j["payload"])
                    num = float(j["payload"].split(":")[1])
                    oxygen_demand_labels.append(j["datetime"])
                    oxygen_demand_data.append(num)
            elif i["type"] == "HealthStatus":
                if i["id"] == j["id"]:
                    print(j["payload"])
                    # agregar datos de HR y SpO2 a dashoard
                    max30102labels.append(j["datetime"])
                    hr_data.append(i["hr"])
                    spo2_data.append(i["spo2"])
                    # agregar temperatura
                    t_labels.append(j["datetime"])
                    t_data.append(i["t"])
                    # agregar health status
                    health_status_labels.append(j["datetime"])
                    res = j["payload"].split(":")
                    num = res[1].split(" ")[0]
                    num = num.replace("-", "")
                    health_status_data[0].append(res[1])
                    health_status_data[1].append(int(num))
            elif i["type"] == "HealthAdvisor":
                if i["id"] == j["id"]:
                    print(j["payload"])
                    # agregar datos de HR y SpO2 a dashoard
                    max30102labels.append(j["datetime"])
                    hr_data.append(i["hr"])
                    spo2_data.append(i["spo2"])
                    # agregar datos sbp, dbp, t, glucose
                    sbp_labels.append(j["datetime"])
                    t_labels.append(j["datetime"])
                    t_data.append(i["t"])
                    sbp_data.append(i["sbp"])
                    dbp_data.append(i["dbp"])
                    glucose_data.append(i["glucose"])
                    if len(patient_data) <= 2:
                        age = i["age"]; patient_data.append(age)
                        gender = i["gender"]; patient_data.append(gender)
                    health_advisor_labels.append(j["datetime"])
                    res = j["payload"].split(":")
                    num = res[1].split(" ")[0]
                    num = num.replace("-", "")
                    health_advisor_data[0].append(res[1])
                    health_advisor_data[1].append(int(num))
    print(patient_data, hr_data, spo2_data, max30102labels, ews_labels, t_data, sbp_data, rr_data, ews_results, loc_data, so_data, t_labels, sbp_labels, dbp_data, glucose_data)
    print(health_status_labels, health_status_data, health_advisor_labels, health_advisor_data)

    return render_template("patient-dashboard.html", patient_data = patient_data, hr_data=hr_data, spo2_data=spo2_data, max30102labels=max30102labels,
                           max30102results=max30102results, ews_labels=ews_labels, t_data=t_data, sbp_data=sbp_data, rr_data=rr_data, 
                           ews_results=ews_results, loc_data=loc_data, so_data=so_data, t_labels=t_labels, sbp_labels=sbp_labels, dbp_data=dbp_data,
                           glucose_data=glucose_data, health_status_labels=health_status_labels, health_advisor_labels=health_advisor_labels,
                           health_status_data=health_status_data, health_advisor_data=health_advisor_data, oxygen_demand_data=oxygen_demand_data,
                           oxygen_demand_labels=oxygen_demand_labels)

@main.route("/sentData")
def viewData():
    return render_template("msgsIndex.html", messages=msg)

@main.route("/sentData/rut")
def viewDataByRut():
    print(request.args)
    if "rut_button" in request.args:
        rut = request.args["rut"]
        msgByRut = []
        for i in msg:
            if i["rut"] == rut:
                msgByRut.append(i)
        return render_template("msgsIndex.html", messages=msgByRut)
    else:
        return render_template("msgsIndex.html", messages=msg)

@main.route("/sentData/id")
def viewDataById(id):
    msgById = []
    for i in msg:
        if i["id"] == id:
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById)

@main.route("/results")
def viewResults():
    from .mqtt_client import mqtt_msgs
    return render_template("resultsIndex.html", messages=mqtt_msgs)

@main.route("/results/rut")
def viewResultsByRut():
    from .mqtt_client import mqtt_msgs
    print(request.args)
    if "rut_button" in request.args:
        rut = request.args["rut"]
        msgByRut = []
        for i in mqtt_msgs:
            if i["rut"] == rut:
                msgByRut.append(i)
        return render_template("resultsIndex.html", messages=msgByRut)
    else:
        return render_template("resultsIndex.html", messages=mqtt_msgs)

@main.route("/results/id")
def viewResultsById(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == id:
            msgById.append(i)
    return render_template("resultsIndex.html", messages=msgById)

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
            msg.append({'returnStatus': 0, 'type': "HR&SPO2", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2})
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
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut)

@main.route('/sentData/HR&SpO2/byRut/<rut>/')
def max30102_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut)

@main.route('/results/HR&SpO2/byId/<id>/')
def max30102_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById)

@main.route('/sentData/HR&SpO2/byId/<id>/')
def max30102_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
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
            msg.append({'returnStatus': 0, 'type': "EWS", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "t": t, "sbp": sbp, "rr": rr, "so": so, "loc": loc})
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
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut)

@main.route('/sentData/EWS/byRut/<rut>/')
def ews_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut)

@main.route('/results/EWS/byId/<id>/')
def ews_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById)

@main.route('/sentData/EWS/byId/<id>/')
def ews_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
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
            msg.append({'returnStatus': 0, 'type': "OxygenDemand", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "age": age, "hadCovid": hadCovid, "gender": gender})
            req_data = {
                "topic": sendOxyDemandDataTopic,
                "msg": f'Datetime=;rut={rut};age={age};gender={gender};spo2={spo2};hr={hr};C/NC={hadCovid}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormOxyDemand.html')

@main.route('/results/oxygenDemand/byId/<id>')
def oxy_demand_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById)

@main.route('/sentData/oxygenDemand/byId/<id>')
def oxy_demand_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/results/oxygenDemand/byRut/<rut>')
def oxy_demand_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut)

@main.route('/sentData/oxygenDemand/byRut/<rut>')
def oxy_demand_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut)

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
            msg.append({'returnStatus': 0, 'type': "HealthStatus", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "t": t})
            req_data = {
                "topic": sendHealthStatusDataTopic,
                "msg": f'DateTime=;Rut={rut};HR={hr};T={t};SPO2={spo2}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHealthStatus.html')

@main.route('/results/healthStatus/byId/<id>')
def health_status_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById)

@main.route('/sentData/healthStatus/byId/<id>')
def health_status_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/results/healthStatus/byRut/<rut>')
def health_status_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut)

@main.route('/sentData/healthStatus/byRut/<rut>')
def health_status_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["id"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut)

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
            msg.append({'returnStatus': 0, 'type': "HealthAdvisor", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2, "t": t, 'glucose': glucose, 'age': age,'gender': gender, 'sbp': sbp, 'dbp': dbp})
            req_data = {
                "topic": sendHealthAdvisorDataTopic,
                "msg": f'DateTime=;Rut={rut};HR={hr};T={t};SPO2={spo2};Gender={gender};Age={age};SBP={sbp};DBP={dbp};Glucose={glucose}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHealthAdvisor.html')

@main.route('/results/healthAdvisor/byId/<id>')
def health_advisor_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById)

@main.route('/sentData/healthAdvisor/byId/<id>')
def health_advisor_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgById)

@main.route('/results/healthAdvisor/byRut/<rut>')
def health_advisor_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut)

@main.route('/sentData/healthAdvisor/byRut/<rut>')
def health_advisor_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["id"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut)

@main.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   print(publish_result)
   return jsonify({'code': publish_result[0]})

@main.route('/about/')
def about():
    return render_template("about.html", messages=msg)