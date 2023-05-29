from app import create_app, socketio_server, mqtt_client

app = create_app()
mqtt_client.app = app
socketio_server.run(app)