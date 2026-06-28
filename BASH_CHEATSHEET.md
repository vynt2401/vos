# BASH SYNTAX CHEATSHEET
# Cho Embedded Linux / Buildroot / IoT

# ============================================================
# 1. VARIABLES
# ============================================================

# Gán giá trị (KHÔNG có space)
NAME="OrangePi"
VERSION=1.0
COUNT=100

# Đọc biến
echo $NAME
echo "Hostname: $NAME"
echo "Path: ${HOME}/projects"

# Default value
echo ${UNDEFINED_VAR:-"default value"}     # In "default value" nếu chưa có
UNDEFINED_VAR="now set"
echo ${UNDEFINED_VAR:-"default value"}     # In "now set"

# Command substitution
KERNEL_VERSION=$(uname -r)                 # Linux 6.1.0
BUILD_DATE=$(date +%Y-%m-%d)               # 2026-06-07
FILE_COUNT=$(ls | wc -l)                   # So file trong directory

# String operations
FILE="output/images/sdcard.img"
echo ${#FILE}                               # 27 (length)
echo ${FILE%.img}                           # output/images/sdcard (xóa .img)
echo ${FILE##*/}                            # sdcard.img (chỉ lấy filename)
echo ${FILE%/*}                             # output/images (chỉ lấy directory)

# Array
SERVERS=("test.mosquitto.org" "localhost" "192.168.1.100")
echo ${SERVERS[0]}                          # test.mosquitto.org
echo ${SERVERS[@]}                          # In hết
echo ${#SERVERS[@]}                         # 3 (số phần tử)

# ============================================================
# 2. IF / ELSE
# ============================================================

# If cơ bản
if [ -f "/dev/sda" ]; then
    echo "Thẻ SD tìm thấy: /dev/sda"
elif [ -f "/dev/sdb" ]; then
    echo "Thẻ SD tìm thấy: /dev/sdb"
else
    echo "Không tìm thấy thẻ SD"
fi

# So sánh số
A=10
B=20
if [ $A -lt $B ]; then      # -lt: less than
    echo "$A < $B"
elif [ $A -gt $B ]; then     # -gt: greater than
    echo "$A > $B"
elif [ $A -eq $B ]; then     # -eq: equal
    echo "$A = $B"
else
    echo "$A <= $B"
fi

# So sánh string
if [ "$NAME" = "OrangePi" ]; then
    echo "Đúng board"
elif [ "$NAME" != "RaspberryPi" ]; then
    echo "Không phải RPi"
fi

# Operators tổng hợp:
# -eq, -ne, -lt, -le, -gt, -ge  (số)
# =, !=                          (string)
# -z, -n                         (string rỗng/không rỗng)

# File test
FILE="sdcard.img"
[ -f "$FILE" ] && echo "File tồn tại"
[ ! -f "$FILE" ] && echo "File không tồn tại"
[ -d "build" ] && echo "Directory tồn tại"
[ -r "$FILE" ] && echo "File có thể đọc"
[ -w "$FILE" ] && echo "File có thể ghi"
[ -x "$FILE" ] && echo "File có thể thực thi"
[ -s "$FILE" ] && echo "File không rỗng"

# Logical operators
if [ -f "sdcard.img" ] && [ -d "output" ]; then
    echo "Cả file và directory tồn tại"
fi

if [ ! -f "sdcard.img" ] || [ ! -d "output" ]; then
    echo "Thiếu file hoặc directory"
fi

# ============================================================
# 3. FOR LOOP
# ============================================================

# For với list
for BOARD in "OrangePi" "RaspberryPi" "BeagleBone"; do
    echo "Board: $BOARD"
done

# For với range
for i in $(seq 1 10); do
    echo "Step $i"
done

# Hoặc
for i in {1..10}; do
    echo "Number: $i"
done

# For với file
for FILE in *.img; do
    echo "Image: $FILE"
    ls -lh "$FILE"
done

# For với output command
for PKG in $(ls output/build/ | grep "python"); do
    echo "Python package: $PKG"
done

# ============================================================
# 4. WHILE LOOP
# ============================================================

# While đọc file line by line
while IFS= read -r LINE; do
    echo "Line: $LINE"
done < packages.txt

# While đếm
COUNT=0
while [ $COUNT -lt 5 ]; do
    echo "Count: $COUNT"
    COUNT=$((COUNT + 1))
done

# While true (vô hạn)
while true; do
    echo "Running... $(date)"
    sleep 5
done

# ============================================================
# 5. FUNCTIONS
# ============================================================

# Function cơ bản
build_image() {
    echo "Building image..."
    make -j$(nproc)
    echo "Done!"
}

# Gọi function
build_image

# Function với parameter
flash_sd() {
    local DEVICE=$1
    local IMAGE=$2

    if [ ! -f "$IMAGE" ]; then
        echo "[ERROR] Image không tồn tại: $IMAGE"
        return 1
    fi

    echo "Flashing $IMAGE to $DEVICE..."
    sudo dd if="$IMAGE" of="$DEVICE" bs=1M status=progress conv=fsync
    sync
    echo "[OK] Flashed!"
    return 0
}

# Gọi
flash_sd "/dev/sdb" "output/images/sdcard.img"

# Function với return value
check_rootfs_size() {
    local SIZE=$(stat -c%s "output/images/sdcard.img" 2>/dev/null)
    local MAX=$((256 * 1024 * 1024))  # 256MB

    if [ $SIZE -gt $MAX ]; then
        echo "[WARN] Rootfs quá lớn: $((SIZE / 1024 / 1024))MB"
        return 1
    fi

    echo "[OK] Rootfs size: $((SIZE / 1024 / 1024))MB"
    return 0
}

# ============================================================
# 6. CASE (SWITCH)
# ============================================================

case "$1" in
    start)
        echo "Starting service..."
        systemctl start mosquitto
        ;;
    stop)
        echo "Stopping service..."
        systemctl stop mosquitto
        ;;
    restart)
        $0 stop
        sleep 1
        $0 start
        ;;
    status)
        systemctl status mosquitto
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac

# ============================================================
# 7. REDIRECTION & PIPELINE
# ============================================================

# Output redirect
echo "Build log" > build.log              # Ghi mới (overwrite)
echo " thêm dòng" >> build.log             # Thêm vào cuối (append)

# Input redirect
sort < unsorted.txt > sorted.txt

# Pipe
ls -la | grep ".img"                       # Lọc file .img
ps aux | grep "mosquitto" | grep -v grep  # Tìm process
cat build.log | tail -20                   # 20 dòng cuối
cat build.log | head -10                   # 10 dòng đầu

# Command thay thế
cat build.log | grep "ERROR" | wc -l      # Đếm số lỗi

# Suppress output
make -j$(nproc) > /dev/null 2>&1           # Ẩn hết output
make -j$(nproc) 2>&1 | tee build.log      # Vừa hiện vừa ghi file

# Here document
cat << EOF > config.txt
broker=test.mosquitto.org
port=1883
topic=iot/sensor
EOF

# ============================================================
# 8. STRING OPERATIONS
# ============================================================

STR="Hello World from Orange Pi"

echo ${#STR}                                # 28 (length)
echo ${STR:0:5}                             # Hello (substring từ vị trí 0, độ dài 5)
echo ${STR:6:5}                             # World
echo ${STR/World/Linux}                     # Hello Linux from Orange Pi (thay thế)
echo ${STR,,}                               # hello world from orange pi (lowercase)
echo ${STR^^}                               # HELLO WORLD FROM ORANGE PI (uppercase)

# Check string start/end
FILE="sdcard.img"
if [[ "$FILE" == *.img ]]; then
    echo "Đúng định dạng"
fi
if [[ "$FILE" == output* ]]; then
    echo "Trong thư mục output"
fi

# ============================================================
# 9. NUMERIC OPERATIONS
# ============================================================

# Arithmetic
A=10
B=3
echo $((A + B))        # 13
echo $((A - B))        # 7
echo $((A * B))        # 30
echo $((A / B))        # 3
echo $((A % B))        # 1 (modulo)
echo $((A ** 2))       # 100 (power)

# Increment
COUNT=0
COUNT=$((COUNT + 1))
((COUNT++))
((COUNT += 5))

# Float (dùng bc)
echo "scale=2; 10/3" | bc                 # 3.33
TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
echo "scale=1; $TEMP/1000" | bc           # 45.2

# Compare
[ 10 -gt 5 ] && echo "10 > 5"
[ 10 -lt 20 ] && echo "10 < 20"

# ============================================================
# 10. FINDING FILES & TEXT
# ============================================================

# find
find . -name "*.img"                        # Tìm file .img
find . -name "*.c" -type f                  # Chỉ tìm file
find . -type d -name "buildroot"            # Chỉ tìm directory
find . -size +100M                          # File lớn hơn 100MB
find . -mtime -7                            # File sửa trong 7 ngày
find . -name "*.log" -delete                # Xóa hết file .log

# grep
grep -r "BR2_PACKAGE_PYTHON" .config        # Tìm trong file
grep -rn "TODO" src/ --include="*.py"       # Tìm + hiển thị số dòng
grep -l "mosquitto" *.sh                    # Chỉ hiện tên file
grep -c "ERROR" build.log                   # Đếm số dòng match
grep -v "WARNING" build.log                 # Lọc BỎ dòng chứa WARNING

# sed
sed -i 's/old/new/g' file.txt               # Thay thế trong file
sed -i '10d' file.txt                       # Xóa dòng 10
sed -n '5,10p' file.txt                     # Hiện dòng 5-10

# awk
awk '{print $1}' file.txt                   # In cột đầu tiên
awk -F: '{print $1}' /etc/passwd            # Tùy chọn delimiter
awk '/ERROR/' build.log                     # Tìm dòng chứa ERROR
awk '{sum+=$1} END {print sum}' nums.txt   # Tổng các số

# ============================================================
# 11. PRACTICAL EXAMPLES CHO DỰ ÁN
# ============================================================

# --- Script build ---
#!/bin/bash
set -e                                          # Dừng nếu có lỗi

BUILDROOT="$HOME/projects/buildroot"
IMAGE="$BUILDROOT/output/images/sdcard.img"

echo "=== Build IoT Gateway ==="

cd "$BUILDROOT"

# Clean
make clean

# Config
make orangepi_zero_defconfig

# Build
echo "[1/2] Building..."
make -j$(nproc) 2>&1 | tee build.log

# Check
if [ ! -f "$IMAGE" ]; then
    echo "[ERROR] Build failed!"
    exit 1
fi

SIZE=$(ls -lh "$IMAGE" | awk '{print $5}')
echo "[OK] Image: $IMAGE ($SIZE)"

# --- Script flash ---
#!/bin/bash
set -e

DEVICE="${1:?Usage: $0 /dev/sdX}"
IMAGE="output/images/sdcard.img"

if [ ! -f "$IMAGE" ]; then
    echo "[ERROR] Image not found: $IMAGE"
    exit 1
fi

echo "Flash $IMAGE -> $DEVICE"
read -p "Confirm (YES): " CONFIRM
[ "$CONFIRM" = "YES" ] || exit 0

sudo dd if="$IMAGE" of="$DEVICE" bs=1M status=progress conv=fsync
sync
echo "[OK] Done!"

# --- Auto find SD card ---
#!/bin/bash
echo "Thẻ SD đang cắm:"
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT | grep "disk"

for DEV in /dev/sd[b-c]; do
    if [ -b "$DEV" ]; then
        SIZE=$(lsblk -bno SIZE "$DEV" 2>/dev/null)
        if [ "$SIZE" -gt 8000000000 ] && [ "$SIZE" -lt 68000000000 ]; then
            echo "Found SD: $DEV ($((SIZE/1024/1024/1024))GB)"
            break
        fi
    fi
done

# --- Backup SD card ---
#!/bin/bash
DEVICE="${1:?Usage: $0 /dev/sdX}"
BACKUP="backup_$(date +%Y%m%d_%H%M%S).img"

echo "Backing up $DEVICE -> $BACKUP"
sudo dd if="$DEVICE" of="$BACKUP" bs=1M status=progress
sync
echo "[OK] Backup: $BACKUP ($(( $(stat -c%s "$BACKUP") / 1024 / 1024 ))MB)"

# --- Benchmark script ---
#!/bin/bash
echo "=== Benchmark ==="
echo "Kernel:   $(uname -r)"
echo "Arch:     $(uname -m)"

# Boot time
if [ -f /proc/uptime ]; then
    UP=$(cat /proc/uptime | awk '{print $1}')
    echo "Uptime:   ${UP}s"
fi

# RAM
if [ -f /proc/meminfo ]; then
    TOTAL=$(awk '/MemTotal/{print $2}' /proc/meminfo)
    AVAIL=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    USED=$(( (TOTAL - AVAIL) / 1024 ))
    TOT=$(( TOTAL / 1024 ))
    echo "RAM:      ${USED}MB / ${TOT}MB ($(( USED * 100 / TOT ))%)"
fi

# Temp
if [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    echo "CPU Temp: $(echo "scale=1; $TEMP/1000" | bc)°C"
fi

# Image size
if [ -f output/images/sdcard.img ]; then
    SIZE=$(ls -lh output/images/sdcard.img | awk '{print $5}')
    echo "Image:    $SIZE"
fi

# ============================================================
# 12. COMMON COMMANDS
# ============================================================

# File operations
cp source dest                # Copy
cp -r dir1 dir2               # Copy directory
mv old new                    # Move/Rename
rm file                       # Delete
rm -rf directory              # Force delete directory
mkdir -p path/to/dir          # Tạo directory (recursive)
touch file.txt                # Tạo file trống
chmod +x script.sh            # Cho phép thực thi
chmod 755 script.sh           # rwxr-xr-x

# System info
uname -a                      # Thông tin kernel
hostname                      # Tên máy
date                          # Thời gian
uptime                        # Thời gian chạy
free -m                       # RAM usage
df -h                         # Disk usage
du -sh directory              # Directory size
lsblk                         # Danh sách block devices
lscpu                         # CPU info

# Process
ps aux                        # Tất cả processes
ps aux | grep name           # Tìm process
kill PID                      # Kill process
killall name                  # Kill by name
top                           # Real-time monitor

# Network
ip addr show                  # IP addresses
ip route show                 # Routing table
ping -c 3 8.8.8.8            # Test connection
curl http://example.com       # HTTP request
wget URL                      # Download
netstat -tlnp                 # Listening ports

# Service
systemctl start service       # Start
systemctl stop service        # Stop
systemctl restart service     # Restart
systemctl status service      # Status
systemctl enable service      # Auto-start on boot

# ============================================================
# 13. SHEBANG & SCRIPT STRUCTURE
# ============================================================

#!/bin/bash
# Mô tả script
# Tác giả: ntv
# Ngày: 2026-06-07

# Exit on error
set -e

# Trap errors
trap 'echo "Error on line $LINENO"; exit 1' ERR

# Define variables
BUILDROOT="$HOME/projects/buildroot"
LOG_FILE="/tmp/build.log"

# Parse arguments
DEVICE="${1:-/dev/sdb}"
VERBOSE="${2:-false}"

# Functions
log() {
    echo "[$(date +%H:%M:%S)] $1"
}

check_deps() {
    for CMD in gcc make cmake; do
        if ! command -v $CMD &> /dev/null; then
            echo "[ERROR] $CMD not found"
            exit 1
        fi
    done
}

# Main
main() {
    log "Starting build..."
    check_deps
    cd "$BUILDROOT"
    make -j$(nproc) 2>&1 | tee "$LOG_FILE"
    log "Build complete!"
}

main "$@"
