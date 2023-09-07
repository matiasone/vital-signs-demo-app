from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from markupsafe import escape
from flask_cors import CORS, cross_origin
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import json
import psycopg2
from .mqtt_client import mqtt_client, receiveEWSResponseStatusTopic, sendEWSDataTopic, receiveHRSpO2ResponseStatusTopic, sendHRSpO2DataTopic
from .mqtt_client import sendOxyDemandDataTopic, receiveOxyDemandResponseStatusTopic, sendHealthAdvisorDataTopic
from .mqtt_client import receiveHealthAdvisorResponseStatusTopic, sendHealthStatusDataTopic, receiveHealthStatusResponseStatusTopic

main = Blueprint("main", __name__)
CORS(main)
msg = []
contacts_by_rut = []
session = {}

os.environ['DB_USERNAME'] = "admin_tt"
os.environ['DB_PASSWORD'] = "wertones1"


def get_db_connection():
    conn = psycopg2.connect(host='localhost',
                            database='mydb_tt',
                            user=os.environ['DB_USERNAME'],
                            password=os.environ['DB_PASSWORD'])
    return conn

@main.route("/")
def index():
    return render_template("index.html", session=session)

@main.route("/register", methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        print(request.form); print(len(request.form))
        rut = request.form['p_rut']
        name = request.form['p_name']
        email = request.form['p_email']
        phone = request.form['p_phone']
        password = request.form['p_password']
        password2 = request.form['p_r_password']
        if not rut:
            flash('Rut is required!')
        elif not name:
            flash('Name is required!')
        elif not email:
            flash('Email is required!')
        elif not phone:
            flash('Email is required!')
        elif not password:
            flash('Password is required!')
        elif not password2:
            flash('Confirm password is required!')
        elif password != password2:
            flash('Passwords are different!')
        else:
            dicto = request.form.to_dict(flat=False)
            name = dicto["p_name"][0]; email = dicto["p_email"][0]; rut = dicto["p_rut"][0]
            phone = dicto["p_phone"][0]; password = dicto["p_password"][0]
            contacts = {}
            if ("p_rut" in dicto) & ("name" in dicto) & ("phone" in dicto) & ("email" in dicto):
                contacts = {
                    "rut": dicto["p_rut"][0],
                    "names": dicto["name"],
                    "phones": dicto["phone"],
                    "mails": dicto["email"]
                }

            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cur.fetchone()
            if account:
                flash('This email already has an account!')
                return render_template("register.html")
            conn.commit()
            cur.close()
            conn.close()
            hash_psswd = generate_password_hash(password, salt_length=50)
            contacts_by_rut.append(contacts)
            contacts_jsondumps = json.dumps(contacts)
            conn = get_db_connection()
            cur = conn.cursor()
            isAdmin = False
            cur.execute('INSERT INTO users (name, rut, email, phone, password, contacts, isAdmin)'
                        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (name, rut, email, phone, hash_psswd, contacts_jsondumps, isAdmin))
            conn.commit()
            cur.close()
            conn.close()
            return render_template("index.html", session=session)
    return render_template("register.html", session=session)

@main.route("/login", methods=('GET', 'POST'))
def login():
    if request.method == "POST":
        print(request.form); print(len(request.form))
        email = request.form['email']
        password = request.form['password']
        if not email:
            flash('Email is required!')
        elif not password:
            flash('Password is required!')
        else:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            account = cur.fetchone()
            print(account)
            print("isAdmin:", account[7])
            if account:
                password_rs = account[5] #password_rs = account["password"]
                print("check:", check_password_hash(password_rs, password))
                if check_password_hash(password_rs, password):
                    session["loggedin"] = True; session["id"] = account[0]
                    session["rut"] = account[2]; session["email"] = account[3]
                    session["phone"] = account[4]; session["name"] = account[1]
                    session["contacts"] = account[6]; session["isAdmin"] = account[7]
                    return redirect(url_for('main.patientDashboard'))
                else:
                    flash("Wrong password!")
                    render_template("login.html", session=session)
            else:
                flash('This email doesn`t have an account!')
    return render_template("login.html", session=session)

@main.route("/logout")
def logout():
    del session["loggedin"]
    return render_template("index.html", session=session)

@main.route("/patientDashboard")
def patientDashboard():
    if 'loggedin' in session:
        return redirect(url_for('main.showPatientDashboard', rut=session["rut"]))
    return render_template("dashboard-by-rut.html", session=session)

@main.route("/showPatientDashboard")
def showPatientDashboard():
    from .mqtt_client import mqtt_msgs
    rut = request.args["rut"]
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
                    if isinstance(res[1].split(":")[1], int):
                        res.append(int(res[1].split(":")[1]))
                    else:
                        res.append(2)
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
    #print(patient_data, hr_data, spo2_data, max30102labels, ews_labels, t_data, sbp_data, rr_data, ews_results, loc_data, so_data, t_labels, sbp_labels, dbp_data, glucose_data)
    #print(health_status_labels, health_status_data, health_advisor_labels, health_advisor_data)

    return render_template("patient-dashboard.html", session=session, patient_data = patient_data, hr_data=hr_data, spo2_data=spo2_data, max30102labels=max30102labels,
                           max30102results=max30102results, ews_labels=ews_labels, t_data=t_data, sbp_data=sbp_data, rr_data=rr_data, 
                           ews_results=ews_results, loc_data=loc_data, so_data=so_data, t_labels=t_labels, sbp_labels=sbp_labels, dbp_data=dbp_data,
                           glucose_data=glucose_data, health_status_labels=health_status_labels, health_advisor_labels=health_advisor_labels,
                           health_status_data=health_status_data, health_advisor_data=health_advisor_data, oxygen_demand_data=oxygen_demand_data,
                           oxygen_demand_labels=oxygen_demand_labels)

@main.route("/sentData")
def viewData():
    if "loggedin" in session:
        print(session["name"], session["rut"], session["isAdmin"])
        if session["isAdmin"]:
            return render_template("msgsIndex.html", messages=msg, session=session)
        else:
            return redirect(url_for("main.viewDataByRut", rut=session["rut"], rut_button=""))
    else:
        return render_template("index.html", messages=msg, session=session)

@main.route("/sentData/rut")
def viewDataByRut():
    print(request.args)
    if "loggedin" in session:
        if "rut_button" in request.args:
            rut = request.args["rut"]
            msgByRut = []
            for i in msg:
                if i["rut"] == rut:
                    msgByRut.append(i)
            return render_template("msgsIndex.html", messages=msgByRut, session=session)
        else:
            return render_template("msgsIndex.html", messages=msg, session=session)
    else:
        return render_template("index.html", messages=msg, session=session)

@main.route("/sentData/id")
def viewDataById(id):
    msgById = []
    for i in msg:
        if i["id"] == id:
            msgById.append(i)
    return render_template("msgsIndex.html", messages=msgById, session=session)

@main.route("/results")
def viewResults():
    from .mqtt_client import mqtt_msgs
    if "loggedin" in session:
        if session["isAdmin"]:
            return render_template("resultsIndex.html", messages=mqtt_msgs, session=session)
        else:
            return redirect(url_for("main.viewResultsByRut", rut=session["rut"], rut_button=""))
    else:
        return render_template("index.html", messages=mqtt_msgs, session=session)

@main.route("/results/rut")
def viewResultsByRut():
    from .mqtt_client import mqtt_msgs
    print(request.args)
    if "loggedin" in session:
        if "rut_button" in request.args:
            rut = request.args["rut"]
            msgByRut = []
            for i in mqtt_msgs:
                if i["rut"] == rut:
                    msgByRut.append(i)
            return render_template("resultsIndex.html", messages=msgByRut, session=session)
        else:
            return render_template("resultsIndex.html", messages=mqtt_msgs, session=session)
    else:
        return render_template("index.html", messages=mqtt_msgs, session=session)
@main.route("/results/id")
def viewResultsById(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == id:
            msgById.append(i)
    return render_template("resultsIndex.html", messages=msgById, session=session)

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
            flash('Rut is required!')
        elif not name:
            flash('Name is required!')
        elif not hr:
            flash('Heart rate is required!')
        elif not spo2:
            flash('Oxygen saturation is required!')    
        else:
            msg.append({'returnStatus': 0, 'type': "HR&SPO2", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2})
            print(msg)
            req_data = {
                "topic": sendHRSpO2DataTopic,
                "msg": f'DateTime=;rut={rut};hr={hr};spo2={spo2}'
            }
            publish_result = mqtt_client.publish(req_data['topic'], req_data['msg'])
            print(publish_result)
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHR&SPO2.html', session=session)

@main.route('/results/HR&SpO2/byRut/<rut>/')
def max30102_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut, session=session)

@main.route('/sentData/HR&SpO2/byRut/<rut>/')
def max30102_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut, session=session)

