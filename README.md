# INPT Campus Energy Monitoring — Virtual IoT Lab


## What it simulates

- Four campus usage profiles: classrooms, laboratory, library, and residence.
- Three-phase meter readings for L1/L2/L3: voltage (V), current (A), active power (kW), and power factor.
- Meter-level frequency (Hz), total active power (kW), and cumulative energy (kWh).
- MQTT transport topics labelled `wifi` or `lora`.
- MQTT broker (Mosquitto) → Python collector → InfluxDB time-series database → Grafana dashboards.

**Important:** all readings are synthetic. `TRANSPORT=lora` simulates a LoRa-labelled data path in software; it does not emulate LoRa radio propagation or use physical LoRa hardware. This is not a replacement for calibrated real electrical measurements and must never be connected to electrical equipment.

## Requirements

- Windows 10/11 with Docker Desktop installed and running, or Linux with Docker Engine and the Compose plugin.
- Internet access on first run so Docker can pull images.

## Run on Windows

1. Install Docker Desktop and launch it. Wait until Docker reports that its engine is running.
2. Extract this folder to a simple path, for example `C:\iot_energy_virtual_lab`.
3. Open PowerShell in that folder.
4. Copy the example environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Start the platform:

   ```powershell
   docker compose up --build -d
   ```

6. Check that the containers are running:

   ```powershell
   docker compose ps
   docker compose logs -f simulator collector
   ```

7. Open Grafana at `http://localhost:3000`. Login: username `admin`, password `admin123`. Change the password if you keep this running beyond a local demo.
8. Open the dashboard **INPT Campus Energy Monitoring - Virtual Lab**. It may take 10–30 seconds for data to appear.

## Run on Linux

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
docker compose logs -f simulator collector
```

Then open `http://localhost:3000` and log in with `admin` / `admin123`.

## Switch the transport label

Edit `.env`:

```dotenv
TRANSPORT=lora
PUBLISH_INTERVAL_SECONDS=5
```

Then recreate the simulator:

```bash
docker compose up -d --build simulator
```

Set `TRANSPORT=wifi` to switch back. Both modes use MQTT in this virtual demo; the label lets you demonstrate how the topic structure could distinguish meter transport technologies.

## Useful checks

- Simulator output: `docker compose logs -f simulator`
- Collector output: `docker compose logs -f collector`
- InfluxDB health: open `http://localhost:8086/ping` (a successful response is normally HTTP 204).
- MQTT topics: `campus/energy/<wifi-or-lora>/<building>`
- InfluxDB database: `energy`; measurement: `energy_readings`.

To stop the platform:

```bash
docker compose down
```

To remove the containers **and erase stored InfluxDB/Grafana data**:

```bash
docker compose down -v
```

## Architecture

```text
Virtual 3-phase meters (Python)
   └── MQTT topic per building / transport label
         └── Mosquitto broker
               └── Python collector
                     └── InfluxDB (energy_readings)
                           └── Grafana dashboards
```

## Project limitations and next steps

- The article describes real meter hardware, campus installation, Wi-Fi/LoRa communication, data storage, Grafana visualization, and a data downloader. This starter reproduces the **software pipeline** and dashboards, not the physical electrical measurement hardware.
- The current version does not implement LoRaWAN, RS-485/Modbus, a PLC/SCADA connection, authentication for MQTT, or the article's separate downloader desktop application.
- Add a data export/downloader or anomaly-detection module as a next project step. For real measurements, use qualified supervision and properly rated isolated metering equipment; do not experiment directly on mains electricity.
