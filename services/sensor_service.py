"""
Soil Sensor Reader Service for Project KISAN.
Integrates RS485 Modbus RTU hardware sensor reading over /dev/ttyUSB0.
When the physical sensor is not attached, returns is_online=False and '--' values.
"""

import os, struct, time
from datetime import datetime


try:
    import serial
    SERIAL_OK = True
except ImportError:
    SERIAL_OK = False

# Modbus RTU Probe Configuration
PORT = "/dev/ttyUSB0"
BAUDRATE = 4800
SLAVE = 0x01
TIMEOUT = 1.0


def _crc(data: bytes) -> bytes:
    """Calculate Modbus RTU 16-bit CRC."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return bytes([crc & 0xFF, (crc >> 8) & 0xFF])


def _s16(v: int) -> int:
    """Convert unsigned 16-bit int to signed 16-bit int."""
    return v - 0x10000 if v >= 0x8000 else v


class SensorService:
    """Hardware Modbus RTU Soil Sensor Service."""

    @staticmethod
    def read_hardware_sensor() -> dict:
        """
        Read raw RS485 Modbus RTU sensor payload from /dev/ttyUSB0.
        Returns dict if physical sensor is attached and responding, None if offline.
        """
        if not SERIAL_OK or not os.path.exists(PORT):
            return None
        try:
            raw = bytes([SLAVE, 0x03, 0x00, 0x00, 0x00, 0x09])
            frame = raw + _crc(raw)
            with serial.Serial(PORT, BAUDRATE, bytesize=8, parity="N", stopbits=1, timeout=TIMEOUT) as s:

                s.reset_input_buffer()
                s.write(frame)
                time.sleep(0.2)
                resp = s.read(23)

            if len(resp) < 23 or resp[1] != 0x03:
                return None

            bc = resp[2]
            data = resp[3:3 + bc]
            if len(data) < 18:
                return None

            r = struct.unpack(">9H", data[:18])
            return dict(
                moisture=round(r[0] / 10.0, 1),
                temperature=round(_s16(r[1]) / 10.0, 1),
                ec=r[2],
                ph=round(r[3] / 10.0, 1),
                nitrogen=float(r[4]),
                phosphorus=float(r[5]),
                potassium=float(r[6]),
                salinity=float(r[7]),
                tds=float(r[8]),
                is_hardware=True
            )
        except Exception:
            return None

    @staticmethod
    def read_sensor_data(simulate_if_offline: bool = False) -> dict:
        """
        Main sensor entry point.
        If physical sensor is not attached, returns is_online=False and '--' values.
        """
        hw_data = SensorService.read_hardware_sensor()

        if hw_data is not None:
            ph = hw_data["ph"]
            n = hw_data["nitrogen"]
            p = hw_data["phosphorus"]
            k = hw_data["potassium"]
            m = hw_data["moisture"]
            t = hw_data["temperature"]
            ec = hw_data["ec"]
            sample_id = f"SMP-{datetime.now().strftime('%M%S')}"
            return {
                "is_online": True,
                "status_text": "● SENSOR ONLINE",
                "sample_id": sample_id,
                "ph": ph,
                "nitrogen": n,
                "phosphorus": p,
                "potassium": k,
                "moisture": m,
                "temperature": t,
                "ec": ec,
                "display_values": {
                    "ph": f"{ph}",
                    "nitrogen": f"{n} mg/kg",
                    "phosphorus": f"{p} mg/kg",
                    "potassium": f"{k} mg/kg",
                    "moisture": f"{m} %",
                    "temperature": f"{t} °C",
                },
                "tags": {
                    "ph": SensorService.get_qualitative_tag("ph", ph),
                    "nitrogen": SensorService.get_qualitative_tag("nitrogen", n),
                    "phosphorus": SensorService.get_qualitative_tag("phosphorus", p),
                    "potassium": SensorService.get_qualitative_tag("potassium", k),
                    "moisture": SensorService.get_qualitative_tag("moisture", m),
                    "temperature": SensorService.get_qualitative_tag("temperature", t),
                }
            }
        else:
            # Physical sensor is NOT attached / offline
            return {
                "is_online": False,
                "status_text": "● SENSOR OFFLINE",
                "sample_id": "--",
                "ph": None,
                "nitrogen": None,
                "phosphorus": None,
                "potassium": None,
                "moisture": None,
                "temperature": None,
                "ec": None,
                "display_values": {
                    "ph": "--",
                    "nitrogen": "--",
                    "phosphorus": "--",
                    "potassium": "--",
                    "moisture": "--",
                    "temperature": "--",
                },
                "tags": {
                    "ph": "Sensor Offline",
                    "nitrogen": "Sensor Offline",
                    "phosphorus": "Sensor Offline",
                    "potassium": "Sensor Offline",
                    "moisture": "Sensor Offline",
                    "temperature": "Sensor Offline",
                }
            }

    @staticmethod
    def get_qualitative_tag(parameter: str, value: float) -> str:
        """Get human-readable qualitative evaluation tag."""
        if value is None:
            return "Sensor Offline"
        if parameter == "ph":
            if value < 6.0: return "Acidic (Low)"
            elif value > 7.5: return "Alkaline (High)"
            return "Neutral (Optimal)"
        elif parameter == "nitrogen":
            if value < 50: return "Low"
            elif value > 90: return "High"
            return "Optimal"
        elif parameter == "phosphorus":
            if value < 30: return "Low"
            elif value > 55: return "High"
            return "Optimal"
        elif parameter == "potassium":
            if value < 150: return "Low"
            elif value > 220: return "High"
            return "Optimal"
        elif parameter == "moisture":
            if value < 30: return "Dry (Low)"
            elif value > 50: return "Wet (High)"
            return "Moist (Good)"
        elif parameter == "temperature":
            if value < 20: return "Cool"
            elif value > 30: return "Warm"
            return "Ideal"
        return "Normal"
