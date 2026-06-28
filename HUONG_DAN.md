# HƯỚNG DẪN XÂY DỰNG CUSTOM LINUX DISTRO CHO IoT
**Target: Orange Pi Zero H3 (Allwinner H3) — Đồ án tốt nghiệp**

---

## 0. QUYẾT ĐỊNH CỐT LÕI

| Lựa chọn | Quyết định | Lý do |
|----------|-----------|-------|
| Build system | **Buildroot 2024.02** | Yocto mất 4–8h/build, learning curve cao |
| Toolchain | **Buildroot toolchain** (armv7-a, hard-float, C++ support) | Tương thích openbox, PyQt5 |
| GUI stack | **Openbox + X11** | RAM ~30MB, nhẹ cho H3 |
| Ngôn ngữ app IoT | **Python 3** | Code nhanh, demo đẹp |
| Rootfs | **ext4** | Đơn giản, ổn định |
| Kernel | **sunxi mainline** | Ổn định, support H3 |
| Bootloader | **U-Boot mainline** | Chuẩn công nghiệp |

---

## 1. YÊU CẦU MÔI TRƯỜNG

### Host: Windows + WSL2 Ubuntu

```powershell
# PowerShell admin
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
```

### Cài gói build (trong WSL)
```bash
sudo apt update && sudo apt install -y \
  build-essential git wget cpio unzip rsync bc file \
  libncurses-dev libncursesw5-dev libtinfo-dev \
  bison flex libssl-dev libelf-dev \
  device-tree-compiler u-boot-tools python3 python3-pip \
  python3-venv qemu-user-static minicom screen curl pkg-config
```

### Target board
- Orange Pi Zero H3 (256/512 MB RAM, ARMv7 quad-core A7)
- Thẻ microSD **16 GB** (Samsung/Sandisk Class 10)
- **Cáp USB-to-Serial 3.3V CP2102** (~50k VND) — bắt buộc debug
- Nguồn 5V/2A ổn định

---

## 2. CÀI ĐẶT BUILDROOT

### Clone vào WSL native filesystem (KHÔNG dùng /mnt/d/)
```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/buildroot/buildroot.git
cd buildroot
git checkout 2024.02
```

### Fix check-lxdialog.sh (gcc 14 tương thích)
```bash
cd support/kconfig/lxdialog
sed -i 's|#include CURSES_LOC|#include <ncurses.h>|' check-lxdialog.sh
sed -i 's|main() {}|int main() { return 0; }|' check-lxdialog.sh
cd ~/projects/buildroot
```

### Fix host-libffi (gcc 14 tương thích)
```bash
# Sau khi build lần đầu bị lỗi host-libffi:
cd ~/projects/buildroot/output/build/host-libffi-3.4.4
sed -n '248,256p' src/tramp.c   # Xác nhận cấu trúc file
# Chèn extern declaration sau #if defined (__linux__) (line ~252)
sed -i '/#if defined (__linux__) || defined (__CYGWIN__)/a\extern int open_temp_exec_file (void);' src/tramp.c
# Xóa stamp để build lại
rm -f .stamp_built .stamp_configured
cd ~/projects/buildroot
make -j$(nproc) 2>&1 | tee build.log
```

---

## 3. CẤU HÌNH BUILDROOT

### Build lần 1: Boot cơ bản (Tuần 1)
```bash
cd ~/projects/buildroot
make orangepi_zero_defconfig
make menuconfig
```

**Mục cần bật trong menuconfig:**

#### Target options
```
Target Architecture → ARM (little endian)
Target Architecture Variant → cortex-a7
Target ABI → hard-float (gnueabihf)
```

#### Toolchain → BẮT BUỘC bật C++
```
Toolchain type → Buildroot toolchain
[*] Enable C++ support
[*] Enable wchar support
```

#### System configuration
```
(custom-iot) System hostname
Root password → (mật khẩu bạn chọn)
[*] Enable root login with password
[*] remount root filesystem read-write during boot
```

#### Target packages → Networking applications
```
[*] dropbear
```

#### Target packages → Shell and utilities
```
[*] bash
```

#### Filesystem images
```
[*] ext4
[*] tar the root filesystem
```