@main.route('/results/HR&SpO2/byId/<id>/')
def max30102_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById, session=session)

@main.route('/sentData/HR&SpO2/byId/<id>/')
def max30102_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgById, session=session)

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
            flash('Rut is required!')
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
    return render_template('postDataFormEWS.html', session=session)

@main.route('/results/EWS/byRut/<rut>/')
def ews_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut, session=session)

@main.route('/sentData/EWS/byRut/<rut>/')
def ews_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut, session=session)

@main.route('/results/EWS/byId/<id>/')
def ews_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById, session=session)

@main.route('/sentData/EWS/byId/<id>/')
def ews_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgById, session=session)

@main.route('/results/EWS/<rut>/<id>')
def ews_results_by_rut_and_id(rut, id):
    pass

@main.route('/sendPatientData/oxygenDemand/', methods=('GET', 'POST'))
@cross_origin(origin='*')
def create_oxy_demand():
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
            flash('Rut is required!')
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
    return render_template('postDataFormOxyDemand.html', session=session)

@main.route('/results/oxygenDemand/byId/<id>')
def oxy_demand_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgById, session=session)

@main.route('/sentData/oxygenDemand/byId/<id>')
def oxy_demand_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("msgsIndex.html", messages=msgById, session=session)

@main.route('/results/oxygenDemand/byRut/<rut>')
def oxy_demand_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("resultsIndex.html", messages=msgByRut, session=session)

