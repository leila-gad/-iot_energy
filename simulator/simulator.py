import json, math, os, random, time
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

HOST = os.getenv("MQTT_HOST", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
INTERVAL = max(1, int(os.getenv("PUBLISH_INTERVAL_SECONDS", "5")))
TRANSPORT = os.getenv("TRANSPORT", "wifi").lower()
if TRANSPORT not in ("wifi", "lora"):
    TRANSPORT = "wifi"

# Representative campus zones; values are synthetic and only for software testing.
BUILDINGS = {
    "classrooms": {"base_kw": 8.0, "phases": 3},
    "laboratory": {"base_kw": 12.0, "phases": 3},
    "library": {"base_kw": 5.0, "phases": 3},
    "residence": {"base_kw": 18.0, "phases": 3},
}
energy_kwh = {name: 0.0 for name in BUILDINGS}
start = time.time()
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="virtual-energy-meters")

while True:
    try:
        client.connect(HOST, PORT, 60)
        client.loop_start()
        print(f"Connected to MQTT at {HOST}:{PORT}; transport label={TRANSPORT}")
        break
    except Exception as exc:
        print(f"Waiting for MQTT: {exc}")
        time.sleep(3)

while True:
    now = time.time()
    elapsed_hours = INTERVAL / 3600.0
    for building, cfg in BUILDINGS.items():
        # Daily usage curve plus noise; the output is not a real electrical measurement.
        hour = datetime.now().hour + datetime.now().minute / 60
        daily_factor = 0.45 + 0.45 * max(0, math.sin((hour - 6) * math.pi / 16))
        total_kw = max(0.3, cfg["base_kw"] * daily_factor * random.uniform(0.88, 1.12))
        phase_weights = [random.uniform(0.28, 0.38) for _ in range(3)]
        weight_sum = sum(phase_weights)
        phase_weights = [w / weight_sum for w in phase_weights]
        phases = {}
        total_kwh_increment = 0.0
        for i, phase in enumerate(("L1", "L2", "L3")):
            voltage = random.uniform(228, 235)
            power_kw = total_kw * phase_weights[i]
            power_factor = random.uniform(0.88, 0.99)
            current = power_kw * 1000 / max(1, voltage * power_factor)
            energy_kwh[building] += power_kw * elapsed_hours
            total_kwh_increment += power_kw * elapsed_hours
            phases[phase] = {
                "voltage_v": round(voltage, 2),
                "current_a": round(current, 3),
                "active_power_kw": round(power_kw, 4),
                "power_factor": round(power_factor, 3),
            }
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "building": building,
            "meter_id": f"virtual-{building}-3phase",
            "transport": TRANSPORT,
            "simulated": True,
            "frequency_hz": round(random.uniform(49.9, 50.1), 2),
            "total_active_power_kw": round(total_kw, 4),
            "energy_kwh": round(energy_kwh[building], 5),
            "phases": phases,
        }
        topic = f"campus/energy/{TRANSPORT}/{building}"
        info = client.publish(topic, json.dumps(payload), qos=0)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Publish issue for {building}: rc={info.rc}")
        print(f"{topic} | {total_kw:.2f} kW | {energy_kwh[building]:.3f} kWh (SIMULATED)")
    time.sleep(INTERVAL)