Save → Exit.

```bash
make savedefconfig
make -j$(nproc) 2>&1 | tee build.log
```

**Build lần đầu: ~30–60 phút.**

### Build lần 2: Thêm GUI + IoT (Tuần 2+3)
```bash
cd ~/projects/buildroot
make menuconfig
```

#### Toolchain (kiểm tra lại)
```
Toolchain →
  [*] Enable C++ support     ← BẮT BUỘC có
  [*] Enable wchar support   ← BẮT BUỘC có
```

#### Target packages → Interpreter languages and scripting
```
[*] python3
```

#### Target packages → Networking applications
```
[*] mosquitto
[*] mosquitto-client
```

#### Target packages → Libraries
```
Python 3 →
  [*] python3-paho-mqtt      (nếu có)
  
  [*] libmodbus
  [*] libcoap
```

#### Target packages → Graphic libraries and applications
```
[*] X.org X Window System →
  X11R7 servers →
    [*] xorg-server
  
  X window managers →
    [*] openbox              (cần C++ toolchain)
    [*] fluxbox              (backup nếu openbox lỗi)
  
  X applications →
    [*] xterm
```

#### Target packages → Fonts, cursors, icons, sounds and themes
```
[*] font-dejavu
```

#### Target packages → Hardware handling
```
[*] evtest                   (test input devices)
```

```bash
make savedefconfig
make -j$(nproc) 2>&1 | tee build.log
```

**Build lần 2: ~1.5–2h.**

### Xác nhận packages đã có trong rootfs
```bash
# Kiểm tra
ls ~/projects/buildroot/output/target/usr/bin/python3*
ls ~/projects/buildroot/output/target/usr/bin/Xorg
ls ~/projects/buildroot/output/target/usr/bin/openbox
ls ~/projects/buildroot/output/target/usr/sbin/mosquitto*
```

---

## 4. OVERLAY + AUTOSTART

### Tạo cấu trúc overlay
```bash
mkdir -p ~/projects/buildroot/board/custom_orangepi/overlay/etc/openbox
mkdir -p ~/projects/buildroot/board/custom_orangepi/overlay/root/iot_app
```

### File overlay: autostart Openbox
```bash
cat > ~/projects/buildroot/board/custom_orangepi/overlay/etc/openbox/autostart << 'EOF'
#!/bin/sh
# Chạy app IoT khi boot
(sleep 3 && python3 /root/iot_app/main.py) &
EOF
chmod +x ~/projects/buildroot/board/custom_orangepi/overlay/etc/openbox/autostart
```

### File overlay: .xinitrc
```bash
cat > ~/projects/buildroot/board/custom_orangepi/overlay/root/.xinitrc << 'EOF'
#!/bin/sh
exec openbox-session
EOF
chmod +x ~/projects/buildroot/board/custom_orangepi/overlay/root/.xinitrc
```

### File overlay: S99iotapp (init script)
```bash
cat > ~/projects/buildroot/board/custom_orangepi/overlay/etc/init.d/S99iotapp << 'EOF'
#!/bin/sh
DAEMON="/root/iot_app/main.py"
LOG="/var/log/iotapp.log"

case "$1" in
  start)
    echo "Starting IoT App..."
    [ -z "$DISPLAY" ] && export DISPLAY=:0
    startx /root/.xinitrc >> "$LOG" 2>&1 &
    ;;
  stop)
    pkill -f "iot_app/main.py"
    ;;
  restart) "$0" stop; sleep 1; "$0" start ;;
esac
EOF
chmod +x ~/projects/buildroot/board/custom_orangepi/overlay/etc/init.d/S99iotapp
```

### Kích hoạt overlay trong Buildroot
```bash
cd ~/projects/buildroot
echo 'BR2_ROOTFS_OVERLAY="board/custom_orangepi/overlay"' >> .config
```

Hoặc qua menuconfig:
```
System configuration →
  Root filesystem overlay directories →
    (board/custom_orangepi/overlay) Root filesystem overlay directories
```

---

## 5. APP IoT MẪU

