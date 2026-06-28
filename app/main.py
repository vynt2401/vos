#!/usr/bin/env python3
"""
IoT Gateway - Orange Pi Zero H3
Standalone version - test tren Windows/Linux truoc khi deploy len board
Tabs: MQTT | Modbus | System | Log
"""

import sys
import os
import json
import time
import platform
import subprocess
import threading
import socket

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QTabWidget, QWidget,
        QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
        QPushButton, QTextEdit, QGroupBox, QSpinBox,
        QComboBox, QCheckBox, QTableWidget, QTableWidgetItem,
        QHeaderView, QMessageBox, QStatusBar
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QFont, QColor
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False
    print("[ERROR] PyQt5 chua cai. Chay: pip install PyQt5")

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False
    print("[WARN] paho-mqtt chua cai. Chay: pip install paho-mqtt")

try:
    from pymodbus.client import ModbusTcpClient
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False
    print("[WARN] pymodbus chua cai. Chay: pip install pymodbus")


# ============================================================
# MQTT Tab
# ============================================================
class MqttTab(QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # --- Connection ---
        grp_conn = QGroupBox("Ket noi MQTT Broker")
        g1 = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Broker:"))
        self.broker_host = QLineEdit("test.mosquitto.org")
        self.broker_host.setMinimumWidth(200)
        row1.addWidget(self.broker_host)
        row1.addWidget(QLabel("Port:"))
        self.broker_port = QSpinBox()
        self.broker_port.setRange(1, 65535)
        self.broker_port.setValue(1883)
        row1.addWidget(self.broker_port)
        row1.addWidget(QLabel("Client ID:"))
        self.client_id = QLineEdit("iot-gateway-test")
        row1.addWidget(self.client_id)
        row1.addStretch()
        g1.addLayout(row1)

        row2 = QHBoxLayout()
        self.btn_connect = QPushButton("  Ket noi  ")
        self.btn_connect.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_connect.clicked.connect(self._connect)
        self.btn_disconnect = QPushButton("  Ngat  ")
        self.btn_disconnect.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px 15px;")
        self.btn_disconnect.clicked.connect(self._disconnect)
        self.btn_disconnect.setEnabled(False)
        self.lbl_status = QLabel("  Chua ket noi")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 12px;")
        row2.addWidget(self.btn_connect)
        row2.addWidget(self.btn_disconnect)
        row2.addWidget(self.lbl_status)
        row2.addStretch()
        g1.addLayout(row2)

        grp_conn.setLayout(g1)
        layout.addWidget(grp_conn)

        # --- Publish ---
        grp_pub = QGroupBox("Gui tin (Publish)")
        g2 = QVBoxLayout()

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Topic:"))
        self.pub_topic = QLineEdit("iot/sensor/temperature")
        row3.addWidget(self.pub_topic)
        g2.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("Noi dung:"))
        self.pub_msg = QLineEdit('{"temp": 25.5, "humidity": 60.0, "timestamp": ""}')
        self.pub_msg.setMinimumWidth(300)
        row4.addWidget(self.pub_msg)
        self.btn_publish = QPushButton("Gui")
        self.btn_publish.setStyleSheet("background-color: #2196F3; color: white; padding: 5px 15px;")
        self.btn_publish.clicked.connect(self._publish)
        self.btn_publish.setEnabled(False)
        row4.addWidget(self.btn_publish)
        g2.addLayout(row4)

        grp_pub.setLayout(g2)
        layout.addWidget(grp_pub)

        # --- Subscribe ---
        grp_sub = QGroupBox("Nhan tin (Subscribe)")
        g3 = QVBoxLayout()

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("Topic filter:"))
        self.sub_topic = QLineEdit("iot/#")
        row5.addWidget(self.sub_topic)
        self.btn_subscribe = QPushButton("Dang ky")
        self.btn_subscribe.setStyleSheet("background-color: #FF9800; color: white; padding: 5px 15px;")
        self.btn_subscribe.clicked.connect(self._subscribe)
        self.btn_subscribe.setEnabled(False)
        row5.addWidget(self.btn_subscribe)
        self.btn_clear = QPushButton("Xoa log")
        self.btn_clear.clicked.connect(lambda: self.log.clear())
        row5.addWidget(self.btn_clear)
        row5.addStretch()
        g3.addLayout(row5)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        g3.addWidget(self.log)

        grp_sub.setLayout(g3)
        layout.addWidget(grp_sub)

        self.setLayout(layout)

    def _connect(self):
        if not HAS_MQTT:
            self.log.append("[ERROR] paho-mqtt chua cai dat")
            return
        try:
            self.client = mqtt.Client(client_id=self.client_id.text())
            self.client.on_connect = self._on_connect
            self.client.on_message = self._on_message
            self.client.on_disconnect = self._on_disconnect
            self.client.on_log = self._on_log
            self.client.connect_async(self.broker_host.text(), self.broker_port.value(), 60)
            self.client.loop_start()
            self.log.append(f"[INFO] Dang ket noi {self.broker_host.text()}:{self.broker_port.value()}...")
            self.btn_connect.setEnabled(False)
        except Exception as e:
            self.log.append(f"[ERROR] {e}")

    def _disconnect(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        self.connected = False
        self.lbl_status.setText("  Da ngat")
        self.lbl_status.setStyleSheet("color: gray; font-weight: bold; font-size: 12px;")
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_publish.setEnabled(False)
        self.btn_subscribe.setEnabled(False)
        self.log.append("[INFO] Da ngat ket noi")

    def _on_connect(self, client, userdata, flags, rc):
        self.connected = True
        self.lbl_status.setText(f"  Da ket noi (rc={rc})")
        self.lbl_status.setStyleSheet("color: green; font-weight: bold; font-size: 12px;")
        self.btn_connect.setEnabled(False)
        self.btn_disconnect.setEnabled(True)
        self.btn_publish.setEnabled(True)
        self.btn_subscribe.setEnabled(True)
        self.log.append(f"[OK] Ket noi thanh cong (rc={rc})")

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        self.lbl_status.setText("  Mat ket noi")
        self.lbl_status.setStyleSheet("color: red; font-weight: bold; font-size: 12px;")
        self.btn_connect.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_publish.setEnabled(False)
        self.btn_subscribe.setEnabled(False)

    def _on_message(self, client, userdata, msg):
        ts = time.strftime("%H:%M:%S")
        self.log.append(f"[{ts}] {msg.topic}: {msg.payload.decode()}")

    def _on_log(self, client, userdata, level, buf):
        pass

    def _publish(self):
        if self.client and self.connected:
            topic = self.pub_topic.text()
            msg = self.pub_msg.text()
            if not topic or not msg:
                return
            result = self.client.publish(topic, msg)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                ts = time.strftime("%H:%M:%S")
                self.log.append(f"[{ts}] [GUI -> {topic}] {msg}")
            else:
                self.log.append(f"[ERROR] Gui that bai, rc={result.rc}")

    def _subscribe(self):
        if self.client and self.connected:
            topic = self.sub_topic.text()
            if not topic:
                return
            result, mid = self.client.subscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.log.append(f"[OK] Dang ky nhan tin: {topic}")
            else:
                self.log.append(f"[ERROR] Dang ky that bai: rc={result}")


# ============================================================
# Modbus Tab
# ============================================================
class ModbusTab(QWidget):
    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # --- Connection ---
        grp = QGroupBox("Modbus TCP Client")
        g1 = QVBoxLayout()

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("IP:"))
        self.modbus_ip = QLineEdit("127.0.0.1")
        self.modbus_ip.setMinimumWidth(150)
        row1.addWidget(self.modbus_ip)
        row1.addWidget(QLabel("Port:"))
        self.modbus_port = QSpinBox()
        self.modbus_port.setRange(1, 65535)
        self.modbus_port.setValue(5020)
        row1.addWidget(self.modbus_port)
        self.btn_mb_connect = QPushButton("Ket noi")
        self.btn_mb_connect.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px 15px;")
        self.btn_mb_connect.clicked.connect(self._connect)
        self.btn_mb_disconnect = QPushButton("Ngat")
        self.btn_mb_disconnect.setStyleSheet("background-color: #f44336; color: white; padding: 5px 15px;")
        self.btn_mb_disconnect.clicked.connect(self._disconnect)
        self.btn_mb_disconnect.setEnabled(False)
        row1.addWidget(self.btn_mb_connect)
        row1.addWidget(self.btn_mb_disconnect)
        self.lbl_mb_status = QLabel("  Chua ket noi")
        self.lbl_mb_status.setStyleSheet("color: red; font-weight: bold;")
        row1.addWidget(self.lbl_mb_status)
        row1.addStretch()
        g1.addLayout(row1)

        grp.setLayout(g1)
        layout.addWidget(grp)

        # --- Read/Write ---
        grp2 = QGroupBox("Doc du lieu")
        g2 = QVBoxLayout()

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Slave ID:"))
        self.slave_id = QSpinBox()
        self.slave_id.setRange(1, 247)
        self.slave_id.setValue(1)
        row2.addWidget(self.slave_id)
        row2.addWidget(QLabel("Address:"))
        self.reg_addr = QSpinBox()
        self.reg_addr.setRange(0, 65535)
        self.reg_addr.setValue(0)
        row2.addWidget(self.reg_addr)
        row2.addWidget(QLabel("So luong:"))
        self.reg_count = QSpinBox()
        self.reg_count.setRange(1, 125)
        self.reg_count.setValue(10)
        row2.addWidget(self.reg_count)
        g2.addLayout(row2)

        row3 = QHBoxLayout()
        self.btn_read_holding = QPushButton("Read Holding Registers (FC3)")
        self.btn_read_holding.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        self.btn_read_holding.clicked.connect(self._read_holding)
        self.btn_read_holding.setEnabled(False)
        row3.addWidget(self.btn_read_holding)

        self.btn_read_input = QPushButton("Read Input Registers (FC4)")
        self.btn_read_input.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        self.btn_read_input.clicked.connect(self._read_input)
        self.btn_read_input.setEnabled(False)
        row3.addWidget(self.btn_read_input)

        self.btn_read_coils = QPushButton("Read Coils (FC1)")
        self.btn_read_coils.setStyleSheet("background-color: #2196F3; color: white; padding: 5px;")
        self.btn_read_coils.clicked.connect(self._read_coils)
        self.btn_read_coils.setEnabled(False)
        row3.addWidget(self.btn_read_coils)
        g2.addLayout(row3)

        grp2.setLayout(g2)
        layout.addWidget(grp2)

        # --- Results table ---
        grp3 = QGroupBox("Ket qua")
        g3 = QVBoxLayout()
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["Address", "Value (Dec)", "Value (Hex)"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        g3.addWidget(self.result_table)
        grp3.setLayout(g3)
        layout.addWidget(grp3)

        # --- Log ---
        grp4 = QGroupBox("Log")
        g4 = QVBoxLayout()
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(80)
        self.log.setFont(QFont("Consolas", 9))
        g4.addWidget(self.log)

        row4 = QHBoxLayout()
        self.btn_clear_log = QPushButton("Xoa log")
        self.btn_clear_log.clicked.connect(lambda: self.log.clear())
        row4.addWidget(self.btn_clear_log)
        row4.addStretch()
        g4.addLayout(row4)

        grp4.setLayout(g4)
        layout.addWidget(grp4)

        self.setLayout(layout)

    def _connect(self):
        if not HAS_MODBUS:
            self.log.append("[ERROR] pymodbus chua cai dat")
            return
        try:
            self.client = ModbusTcpClient(
                host=self.modbus_ip.text(),
                port=self.modbus_port.value()
            )
            if self.client.connect():
                self.connected = True
                self.lbl_mb_status.setText("  Da ket noi")
                self.lbl_mb_status.setStyleSheet("color: green; font-weight: bold;")
                self.btn_mb_connect.setEnabled(False)
                self.btn_mb_disconnect.setEnabled(True)
                self.btn_read_holding.setEnabled(True)
                self.btn_read_input.setEnabled(True)
                self.btn_read_coils.setEnabled(True)
                self.log.append(f"[OK] Ket noi Modbus TCP {self.modbus_ip.text()}:{self.modbus_port.value()}")
            else:
                self.log.append("[ERROR] Khong the ket noi")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")

    def _disconnect(self):
        if self.client:
            self.client.close()
        self.connected = False
        self.lbl_mb_status.setText("  Da ngat")
        self.lbl_mb_status.setStyleSheet("color: gray; font-weight: bold;")
        self.btn_mb_connect.setEnabled(True)
        self.btn_mb_disconnect.setEnabled(False)
        self.btn_read_holding.setEnabled(False)
        self.btn_read_input.setEnabled(False)
        self.btn_read_coils.setEnabled(False)

    def _read_holding(self):
        self._do_read("holding")

    def _read_input(self):
        self._do_read("input")

    def _do_read(self, reg_type):
        try:
            slave = self.slave_id.value()
            addr = self.reg_addr.value()
            count = self.reg_count.value()

            if reg_type == "holding":
                result = self.client.read_holding_registers(addr, count, slave=slave)
            else:
                result = self.client.read_input_registers(addr, count, slave=slave)

            if result.isError():
                self.log.append(f"[ERROR] Modbus error: {result}")
                return

            data = result.registers
            self.result_table.setRowCount(len(data))
            for i, val in enumerate(data):
                self.result_table.setItem(i, 0, QTableWidgetItem(str(addr + i)))
                self.result_table.setItem(i, 1, QTableWidgetItem(str(val)))
                hex_item = QTableWidgetItem(f"0x{val:04X}")
                hex_item.setForeground(QColor("#0066CC"))
                self.result_table.setItem(i, 2, hex_item)

            self.log.append(f"[OK] Doc {reg_type}: {len(data)} thanh ghi tu address {addr}")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")

    def _read_coils(self):
        try:
            slave = self.slave_id.value()
            addr = self.reg_addr.value()
            count = self.reg_count.value()

            result = self.client.read_coils(addr, count, slave=slave)
            if result.isError():
                self.log.append(f"[ERROR] Modbus error: {result}")
                return

            data = result.bits[:count]
            self.result_table.setRowCount(len(data))
            for i, val in enumerate(data):
                self.result_table.setItem(i, 0, QTableWidgetItem(str(addr + i)))
                status = "ON" if val else "OFF"
                item = QTableWidgetItem(status)
                item.setForeground(QColor("green") if val else QColor("red"))
                self.result_table.setItem(i, 1, item)
                self.result_table.setItem(i, 2, QTableWidgetItem("1" if val else "0"))

            self.log.append(f"[OK] Doc coils: {len(data)} tu address {addr}")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")


# ============================================================
# System Tab
# ============================================================
class SystemTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)
        self._refresh()

    def _init_ui(self):
        layout = QVBoxLayout()

        row = QHBoxLayout()
        btn_refresh = QPushButton("Lam moi")
        btn_refresh.clicked.connect(self._refresh)
        row.addWidget(btn_refresh)
        row.addStretch()
        layout.addLayout(row)

        self.info = QTextEdit()
        self.info.setReadOnly(True)
        self.info.setFont(QFont("Consolas", 10))
        self.info.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        layout.addWidget(self.info)

        self.setLayout(layout)

    def _refresh(self):
        lines = []
        is_windows = platform.system() == "Windows"
        sep = "=" * 45

        lines.append(sep)
        lines.append("  HE THONG - IoT Gateway")
        lines.append(f"  {platform.system()} {platform.release()}")
        lines.append(sep)
        lines.append("")

        # Hostname
        try:
            lines.append(f"Hostname:     {socket.gethostname()}")
        except:
            lines.append("Hostname:     N/A")

        # Uptime
        try:
            if is_windows:
                r = subprocess.run(["powershell", "-Command",
                    "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime"],
                    capture_output=True, text=True, timeout=3)
                lines.append(f"Uptime:       {r.stdout.strip()}")
            else:
                with open("/proc/uptime") as f:
                    up = float(f.read().split()[0])
                    h, m = int(up // 3600), int((up % 3600) // 60)
                    lines.append(f"Uptime:       {h}h {m}m")
        except:
            lines.append("Uptime:       N/A")

        # CPU
        lines.append(f"Platform:     {platform.machine()}")
        lines.append(f"Processor:    {platform.processor() or 'N/A'}")

        # RAM
        try:
            if is_windows:
                r = subprocess.run(["powershell", "-Command",
                    "Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory"],
                    capture_output=True, text=True, timeout=3)
                total = int(r.stdout.strip().split()[-1]) // (1024*1024)
                r2 = subprocess.run(["powershell", "-Command",
                    "$os = Get-CimInstance Win32_OperatingSystem; [math]::Round(($os.TotalVisibleMemorySize - $os.FreePhysicalMemory)/1024)"],
                    capture_output=True, text=True, timeout=3)
                used = int(r2.stdout.strip())
                lines.append(f"RAM:          {used}MB / {total}MB ({used*100//max(total,1)}%)")
            else:
                with open("/proc/meminfo") as f:
                    for line in f:
                        if "MemTotal" in line:
                            total = int(line.split()[1]) // 1024
                        elif "MemAvailable" in line:
                            avail = int(line.split()[1]) // 1024
                    used = total - avail
                    lines.append(f"RAM:          {used}MB / {total}MB ({used*100//max(total,1)}%)")
        except:
            lines.append("RAM:          N/A")

        # CPU Temp (Linux only)
        if not is_windows:
            try:
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    temp = int(f.read().strip()) / 1000
                    lines.append(f"CPU Temp:     {temp:.1f} C")
            except:
                pass

        # Disk
        try:
            if is_windows:
                r = subprocess.run(["powershell", "-Command",
                    "Get-PSDrive C | Select-Object Used,Free"],
                    capture_output=True, text=True, timeout=3)
                lines.append(f"Disk C:       {r.stdout.strip()}")
            else:
                r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
                for line in r.stdout.split("\n")[1:]:
                    if "/" in line:
                        parts = line.split()
                        lines.append(f"Disk:         {parts[2]} / {parts[1]} ({parts[4]})")
                        break
        except:
            pass

        # Network
        lines.append("")
        lines.append("--- MANG ---")
        try:
            if is_windows:
                r = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=3)
                for line in r.stdout.split("\n"):
                    if "IPv4" in line or "adapter" in line.lower():
                        lines.append(f"  {line.strip()}")
            else:
                r = subprocess.run(["ip", "-4", "addr", "show"], capture_output=True, text=True, timeout=2)
                iface = ""
                for line in r.stdout.split("\n"):
                    if line.strip().startswith(("1:", "2:", "3:")):
                        iface = line.split(":")[1].strip()
                    elif "inet " in line and iface:
                        ip = line.strip().split()[1].split("/")[0]
                        lines.append(f"  {iface}: {ip}")
                        iface = ""
        except:
            pass

        # Processes
        try:
            if is_windows:
                r = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=3)
                count = len(r.stdout.strip().split("\n")) - 3
            else:
                r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=2)
                count = len(r.stdout.strip().split("\n")) - 1
            lines.append(f"\nProcesses:    {count}")
        except:
            pass

        lines.append(f"\n{sep}")
        self.info.setText("\n".join(lines))


