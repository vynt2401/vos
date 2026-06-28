IoT Gateway - Test tren Windows
================================

Cau truc:
  app/
  ├── main.py              # App chinh (MQTT + Modbus + System + Log)
  ├── modbus_server.py     # Modbus server mau de test
  ├── requirements.txt     # Dependencies
  ├── test_env.py          # Kiem tra moi truong
  ├── install.bat          # Cai dat (Windows)
  └── run.bat              # Chay app (Windows)

Huong dan su dung:
  1. Cai dat dependencies:
     - Double click install.bat
     - Hoac: pip install -r requirements.txt

  2. Kiem tra moi truong:
     python test_env.py

  3. Chay app chinh:
     - Double click run.bat
     - Hoac: python main.py

  4. Test Modbus:
     - Mo terminal 1: python modbus_server.py
     - Mo terminal 2: python main.py
     - Vao tab Modbus, ket noi 127.0.0.1:5020
     - Nhan "Read Holding Registers"

  5. Test MQTT:
     - Vao tab MQTT
     - Broker: test.mosquitto.org, Port: 1883
     - Nhan "Ket noi"
     - Subscribe topic: iot/#
     - Publish tin nhan bat ky

Ghi chu:
  - App chay tren Windows giong het tren Orange Pi
  - Khi deploy len board, chi can copy folder iot_app/ vao rootfs
  - Modbus server chi dung de test, khong can tren board that