### `iot-app/main.py`
```python
#!/usr/bin/env python3
import sys
import os
import json
import time
import subprocess

try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget,
                                  QWidget, QVBoxLayout, QHBoxLayout,
                                  QLabel, QLineEdit, QPushButton,
                                  QTextEdit, QComboBox, QGroupBox)
    from PyQt5.QtCore import Qt, QTimer
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False


class MqttTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Broker config
        grp = QGroupBox("MQTT Broker")
        g = QVBoxLayout()
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Broker:"))
        self.broker = QLineEdit("test.mosquitto.org")
        h1.addWidget(self.broker)
        h1.addWidget(QLabel("Port:"))
        self.port = QLineEdit("1883")
        h1.addWidget(self.port)
        g.addLayout(h1)

        h2 = QHBoxLayout()
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.connect_broker)
        h2.addWidget(self.btn_connect)
        self.btn_disconnect = QPushButton("Disconnect")
        self.btn_disconnect.clicked.connect(self.disconnect_broker)
        h2.addWidget(self.btn_disconnect)
        self.status = QLabel("Disconnected")
        h2.addWidget(self.status)
        g.addLayout(h2)
        grp.setLayout(g)
        layout.addWidget(grp)

        # Publish
        grp2 = QGroupBox("Publish")
        g2 = QVBoxLayout()
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("Topic:"))
        self.pub_topic = QLineEdit("iot/test")
        h3.addWidget(self.pub_topic)
        g2.addLayout(h3)
        h4 = QHBoxLayout()
        h4.addWidget(QLabel("Message:"))
        self.pub_msg = QLineEdit("Hello from Orange Pi")
        h4.addWidget(self.pub_msg)
        self.btn_publish = QPushButton("Publish")
        self.btn_publish.clicked.connect(self.publish_msg)
        h4.addWidget(self.btn_publish)
        g2.addLayout(h4)
        grp2.setLayout(g2)
        layout.addWidget(grp2)

        # Subscribe
        grp3 = QGroupBox("Subscribe")
        g3 = QVBoxLayout()
        h5 = QHBoxLayout()
        h5.addWidget(QLabel("Topic:"))
        self.sub_topic = QLineEdit("iot/#")
        h5.addWidget(self.sub_topic)
        self.btn_subscribe = QPushButton("Subscribe")
        self.btn_subscribe.clicked.connect(self.subscribe_topic)
        h5.addWidget(self.btn_subscribe)
        g3.addLayout(h5)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        g3.addWidget(self.log)
        grp3.setLayout(g3)
        layout.addWidget(grp3)

        self.setLayout(layout)
        self.client = None

    def connect_broker(self):
        if not HAS_MQTT:
            self.log.append("[ERROR] paho-mqtt not installed")
            return
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        try:
            self.client.connect(self.broker.text(), int(self.port.text()))
            self.client.loop_start()
            self.status.setText("Connected")
            self.log.append(f"[INFO] Connecting to {self.broker.text()}...")
        except Exception as e:
            self.log.append(f"[ERROR] {e}")

    def disconnect_broker(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.status.setText("Disconnected")
            self.log.append("[INFO] Disconnected")

    def on_connect(self, client, userdata, flags, rc):
        self.log.append(f"[INFO] Connected with result code {rc}")

    def on_message(self, client, userdata, msg):
        self.log.append(f"[RECV] {msg.topic}: {msg.payload.decode()}")

    def publish_msg(self):
        if self.client:
            self.client.publish(self.pub_topic.text(), self.pub_msg.text())
            self.log.append(f"[SEND] {self.pub_topic.text()}: {self.pub_msg.text()}")

    def subscribe_topic(self):
        if self.client:
            self.client.subscribe(self.sub_topic.text())
            self.log.append(f"[INFO] Subscribed to {self.sub_topic.text()}")


class SystemTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.info = QLabel("Loading system info...")
        self.info.setAlignment(Qt.AlignTop)
        self.info.setWordWrap(True)
        layout.addWidget(self.info)

        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh)
        layout.addWidget(btn_refresh)

        self.setLayout(layout)
        self.refresh()

    def refresh(self):
        info = []
        try:
            with open("/proc/uptime") as f:
                uptime = float(f.read().split()[0])
                info.append(f"Uptime: {int(uptime//3600)}h {int((uptime%3600)//60)}m")
        except: pass
        try:
            with open("/proc/loadavg") as f:
                info.append(f"Load: {f.read().strip()}")
        except: pass
        try:
            r = subprocess.run(["free", "-m"], capture_output=True, text=True)
            info.append(f"Memory:\n{r.stdout}")
        except: pass
        try:
            with open("/sys/class/thermal/thermal_zone0/temp") as f:
                temp = int(f.read().strip()) / 1000
                info.append(f"CPU Temp: {temp:.1f}°C")
        except: pass
        try:
            r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
            info.append(f"Disk:\n{r.stdout}")
        except: pass
        self.info.setText("\n".join(info))


class IotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IoT Gateway - Orange Pi Zero H3")
        self.resize(800, 480)
        tabs = QTabWidget()
        tabs.addTab(MqttTab(), "MQTT")
        tabs.addTab(SystemTab(), "System")
        self.setCentralWidget(tabs)


if __name__ == "__main__":
    if not HAS_PYQT5:
        print("PyQt5 not available. Running in text mode.")
        while True:
            print(f"[{time.strftime('%H:%M:%S')}] IoT Gateway running...")
            time.sleep(10)
    else:
        app = QApplication(sys.argv)
        w = IotApp()
        w.showFullScreen()
        sys.exit(app.exec_())
```

