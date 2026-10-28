import json, os, time
from datetime import datetime
import paho.mqtt.client as mqtt
from influxdb import InfluxDBClient

MQTT_HOST = os.getenv("MQTT_HOST", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
DB_HOST = os.getenv("INFLUX_HOST", "influxdb")
DB_PORT = int(os.getenv("INFLUX_PORT", "8086"))
DB_NAME = os.getenv("INFLUX_DB", "energy")

db = InfluxDBClient(host=DB_HOST, port=DB_PORT, database=DB_NAME)
for _ in range(30):
    try:
        db.ping()
        break
    except Exception:
        time.sleep(2)

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"MQTT connected: {reason_code}")
    client.subscribe("campus/energy/+/+")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8"))
        fields = {
            "total_active_power_kw": float(data["total_active_power_kw"]),
            "energy_kwh": float(data["energy_kwh"]),
            "frequency_hz": float(data["frequency_hz"]),
            "simulated": 1,
        }
        for phase, values in data["phases"].items():
            for key, value in values.items():
                fields[f"{phase}_{key}"] = float(value)
        point = [{
            "measurement": "energy_readings",
            "time": datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00")),
            "tags": {"building": data["building"], "meter_id": data["meter_id"], "transport": data["transport"]},
            "fields": fields,
        }]
        db.write_points(point, time_precision="s")
        print(f"Stored {data['building']} | {fields['total_active_power_kw']} kW")
    except Exception as exc:
        print(f"Could not process MQTT message: {exc}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="energy-influx-collector")
client.on_connect = on_connect
client.on_message = on_message
while True:
    try:
        client.connect(MQTT_HOST, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as exc:
        print(f"Waiting/reconnecting to MQTT: {exc}")
        time.sleep(3)
