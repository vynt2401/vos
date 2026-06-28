#!/usr/bin/env python3
"""
Modbus TCP Server - Mau de test tab Modbus trong IoT Gateway
Chay truoc khi test: python modbus_server.py
"""

import random
import time
import threading
import pymodbus

try:
    from pymodbus.server import StartTcpServer
    from pymodbus.datastore import (
        ModbusSequentialDataBlock,
        ModbusSlaveContext,
        ModbusServerContext,
    )
    HAS_PYMODBUS = True
except ImportError:
    HAS_PYMODBUS = False

try:
    from twisted.internet import reactor
    HAS_TWISTED = False
except ImportError:
    HAS_TWISTED = False


def create_store():
    """Tao Modbus data store voi gia tri mau"""
    hr_values = [0] * 100
    ir_values = [0] * 100
    coil_values = [False] * 100

    # Holding registers: gia tri mau sensor
    hr_values[0] = 2550   # temperature x100 = 25.50 C
    hr_values[1] = 6500   # humidity x100 = 65.00%
    hr_values[2] = 1013   # pressure = 1013 hPa
    hr_values[3] = 500    # light = 500 lux
    hr_values[4] = 330    # battery x10 = 33.0V

    # Input registers: gia tri thoi gian
    ir_values[0] = int(time.time()) & 0xFFFF
    ir_values[1] = (int(time.time()) >> 16) & 0xFFFF
    ir_values[2] = 42     # uptime minutes
    ir_values[3] = 99     # free memory %

    # Coils: trang thai
    coil_values[0] = True   # sensor 1 online
    coil_values[1] = True   # sensor 2 online
    coil_values[2] = False  # sensor 3 offline
    coil_values[3] = True   # relay 1 ON
    coil_values[4] = False  # relay 2 OFF

    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [0]*100),
        co=ModbusSequentialDataBlock(0, coil_values),
        hr=ModbusSequentialDataBlock(0, hr_values),
        ir=ModbusSequentialDataBlock(0, ir_values),
        zero_mode=True,
    )
    return ModbusServerContext(slaves=store, single=True)


def update_values(context):
    """Cap nhat gia tri sensor mo phong (random)"""
    slave = context[0]
    while True:
        # Random temperature: 20-35 C
        temp = random.randint(2000, 3500)
        slave.setValues(3, 0, [temp])

        # Random humidity: 40-80%
        hum = random.randint(4000, 8000)
        slave.setValues(3, 1, [hum])

        # Random pressure: 1000-1030
        pres = random.randint(1000, 1030)
        slave.setValues(3, 2, [pres])

        # Random light: 0-1000
        light = random.randint(0, 1000)
        slave.setValues(3, 3, [light])

        # Update uptime
        slave.setValues(3, 8, [int(time.time()) & 0xFFFF])

        time.sleep(2)


def main():
    if not HAS_PYMODBUS:
        print("[ERROR] pymodbus chua cai. Chay: pip install pymodbus")
        return

    HOST = "0.0.0.0"
    PORT = 5020

    print("=" * 50)
    print("  Modbus TCP Server - Mau test")
    print(f"  Listening on {HOST}:{PORT}")
    print("=" * 50)
    print()
    print("  Holding Registers:")
    print("    [0] Temperature x100 (25.50 = 2550)")
    print("    [1] Humidity x100 (65.00 = 6500)")
    print("    [2] Pressure (1013 hPa)")
    print("    [3] Light (500 lux)")
    print("    [4] Battery x10 (33.0V = 330)")
    print()
    print("  Input Registers:")
    print("    [0-1] Timestamp")
    print("    [2] Uptime (minutes)")
    print("    [3] Free memory %")
    print()
    print("  Coils:")
    print("    [0-2] Sensor status")
    print("    [3-4] Relay status")
    print()
    print("  Gia tri se tu dong random moi 2 giay.")
    print("  Nhan Ctrl+C de dung.")
    print()

    context = create_store()

    # Thread cap nhat gia tri
    updater = threading.Thread(target=update_values, args=(context,), daemon=True)
    updater.start()

    # Chay server
    StartTcpServer(context=context, address=(HOST, PORT))


if __name__ == "__main__":
    main()