---

## 6. FLASH SD & BOOT

```bash
# Xác định thẻ SD
lsblk
# Tìm /dev/sdX (ví dụ: /dev/sdb)

# Flash
sudo dd if=~/projects/buildroot/output/images/sdcard.img of=/dev/sdX bs=1M status=progress conv=fsync
sync

# Xem serial (cắm cáp CP2102)
sudo minicom -D /dev/ttyUSB0 -b 115200
```

### Đăng nhập
```
Username: root
Password: (mật khẩu đã set trong menuconfig)
```

### Kiểm tra
```bash
# Network
ip addr show

# SSH từ Windows
ssh root@<ip-address>

# Kiểm tra Python
python3 --version

# Kiểm tra mosquitto
mosquitto_pub -h test.mosquitto.org -t "test" -m "hello"
```

---

## 7. LỖI THƯỜNG GẶP & CÁCH FIX

| # | Lỗi | Nguyên nhân | Fix |
|---|------|------------|-----|
| 1 | `make menuconfig` ncurses not found trên `/mnt/d/` | WSL Windows filesystem | Copy buildroot về `~/projects/` |
| 2 | `check-lxdialog.sh` "Unable to find ncurses" | Script không truyền `-DCURSES_LOC`, `main() {}` lỗi gcc 14 | `sed` sửa script (xem mục 2) |
| 3 | `PATH contains spaces/TABs` | WSL Windows PATH | `export PATH=/usr/local/sbin:...` |
| 4 | `host-libffi`: implicit declaration | libffi 3.4.4 không compat gcc 14 | Thêm `extern int open_temp_exec_file(void)` vào `tramp.c` |
| 5 | `openbox needs C++ toolchain` | Toolchain chưa bật C++ | `Target options → Toolchain → [*] Enable C++ support` |
| 6 | `harfbuzz: Unknown compiler g++` | Thiếu g++ cross-compiler | Bật C++ toolchain → `make toolchain-rebuild` → rebuild |
| 7 | Image quá nhỏ, không có X11/openbox | Chưa bật packages GUI | `make menuconfig` → bật X.org, openbox, font-dejavu |

---

## 8. LỘ TRÌNH 4 TUẦN

### TUẦN 1 ✅ (HOÀN THÀNH)
- [x] Cài WSL2 + Ubuntu
- [x] Clone Buildroot 2024.02
- [x] Fix check-lxdialog.sh (gcc 14)
- [x] Fix host-libffi (gcc 14)
- [x] Build image 61 MB thành công
- [ ] Flash SD + boot Orange Pi
- [ ] SSH vào board

### TUẦN 2 (ĐANG LÀM)
- [ ] Bật C++ toolchain
- [ ] Bật X11 + Openbox + Python3
- [ ] Build lại image có GUI (~100–150 MB)
- [ ] Overlay autostart
- [ ] Test GUI boot lên

