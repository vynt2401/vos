# Custom Linux Distro cho IoT Gateway

Xây dựng hệ điều hành Linux nhúng tùy chỉnh dành cho **Orange Pi Zero H3** (ARMv7) và **VMware** (x86_64 có GUI), phục vụ làm IoT Gateway.

## Công nghệ sử dụng

| Thành phần       | Công nghệ                                                        |
|------------------|------------------------------------------------------------------|
| Build system     | **Buildroot 2024.02** (thay vì Yocto — nhẹ hơn, build nhanh hơn) |
| Toolchain        | Buildroot internal toolchain (armv7-a, hard-float, C++)          |
| Kernel           | Linux mainline 6.6.3 + sunxi defconfig                           |
| Bootloader       | U-Boot mainline 2023.10                                          |
| GUI stack        | **X11R7 + Openbox** (~30MB RAM)                                  |
| Ngôn ngữ         | Python 3 (PyQt5) / C++ (Qt5)                                     |
| IoT protocols    | **MQTT** (Mosquitto), **Modbus TCP**                             |
| Rootfs           | ext4 (256MB ARM / 512MB x86)                                     | 

## Tính năng nổi bật

- **Custom rootfs** siêu nhẹ: image chỉ **61–150 MB** (Armbian mặc định ~1.2 GB — cải thiện 8–20x)
- **RAM idle chỉ 30–45 MB** (so với 110 MB của Armbian — tiết kiệm 60–70%)
- **Boot time 5–8s** (Armbian ~18s)
- **IoT Gateway app** với 4 tab: MQTT Client, Modbus Scanner, System Monitor, Log Viewer
- Hỗ trợ cả Python PyQt5 và C++ Qt5 (cross-platform)
- Kernel size chỉ **3–5 MB** (Armbian ~8 MB)

## Cấu trúc thư mục

```
FINAL_PROJECT/
├── app/                          # Source code IoT Gateway
│   ├── main.py                   # Python PyQt5 (MQTT + Modbus + System + Log)
│   ├── modbus_server.py          # Modbus TCP test server
│   ├── cpp-qt5/                  # C++ Qt5 version (cross-platform)
│   └── requirements.txt
├── buildroot/                    # Buildroot 2024.02 (full source tree)
│   ├── .config                   # Build config cho Orange Pi Zero
│   ├── configs/vm_gui_defconfig  # Build config cho VMware x86_64
│   ├── board/custom/overlay/     # Rootfs overlay (autostart, .xinitrc, iot_app)
│   ├── package/libffi/           # (đã patch GCC 14 compatibility)
│   ├── dl/                       # Source tarballs đã download
│   └── output/                   # Build output (target, host, images)
├── op/                           # Output image
│   └── sdcard.img
├── HUONG_DAN.md                  # Hướng dẫn chi tiết (660 dòng)
└── README.md                     # File này
```

## Cách build

### Yêu cầu: Windows + WSL2 Ubuntu 22.04

```powershell
# PowerShell admin
wsl --install -d Ubuntu-22.04
wsl --set-default-version 2
```

```bash
# Trong WSL Ubuntu
sudo apt update && sudo apt install -y \
  build-essential git wget cpio unzip rsync bc file \
  libncurses-dev libncursesw5-dev libtinfo-dev \
  bison flex libssl-dev libelf-dev \
  device-tree-compiler u-boot-tools python3 python3-pip \
  python3-venv qemu-user-static minicom screen curl pkg-config
```

### Build cho Orange Pi Zero (ARM — chạy trên thẻ SD)

```bash
git clone https://github.com/buildroot/buildroot.git ~/projects/buildroot
cd ~/projects/buildroot
git checkout 2024.02
make orangepi_zero_defconfig
make menuconfig  # bật C++ toolchain, Python 3, Openbox, X11, Mosquitto
make -j$(nproc) 2>&1 | tee build.log
```

### Build cho VMware (x86_64 — có GUI)

```bash
cd ~/projects/buildroot
make vm_gui_defconfig
make -j$(nproc) 2>&1 | tee build.log
# Output: output/images/rootfs.ext4 -> dùng làm ổ cứng cho VM
```

### Fix lỗi GCC 14 trên WSL

Buildroot 2024.02 + libffi 3.4.4 không tương thích GCC 14 (lỗi `implicit-function-declaration`). Đã fix bằng patch tại `package/libffi/0004-Fix-GCC-14-implicit-function-declaration-in-tramp.c.patch`.

```bash
# Nếu chưa có patch:
cp /path/to/patch ~/projects/buildroot/package/libffi/
rm -rf output/build/host-libffi-3.4.4
make host-libffi
```

## Flash và chạy

```bash
# Flash lên thẻ SD
sudo dd if=~/projects/buildroot/output/images/sdcard.img of=/dev/sdX bs=1M status=progress conv=fsync
sync

# Kết nối serial (cáp CP2102)
sudo minicom -D /dev/ttyUSB0 -b 115200

# Đăng nhập
# Username: root | Password: (đã set trong menuconfig)
```

## App IoT Gateway

Gồm 4 tab chức năng:

| Tab          | Chức năng                                    |
|--------------|----------------------------------------------|
| **MQTT**     | Kết nối broker, publish/subscribe topic      |
| **Modbus**   | Đọc holding/input registers, coils qua TCP   |
| **System**   | Monitor CPU, RAM, disk, network, temperature |
| **Log**      | Xem dmesg / system log                       |

Chạy tự động sau boot 3 giây nhờ openbox autostart.

## Benchmark dự kiến

| Metric       | Armbian | Custom Buildroot | Cải thiện |
|--------------|---------|------------------|-----------|
| Image size   | 1.2 GB  | 61–150 MB        | 8–20x     |
| RAM idle     | 110 MB  | 30–45 MB         | 60–70%    |
| Boot time    | 18s     | 5–8s             | 55–70%    |
| Kernel size  | 8 MB    | 3–5 MB           | 40–60%    |

## Câu hỏi bảo vệ thường gặp

| Câu hỏi                      | Trả lời                                             |
|------------------------------|-----------------------------------------------------|
| Vì sao chọn Buildroot?       | Nhẹ, nhanh, phù hợp scope đồ án                     |
| Boot time cải thiện nhờ đâu? | Tắt service không cần, kernel tối ưu, không systemd |
| Sao không dùng Armbian?      | Custom rootfs, giảm size 90%, kiểm soát toàn diện   |
| Hướng phát triển?            | OTA update, secure boot, LoRaWAN, Zigbee gateway    |
