from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, abort
from markupsafe import escape
from .mqtt_client import mqtt_client

main = Blueprint("main", __name__)

msg = []

@main.route("/")
def index():
    return render_template("index.html")

@main.route("/sentData")
def viewData():
    return render_template("msgsIndex.html", messages=msg)

@main.route("/sentData/<rut>")
def viewDataById(rut):
    msgByRut = []
    for i in msg:
        if i["rut"] == rut:
            msgByRut.append(i)
    return render_template("msgsIndex.html", messages=msgByRut)

@main.route('/sendPatientData/HR&SpO2/', methods=('GET', 'POST'))
def create_HRSpO2():
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
            msg.append({'type': "HR&SPO2", 'id': len(msg) + 1,'rut': rut, 'name': name, "hr": hr, "spo2": spo2})
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormHR&SPO2.html')

@main.route('/sendPatientData/EWS/', methods=('GET', 'POST'))
def create_EWS():
    if request.method == 'POST':
        rut = request.form['rut']
        name = request.form['name']
        hr = request.form['hr']
        spo2 = request.form['spo2']
        t = request.form['t']
        sbp = request.form['sbp']
        rr = request.form['rr']
        so = request.form['so']
        loc = request.form['loc']
        if so == "on":
            so = 1
        else:
            so = 0
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
            return redirect(url_for('main.viewData'))
    return render_template('postDataFormEWS.html')


@main.route('/publish', methods=['POST'])
def publish_message():
   request_data = request.get_json()
   publish_result = mqtt_client.publish(request_data['topic'], request_data['msg'])
   print(publish_result)
   return jsonify({'code': publish_result[0]})

@main.route('/about/')
def about():
    return render_template("about.html", messages=msg)