### TUẦN 3
- [ ] Viết app IoT (MQTT tab, System tab)
- [ ] Flash overlay + app vào rootfs
- [ ] Demo MQTT kết nối test.mosquitto.org
- [ ] Demo Modbus / CoAP (nếu kịp)

### TUẦN 4
- [ ] Đo benchmark (boot time, RAM, image size, CPU temp)
- [ ] Viết script flash + backup
- [ ] Viết báo cáo đồ án
- [ ] Chuẩn bị slide + demo

---

## 9. CẤU TRÚC DỰ ÁN

```
final-project/
├── HUONG_DAN.md                    # file này
├── docs/
│   ├── bao-cao.pdf
│   └── user-manual.md
├── board/custom_orangepi/
│   └── overlay/
│       ├── etc/
│       │   ├── openbox/autostart
│       │   └── init.d/S99iotapp
│       └── root/
│           ├── .xinitrc
│           └── iot_app/
│               └── main.py
├── iot-app/                        # source code Python
│   └── main.py
└── scripts/
    ├── build.sh
    ├── flash.sh
    └── benchmark.sh
```

---

## 10. ĐO BENCHMARK (cho báo cáo)

```bash
# Boot time (từ serial log)
# Xem dòng "Run /init as init process" — tính từ power-on

# RAM
free -m

# Image size
ls -lh output/images/sdcard.img

# CPU temp
cat /sys/class/thermal/thermal_zone0/temp   # chia 1000 = °C

# Disk
df -h /
```

Mẫu bảng benchmark:
| Metric | Armbian mặc định | Custom Buildroot | Cải thiện |
|--------|-----------------|------------------|-----------|
| Image size | 1.2 GB | 61–150 MB | 8–20x nhẹ hơn |
| RAM idle | 110 MB | 30–45 MB | 60–70% |
| Boot time | 18s | 5–8s | 55–70% |
| Kernel size | 8 MB | 3–5 MB | 40–60% |

---

## 11. CÂU HỎI GIÁM KHẢO HAY HỎI

- **"Vì sao chọn Buildroot?"** → nhẹ, nhanh, phù hợp scope đồ án, 1 tháng đủ
- **"Boot time cải thiện nhờ đâu?"** → tắt service, kernel tối ưu, không systemd phức tạp
- **"Làm sao update firmware OTA?"** → phân tích: A/B partition, SWUpdate, RAUC
- **"Khác gì với Yocto?"** → Buildroot đơn giản hơn, không SDK generator, không BSP layer
- **"Tại sao không dùng Armbian/Raspbian?"** → custom được rootfs, giảm size, kiểm soát toàn diện
- **"Hướng phát triển?"** → OTA update, secure boot, LoRaWAN, Zigbee gateway

---

## 12. CHECKLIST TRƯỚC BÁO CÁO 1 TUẦN

- [ ] Image build reproducible (`make clean && make`)
- [ ] Script flash tự động
- [ ] Demo chạy ổn định 5 phút không crash
- [ ] Đo xong benchmark, có bảng so sánh
- [ ] Screenshot GUI trên board (dùng `fbgrab` hoặc máy ảnh)
- [ ] Video demo 2–3 phút (backup nếu demo trực tiếp lỗi)
- [ ] Báo cáo PDF, đánh số trang, mục lục
- [ ] Slide PPT 15–20 trang
- [ ] Tập demo 1 lần, đo thời gian (< 10 phút)
- [ ] Mang theo: laptop, thẻ SD backup, cáp serial, adapter nguồn

---

## 13. TÀI LIỆU THAM KHẢO

- Buildroot manual: https://buildroot.org/downloads/manual/manual.html
- Allwinner H3: https://linux-sunxi.org/H3
- Orange Pi Zero: http://www.orangepi.org/html/hardWare/computerInterfaceZone.html
- U-Boot: https://u-boot.readthedocs.io/
- Device Tree: https://devicetree-specification.readthedocs.io/
- MQTT: https://mosquitto.org/
- Modbus: https://libmodbus.org/
- PyQt5: https://www.pythonguis.com/pyqt5-tutorial/
