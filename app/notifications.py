def send_email_sms(name, rut, payload, input, datetime, feature, contacts):
    print("estamos en send email-sms")
    if feature == "HR&SpO2":
        # obtener lista de correos y números por rut del paciente
        print("contactos:", contacts)
        for i in contacts:
            print(i)
            print(rut, i["rut"], rut==i["rut"])
            if i["rut"] == rut:
                print("enviaremos correo y sms")
                correo(name, rut, i["mails"], payload, input, datetime)
                sms(name, rut, i["mails"], payload, input, datetime)

def sms(name, rut, receivers, payload, input, datetime):
    from twilio.rest import Client
    import keys
    client = Client(keys.account_sid, keys.auth_token)
    str = f'Patient {name} has registered the following parameters for heart rate and oxygen saturation: '
    parametros = f'{input[0]} y {input[1]}. '
    str2 = "According to EWS protocol,  "
    fecha = f' Date: {datetime}'
    str_final = str + parametros + str2 + payload + "." + fecha
    message = client.messages.create(
        body = str_final,
        from_ = keys.phone_number,
        to = keys.my_phone_number
    )
    print(message.body)

def correo(name, rut, receivers, payload, input, datetime):
    import smtplib, ssl
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    str = f'Patient {name} has registered the following parameters for heart rate and oxygen saturation: '
    parametros = f'{input[0]} y {input[1]}. '
    str2 = "According to EWS protocol,  "
    fecha = f' Date: {datetime}'

    str_final = str + parametros + str2 + payload + "." + fecha
    str_encoded = str_final.encode("utf-8")
    print(str_encoded)
    smtp_address = 'smtp.gmail.com'
    smtp_port = 465
    email_address = "matiaspruebas97@gmail.com"
    email_password = "rvgnfqyihxotevak"

    context = ssl.create_default_context()

    print(str_final)

    
    message = MIMEMultipart("alternative")
    message["Subject"] = f'{name}`s vital signs'
    message["From"] = email_address
    texte = f'''
        {str_final}
        Cdt
        mon_lien_incroyable
        '''
    html = f'''
        <html>
        <body>
        <p>{str_final}</p>
        <b>Cdt</b>
        <br>
        <a href="http://127.0.0.1:5000/showPatientDashboard?rut={rut}">vital signs demo app</a>
        </body>
        </html>
        '''
    texte_mime = MIMEText(texte, 'plain')
    html_mime = MIMEText(html, 'html')
    message.attach(texte_mime)
    message.attach(html_mime)

    # de aquí en adelante no funciona pero para mañana lo dejamos tiki taka
    with smtplib.SMTP_SSL(smtp_address, smtp_port, context=context) as server:
        server.login(email_address, email_password)
        for email_receiver in receivers:
            print(email_receiver)
            message["To"] = email_receiver
            server.sendmail(email_address, email_receiver, message.as_string())
            print(message)
            del message["To"]