#!/usr/bin/env python3
"""
IoT Gateway Test Script
Chay script nay de kiem tra tat ca dependencies truoc khi chay app chinh
"""

import sys
import platform

print("=" * 50)
print("  IoT Gateway - Kiem tra moi truong")
print(f"  {platform.system()} {platform.release()}")
print("=" * 50)
print()

errors = []

# 1. Python version
print("[1/5] Python version...")
ver = sys.version_info
print(f"  Python {ver.major}.{ver.minor}.{ver.micro}")
if ver.major < 3 or (ver.major == 3 and ver.minor < 8):
    print("  [WARN] Nen dung Python 3.8+")
print()

# 2. PyQt5
print("[2/5] PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import PYQT_VERSION_STR
    print(f"  PyQt5 {PYQT_VERSION_STR} - OK")
except ImportError as e:
    print(f"  [ERROR] PyQt5 khong co: {e}")
    errors.append("PyQt5")

# 3. paho-mqtt
print("[3/5] paho-mqtt...")
try:
    import paho.mqtt.client as mqtt
    ver = getattr(mqtt, '__version__', 'installed')
    print(f"  paho-mqtt {ver} - OK")
except ImportError as e:
    print(f"  [ERROR] paho-mqtt khong co: {e}")
    errors.append("paho-mqtt")

# 4. pymodbus
print("[4/5] pymodbus...")
try:
    import pymodbus
    print(f"  pymodbus {pymodbus.__version__} - OK")
except ImportError as e:
    print(f"  [ERROR] pymodbus khong co: {e}")
    errors.append("pymodbus")

# 5. Network connectivity
print("[5/5] Network test...")
try:
    import socket
    s = socket.create_connection(("test.mosquitto.org", 1883), timeout=5)
    s.close()
    print("  MQTT broker (test.mosquitto.org:1883) - OK")
except Exception as e:
    print(f"  [WARN] Khong ket noi MQTT broker: {e}")
    print("  (Van co the chay offline)")

# Summary
print()
print("=" * 50)
if errors:
    print(f"  THIEU: {', '.join(errors)}")
    print(f"  Chay: pip install {' '.join(errors)}")
else:
    print("  Tat ca OK! Chay: python main.py")
print("=" * 50)