@main.route('/sentData/oxygenDemand/byRut/<rut>')
def oxy_demand_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("msgsIndex.html", messages=msgByRut, session=session)

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
            flash('Rut is required!')
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
    return render_template('postDataFormHealthStatus.html', session=session)

@main.route('/results/healthStatus/byId/<id>')
def health_status_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("resultsIndex.html", messages=msgById, session=session)

@main.route('/sentData/healthStatus/byId/<id>')
def health_status_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("msgsIndex.html", messages=msgById, session=session)

@main.route('/results/healthStatus/byRut/<rut>')
def health_status_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("resultsIndex.html", messages=msgByRut, session=session)

@main.route('/sentData/healthStatus/byRut/<rut>')
def health_status_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["id"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("msgsIndex.html", messages=msgByRut, session=session)

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
            flash('Rut is required!')
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
    return render_template('postDataFormHealthAdvisor.html', session=session)

@main.route('/results/healthAdvisor/byId/<id>')
def health_advisor_results_by_id(id):
    from .mqtt_client import mqtt_msgs
    msgById = []
    for i in mqtt_msgs:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("resultsIndex.html", messages=msgById, session=session)

@main.route('/sentData/healthAdvisor/byId/<id>')
def health_advisor_msgs_by_id(id):
    msgById = []
    for i in msg:
        if i["id"] == int(id):
            msgById.append(i)
    if len(msgById) == 0:
        return render_template("404NotFound.html", session=session)
    return render_template("msgsIndex.html", messages=msgById, session=session)

@main.route('/results/healthAdvisor/byRut/<rut>')
def health_advisor_results_by_rut(rut):
    from .mqtt_client import mqtt_msgs
    msgByRut = []
    for i in mqtt_msgs:
        if i["rut"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("resultsIndex.html", messages=msgByRut, session=session)

@main.route('/sentData/healthAdvisor/byRut/<rut>')
def health_advisor_msgs_by_rut(rut):
    msgByRut = []
    for i in msg:
        if i["id"] == rut:
            msgByRut.append(i)
    if len(msgByRut) == 0:
        return render_template("404NotFound.html")
    return render_template("msgsIndex.html", messages=msgByRut, session=session)

@main.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   print(publish_result)
   return jsonify({'code': publish_result[0]})

@main.route('/about/')
def about():
    return render_template("about.html", messages=msg, session=session)