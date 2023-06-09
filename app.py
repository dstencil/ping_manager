from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import threading
import time
from ping3 import ping, verbose_ping

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'  # Update the database URI as needed
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define Device model
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(15), unique=True, nullable=False)

    def __repr__(self):
        return f'<Device {self.ip_address}>'

# Define PingResult model
class PingResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    result = db.Column(db.Boolean, nullable=False)

    def __repr__(self):
        return f'<PingResult for Device {self.device_id}: {self.result} at {self.timestamp}>'

# Create devices table if not exists
with app.app_context():
    db.create_all()

# Function to perform ping and update PingResult table
def perform_ping(device_id):
    device = Device.query.get(device_id)
    if device:
        result = ping(device.ip_address)
        if result is not None:
            ping_result = PingResult(device_id=device_id, result=result)
        else:
            ping_result = PingResult(device_id=device_id, result=False)
        db.session.add(ping_result)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/devices', methods=['GET'])
def get_devices():
    devices = Device.query.all()
    devices_list = []
    for device in devices:
        devices_list.append({'id': device.id, 'ip_address': device.ip_address})
    return jsonify({'devices': devices_list})

@app.route('/add', methods=['POST'])
def add_device():
    ip_addresses = request.form['ip_address'].split(',')
    for ip_address in ip_addresses:
        ping_result = ping(ip_address.strip())  # Strip any leading/trailing whitespace from IP address

        if ping_result is not None and ping_result != False:  # If the device is pingable
            device = Device(ip_address=ip_address.strip())  # Pass user_name and user_password to Device constructor
            db.session.add(device)
            #db.session.commit()
        else:  # If the device is not pingable
            return f'Device with IP address {ip_address} is not alive or Duplicate IP Address. Try Again'
    db.session.commit()
    return 'Devices added successfully'
@app.route('/ping', methods=['POST'])
def ping_device():
    device_id = request.form['device']
    device = Device.query.get(device_id)
    if device:
        result = ping(device.ip_address)
        if result is not None and result != False:
            return jsonify({'result': f'Ping result for device with id {device_id}: {result} ms (Success)'})
        else:
            return jsonify({'result': f'Ping failed for device with id {device_id} (Failure)'})
    else:
        return 'Device not found', 404

@app.route('/delete_device', methods=['POST'])
def delete_device():
    device_id = request.form['device_id']
    device = Device.query.get(device_id)
    if device:
        db.session.delete(device)
        db.session.commit()
        return 'Device deleted successfully'
    else:
        return 'Device not found', 404

if __name__ == '__main__':
    app.run(debug=True)