# ============================================================
# Log Tab
# ============================================================
class LogTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        row = QHBoxLayout()
        btn_dmesg = QPushButton("Xem dmesg (Linux)")
        btn_dmesg.clicked.connect(self._load_dmesg)
        row.addWidget(btn_dmesg)

        btn_event = QPushButton("Xem event log (Windows)")
        btn_event.clicked.connect(self._load_event_log)
        row.addWidget(btn_event)

        btn_clear = QPushButton("Xoa")
        btn_clear.clicked.connect(lambda: self.log.clear())
        row.addWidget(btn_clear)
        row.addStretch()
        layout.addLayout(row)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Consolas", 9))
        self.log.setStyleSheet("background-color: #1e1e1e; color: #cccccc;")
        layout.addWidget(self.log)

        self.setLayout(layout)

    def _load_dmesg(self):
        try:
            r = subprocess.run(["dmesg", "--time-format=iso"], capture_output=True, text=True, timeout=3)
            self.log.setPlainText(r.stdout[-8000:])
        except Exception as e:
            self.log.setPlainText(f"Khong the doc dmesg: {e}")

    def _load_event_log(self):
        try:
            r = subprocess.run(
                ["powershell", "-Command",
                 "Get-EventLog -LogName System -Newest 50 | Format-Table -AutoSize"],
                capture_output=True, text=True, timeout=10
            )
            self.log.setPlainText(r.stdout[:8000])
        except Exception as e:
            self.log.setPlainText(f"Khong the doc event log: {e}")


# ============================================================
# Main Window
# ============================================================
class IotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IoT Gateway - Orange Pi Zero H3 [TEST MODE]")
        self.resize(900, 550)

        tabs = QTabWidget()
        tabs.addTab(MqttTab(), "MQTT")
        tabs.addTab(ModbusTab(), "Modbus")
        tabs.addTab(SystemTab(), "System")
        tabs.addTab(LogTab(), "Log")
        self.setCentralWidget(tabs)

        self.statusBar().showMessage("Test mode - Chay tren may tinh truoc khi deploy len board")
        self.statusBar().setStyleSheet("background-color: #333; color: white; padding: 3px;")


if __name__ == "__main__":
    if not HAS_PYQT5:
        print("ERROR: PyQt5 chua cai dat.")
        print("Chay: pip install PyQt5 paho-mqtt pymodbus")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Dark theme
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.Base, QColor(35, 35, 35))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
    palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, QColor(35, 35, 35))
    app.setPalette(palette)

    win = IotApp()
    win.show()
    sys.exit(app.exec_())
