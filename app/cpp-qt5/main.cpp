/*
 * IoT Gateway - C++ Qt5
 * Chay tren ca Windows va Linux
 */

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
#endif

#include <QApplication>
#include <QMainWindow>
#include <QTabWidget>
#include <QWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QLabel>
#include <QLineEdit>
#include <QPushButton>
#include <QTextEdit>
#include <QGroupBox>
#include <QSpinBox>
#include <QTableWidget>
#include <QHeaderView>
#include <QTimer>
#include <QTcpSocket>
#include <QDateTime>
#include <QProcess>
#include <QFile>
#include <QDir>
#include <QNetworkInterface>
#include <QStatusBar>
#include <QFont>
#include <QPalette>
#include <QColor>

// ============================================================
// MQTT Tab
// ============================================================
class MqttTab : public QWidget {
    Q_OBJECT
public:
    MqttTab(QWidget *parent = nullptr) : QWidget(parent) {
        auto *layout = new QVBoxLayout(this);

        auto *connBox = new QGroupBox("Ket noi MQTT Broker");
        auto *g1 = new QVBoxLayout();
        auto *r1 = new QHBoxLayout();
        r1->addWidget(new QLabel("Broker:"));
        m_host = new QLineEdit("test.mosquitto.org");
        m_host->setMinimumWidth(200);
        r1->addWidget(m_host);
        r1->addWidget(new QLabel("Port:"));
        m_port = new QSpinBox();
        m_port->setRange(1, 65535);
        m_port->setValue(1883);
        r1->addWidget(m_port);
        r1->addStretch();
        g1->addLayout(r1);

        auto *r2 = new QHBoxLayout();
        m_btnConn = new QPushButton("Ket noi");
        m_btnConn->setStyleSheet("background-color:#4CAF50;color:white;font-weight:bold;padding:5px 15px;");
        m_btnDisconn = new QPushButton("Ngat");
        m_btnDisconn->setStyleSheet("background-color:#f44336;color:white;font-weight:bold;padding:5px 15px;");
        m_btnDisconn->setEnabled(false);
        m_status = new QLabel("  Chua ket noi");
        m_status->setStyleSheet("color:red;font-weight:bold;");
        r2->addWidget(m_btnConn);
        r2->addWidget(m_btnDisconn);
        r2->addWidget(m_status);
        r2->addStretch();
        g1->addLayout(r2);
        connBox->setLayout(g1);
        layout->addWidget(connBox);

        auto *pubBox = new QGroupBox("Gui tin (Publish)");
        auto *g2 = new QVBoxLayout();
        auto *r3 = new QHBoxLayout();
        r3->addWidget(new QLabel("Topic:"));
        m_pubTopic = new QLineEdit("iot/sensor/temperature");
        r3->addWidget(m_pubTopic);
        g2->addLayout(r3);
        auto *r4 = new QHBoxLayout();
        r4->addWidget(new QLabel("Noi dung:"));
        m_pubMsg = new QLineEdit("{\"temp\": 25.5}");
        m_pubMsg->setMinimumWidth(300);
        r4->addWidget(m_pubMsg);
        m_btnPub = new QPushButton("Gui");
        m_btnPub->setStyleSheet("background-color:#2196F3;color:white;padding:5px 15px;");
        m_btnPub->setEnabled(false);
        r4->addWidget(m_btnPub);
        g2->addLayout(r4);
        pubBox->setLayout(g2);
        layout->addWidget(pubBox);

        auto *subBox = new QGroupBox("Nhan tin (Subscribe)");
        auto *g3 = new QVBoxLayout();
        auto *r5 = new QHBoxLayout();
        r5->addWidget(new QLabel("Topic:"));
        m_subTopic = new QLineEdit("iot/#");
        r5->addWidget(m_subTopic);
        m_btnSub = new QPushButton("Dang ky");
        m_btnSub->setStyleSheet("background-color:#FF9800;color:white;padding:5px 15px;");
        m_btnSub->setEnabled(false);
        r5->addWidget(m_btnSub);
        auto *btnClr = new QPushButton("Xoa log");
        r5->addWidget(btnClr);
        r5->addStretch();
        g3->addLayout(r5);
        m_log = new QTextEdit();
        m_log->setReadOnly(true);
        m_log->setFont(QFont("Consolas", 9));
        m_log->setStyleSheet("background-color:#1e1e1e;color:#00ff00;");
        g3->addWidget(m_log);
        subBox->setLayout(g3);
        layout->addWidget(subBox);

        m_sock = new QTcpSocket(this);
        connect(m_btnConn, &QPushButton::clicked, this, &MqttTab::doConnect);
        connect(m_btnDisconn, &QPushButton::clicked, this, &MqttTab::doDisconnect);
        connect(m_btnPub, &QPushButton::clicked, this, &MqttTab::doPublish);
        connect(m_btnSub, &QPushButton::clicked, this, &MqttTab::doSubscribe);
        connect(btnClr, &QPushButton::clicked, m_log, &QTextEdit::clear);
        connect(m_sock, &QTcpSocket::connected, this, [this]() {
            m_sock->write(mktConnect());
            m_status->setText("  Da ket noi");
            m_status->setStyleSheet("color:green;font-weight:bold;");
            m_btnConn->setEnabled(false);
            m_btnDisconn->setEnabled(true);
            m_btnPub->setEnabled(true);
            m_btnSub->setEnabled(true);
            m_log->append("[OK] Ket noi thanh cong");
        });
        connect(m_sock, &QTcpSocket::disconnected, this, [this]() {
            m_status->setText("  Da ngat");
            m_status->setStyleSheet("color:gray;font-weight:bold;");
            m_btnConn->setEnabled(true);
            m_btnDisconn->setEnabled(false);
            m_btnPub->setEnabled(false);
            m_btnSub->setEnabled(false);
            m_log->append("[INFO] Da ngat ket noi");
        });
        connect(m_sock, &QTcpSocket::readyRead, this, [this]() {
            QByteArray d = m_sock->readAll();
            if (d.size() > 3 && (d[0] & 0xF0) == 0x30) {
                int tLen = ((unsigned char)d[1] << 8) | (unsigned char)d[2];
                QString ts = QDateTime::currentDateTime().toString("HH:mm:ss");
                m_log->append(QString("[%1] %2: %3").arg(ts, d.mid(3, tLen), d.mid(3 + tLen)));
            }
        });
    }

private:
    void doConnect() {
        m_log->append("[INFO] Dang ket noi...");
        m_btnConn->setEnabled(false);
        m_sock->connectToHost(m_host->text(), m_port->value());
    }
    void doDisconnect() { m_sock->disconnectFromHost(); }
    void doPublish() {
        if (!m_sock->isOpen()) return;
        QByteArray pkt;
        pkt += (char)0x30;
        QByteArray body;
        QString t = m_pubTopic->text();
        body += (char)((t.length() >> 8) & 0xFF);
        body += (char)(t.length() & 0xFF);
        body += t.toUtf8();
        body += m_pubMsg->text().toUtf8();
        pkt += (char)body.length();
        pkt += body;
        m_sock->write(pkt);
        m_log->append(QString("[%1] [GUI -> %2] %3")
            .arg(QDateTime::currentDateTime().toString("HH:mm:ss"), t, m_pubMsg->text()));
    }
    void doSubscribe() {
        if (!m_sock->isOpen()) return;
        QByteArray pkt;
        pkt += (char)0x82;
        QByteArray body;
        body += (char)0x00; body += (char)0x01;
        QString t = m_subTopic->text();
        body += (char)((t.length() >> 8) & 0xFF);
        body += (char)(t.length() & 0xFF);
        body += t.toUtf8();
        body += (char)0x00;
        pkt += (char)body.length();
        pkt += body;
        m_sock->write(pkt);
        m_log->append("[OK] Dang ky: " + t);
    }
    QByteArray mktConnect() {
        QString id = "cpp-iot-gw";
        QByteArray b;
        b += (char)0x10;
        QByteArray p;
        p += (char)0x00; p += (char)0x04; p += "MQTT";
        p += (char)0x04; p += (char)0x02;
        p += (char)0x00; p += (char)0x3C;
        p += (char)0x00; p += (char)id.length();
        p += id.toUtf8();
        b += (char)p.length(); b += p;
        return b;
    }

    QLineEdit *m_host, *m_pubTopic, *m_pubMsg, *m_subTopic;
    QSpinBox *m_port;
    QPushButton *m_btnConn, *m_btnDisconn, *m_btnPub, *m_btnSub;
    QLabel *m_status;
    QTextEdit *m_log;
    QTcpSocket *m_sock;
};

// ============================================================
// Modbus Tab
// ============================================================
class ModbusTab : public QWidget {
    Q_OBJECT
public:
    ModbusTab(QWidget *parent = nullptr) : QWidget(parent), m_mbSock(nullptr) {
        auto *layout = new QVBoxLayout(this);

        auto *connGrp = new QGroupBox("Modbus TCP Client");
        auto *g1 = new QVBoxLayout();
        auto *r1 = new QHBoxLayout();
        r1->addWidget(new QLabel("IP:"));
        m_ip = new QLineEdit("127.0.0.1");
        m_ip->setMinimumWidth(150);
        r1->addWidget(m_ip);
        r1->addWidget(new QLabel("Port:"));
        m_port = new QSpinBox();
        m_port->setRange(1, 65535);
        m_port->setValue(5020);
        r1->addWidget(m_port);
        m_btnConn = new QPushButton("Ket noi");
        m_btnConn->setStyleSheet("background-color:#4CAF50;color:white;padding:5px 15px;");
        m_btnDisconn = new QPushButton("Ngat");
        m_btnDisconn->setStyleSheet("background-color:#f44336;color:white;padding:5px 15px;");
        m_btnDisconn->setEnabled(false);
        m_status = new QLabel("  Chua ket noi");
        m_status->setStyleSheet("color:red;font-weight:bold;");
        r1->addWidget(m_btnConn);
        r1->addWidget(m_btnDisconn);
        r1->addWidget(m_status);
        r1->addStretch();
        g1->addLayout(r1);
        connGrp->setLayout(g1);
        layout->addWidget(connGrp);

        auto *readGrp = new QGroupBox("Doc du lieu");
        auto *g2 = new QVBoxLayout();
        auto *r2 = new QHBoxLayout();
        r2->addWidget(new QLabel("Address:"));
        m_addr = new QSpinBox();
        m_addr->setRange(0, 65535);
        m_addr->setValue(0);
        r2->addWidget(m_addr);
        r2->addWidget(new QLabel("So luong:"));
        m_count = new QSpinBox();
        m_count->setRange(1, 125);
        m_count->setValue(10);
        r2->addWidget(m_count);
        g2->addLayout(r2);
        auto *r3 = new QHBoxLayout();
        m_btnFC3 = new QPushButton("Read Holding (FC3)");
        m_btnFC3->setStyleSheet("background-color:#2196F3;color:white;padding:5px;");
        m_btnFC4 = new QPushButton("Read Input (FC4)");
        m_btnFC4->setStyleSheet("background-color:#2196F3;color:white;padding:5px;");
        m_btnFC1 = new QPushButton("Read Coils (FC1)");
        m_btnFC1->setStyleSheet("background-color:#2196F3;color:white;padding:5px;");
        m_btnFC3->setEnabled(false);
        m_btnFC4->setEnabled(false);
        m_btnFC1->setEnabled(false);
        r3->addWidget(m_btnFC3);
        r3->addWidget(m_btnFC4);
        r3->addWidget(m_btnFC1);
        g2->addLayout(r3);
        readGrp->setLayout(g2);
        layout->addWidget(readGrp);

        auto *resGrp = new QGroupBox("Ket qua");
        auto *g3 = new QVBoxLayout();
        m_table = new QTableWidget();
        m_table->setColumnCount(3);
        m_table->setHorizontalHeaderLabels({"Address", "Dec", "Hex"});
        m_table->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
        g3->addWidget(m_table);
        resGrp->setLayout(g3);
        layout->addWidget(resGrp);

        m_mbLog = new QTextEdit();
        m_mbLog->setReadOnly(true);
        m_mbLog->setMaximumHeight(80);
        m_mbLog->setFont(QFont("Consolas", 9));
        layout->addWidget(m_mbLog);

        connect(m_btnConn, &QPushButton::clicked, this, &ModbusTab::doConnect);
        connect(m_btnDisconn, &QPushButton::clicked, this, &ModbusTab::doDisconnect);
        connect(m_btnFC3, &QPushButton::clicked, this, &ModbusTab::doReadFC3);
        connect(m_btnFC4, &QPushButton::clicked, this, &ModbusTab::doReadFC4);
        connect(m_btnFC1, &QPushButton::clicked, this, &ModbusTab::doReadFC1);
    }

private slots:
    void doConnect() {
        m_mbSock = new QTcpSocket(this);
        m_mbSock->connectToHost(m_ip->text(), m_port->value());
        if (m_mbSock->waitForConnected(3000)) {
            m_status->setText("  Da ket noi");
            m_status->setStyleSheet("color:green;font-weight:bold;");
            m_btnConn->setEnabled(false);
            m_btnDisconn->setEnabled(true);
            m_btnFC3->setEnabled(true);
            m_btnFC4->setEnabled(true);
            m_btnFC1->setEnabled(true);
            m_mbLog->append("[OK] Ket noi Modbus TCP");
        } else {
            m_mbLog->append("[ERROR] " + m_mbSock->errorString());
            m_mbSock->deleteLater();
            m_mbSock = nullptr;
        }
    }
    void doDisconnect() {
        if (m_mbSock) { m_mbSock->disconnectFromHost(); m_mbSock->deleteLater(); m_mbSock = nullptr; }
        m_status->setText("  Da ngat");
        m_status->setStyleSheet("color:gray;font-weight:bold;");
        m_btnConn->setEnabled(true);
        m_btnDisconn->setEnabled(false);
        m_btnFC3->setEnabled(false);
        m_btnFC4->setEnabled(false);
        m_btnFC1->setEnabled(false);
    }
    void doReadFC3() { sendMBRequest(0x03); }
    void doReadFC4() { sendMBRequest(0x04); }
    void doReadFC1() {
        if (!m_mbSock || !m_mbSock->isOpen()) return;
        QByteArray req;
        req += (char)0x00; req += (char)0x01;
        req += (char)0x00; req += (char)0x00;
        req += (char)0x00; req += (char)0x06;
        req += (char)0x01;
        req += (char)0x01;
        req += (char)((m_addr->value() >> 8) & 0xFF);
        req += (char)(m_addr->value() & 0xFF);
        req += (char)((m_count->value() >> 8) & 0xFF);
        req += (char)(m_count->value() & 0xFF);
        m_mbSock->write(req);
        m_mbSock->waitForReadyRead(3000);
        QByteArray r = m_mbSock->readAll();
        if (r.size() < 9) { m_mbLog->append("[ERROR] Khong nhan duoc du lieu"); return; }
        int n = (unsigned char)r[8];
        m_table->setRowCount(n);
        for (int i = 0; i < n; i++) {
            bool on = r[9 + i];
            m_table->setItem(i, 0, new QTableWidgetItem(QString::number(m_addr->value() + i)));
            m_table->setItem(i, 1, new QTableWidgetItem(on ? "ON" : "OFF"));
            m_table->setItem(i, 2, new QTableWidgetItem(on ? "1" : "0"));
        }
        m_mbLog->append(QString("[OK] Doc %1 coils").arg(n));
    }

private:
    void sendMBRequest(uint8_t fc) {
        if (!m_mbSock || !m_mbSock->isOpen()) return;
        QByteArray req;
        req += (char)0x00; req += (char)0x01;
        req += (char)0x00; req += (char)0x00;
        req += (char)0x00; req += (char)0x06;
        req += (char)0x01;
        req += (char)fc;
        req += (char)((m_addr->value() >> 8) & 0xFF);
        req += (char)(m_addr->value() & 0xFF);
        req += (char)((m_count->value() >> 8) & 0xFF);
        req += (char)(m_count->value() & 0xFF);
        m_mbSock->write(req);
        m_mbSock->waitForReadyRead(3000);
        QByteArray r = m_mbSock->readAll();
        if (r.size() < 9) { m_mbLog->append("[ERROR] Khong nhan duoc du lieu"); return; }
        int n = ((unsigned char)r[8]) / 2;
        m_table->setRowCount(n);
        for (int i = 0; i < n; i++) {
            int v = ((unsigned char)r[9 + i*2] << 8) | (unsigned char)r[10 + i*2];
            m_table->setItem(i, 0, new QTableWidgetItem(QString::number(m_addr->value() + i)));
            m_table->setItem(i, 1, new QTableWidgetItem(QString::number(v)));
            m_table->setItem(i, 2, new QTableWidgetItem(QString("0x%1").arg(v, 4, 16, QChar('0'))));
        }
        m_mbLog->append(QString("[OK] Doc %1 thanh ghi").arg(n));
    }

    QLineEdit *m_ip;
    QSpinBox *m_port, *m_addr, *m_count;
    QPushButton *m_btnConn, *m_btnDisconn, *m_btnFC3, *m_btnFC4, *m_btnFC1;
    QLabel *m_status;
    QTableWidget *m_table;
    QTextEdit *m_mbLog;
    QTcpSocket *m_mbSock;
};

// ============================================================
// System Tab
// ============================================================
class SystemTab : public QWidget {
    Q_OBJECT
public:
    SystemTab(QWidget *parent = nullptr) : QWidget(parent) {
        auto *layout = new QVBoxLayout(this);
        auto *r = new QHBoxLayout();
        auto *btn = new QPushButton("Lam moi");
        r->addWidget(btn); r->addStretch();
        layout->addLayout(r);
        m_info = new QTextEdit();
        m_info->setReadOnly(true);
        m_info->setFont(QFont("Consolas", 10));
        m_info->setStyleSheet("background-color:#1e1e1e;color:#00ff00;");
        layout->addWidget(m_info);
        auto *t = new QTimer(this);
        connect(t, &QTimer::timeout, this, &SystemTab::refresh);
        connect(btn, &QPushButton::clicked, this, &SystemTab::refresh);
        t->start(2000);
        refresh();
    }

private slots:
    void refresh() {
        QStringList L;
        L << "=============================================";
#ifdef _WIN32
        L << "  HE THONG - IoT Gateway [Windows]";
#else
        L << "  HE THONG - IoT Gateway [Linux]";
#endif
        L << "=============================================" << "";

        // Hostname
        char hn[256] = {0};
#ifdef _WIN32
        DWORD sz = sizeof(hn);
        GetComputerNameA(hn, &sz);
#else
        gethostname(hn, sizeof(hn));
#endif
        L << QString("Hostname:  %1").arg(hn);
        L << QString("Platform:  %1").arg(QSysInfo::currentCpuArchitecture());
        L << QString("OS:        %1").arg(QSysInfo::prettyProductName());

#ifdef _WIN32
        // RAM via PowerShell
        QProcess p;
        p.start("powershell", {"-Command",
            "$o=Get-CimInstance Win32_OperatingSystem;"
            "$t=[math]::Round($o.TotalVisibleMemorySize/1024);"
            "$f=[math]::Round($o.FreePhysicalMemory/1024);"
            "Write-Output \"$t $f\""});
        p.waitForFinished(3000);
        QStringList rp = QString(p.readAllStandardOutput()).trimmed().split(' ');
        if (rp.size() >= 2) {
            int tot = rp[0].toInt(), free = rp[1].toInt(), used = tot - free;
            L << QString("RAM:       %1MB / %2MB (%3%)").arg(used).arg(tot).arg(used*100/qMax(tot,1));
        }
        // Uptime
        p.start("powershell", {"-Command",
            "$b=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime;"
            "$d=(Get-Date)-$b;Write-Output \"$($d.Hours)h $($d.Minutes)m\""});
        p.waitForFinished(3000);
        L << QString("Uptime:    %1").arg(QString(p.readAllStandardOutput()).trimmed());
        // Processes
        p.start("powershell", {"-Command", "(Get-Process).Count"});
        p.waitForFinished(3000);
        L << QString("Processes: %1").arg(QString(p.readAllStandardOutput()).trimmed());
#else
        QFile f("/proc/uptime");
        if (f.open(QIODevice::ReadOnly)) {
            double up = f.readAll().split(' ')[0].toDouble();
            L << QString("Uptime:    %1h %2m").arg((int)up/3600).arg(((int)up%3600)/60);
        }
        QFile m("/proc/meminfo");
        if (m.open(QIODevice::ReadOnly)) {
            qint64 tot=0, av=0;
            while (!m.atEnd()) {
                QString ln = m.readLine().trimmed();
                if (ln.startsWith("MemTotal:")) tot = ln.split(':')[1].trimmed().split(' ')[0].toLongLong()/1024;
                if (ln.startsWith("MemAvailable:")) av = ln.split(':')[1].trimmed().split(' ')[0].toLongLong()/1024;
            }
            qint64 used = tot - av;
            L << QString("RAM:       %1MB / %2MB (%3%)").arg(used).arg(tot).arg(used*100/qMax(tot,1LL));
        }
        QFile t("/sys/class/thermal/thermal_zone0/temp");
        if (t.open(QIODevice::ReadOnly))
            L << QString("CPU Temp:  %1 C").arg(t.readAll().trimmed().toDouble()/1000.0, 0, 'f', 1);
#endif

        // Network
        L << "" << "--- MANG ---";
        for (auto &iface : QNetworkInterface::allInterfaces()) {
            if (iface.flags().testFlag(QNetworkInterface::IsUp) &&
                iface.flags().testFlag(QNetworkInterface::IsRunning)) {
                for (auto &entry : iface.addressEntries()) {
                    if (entry.ip().protocol() == QAbstractSocket::IPv4Protocol)
                        L << QString("  %1: %2").arg(iface.humanReadableName(), entry.ip().toString());
                }
            }
        }
        L << "=============================================";
        m_info->setText(L.join('\n'));
    }

private:
    QTextEdit *m_info;
};

// ============================================================
// Log Tab
// ============================================================
class LogTab : public QWidget {
    Q_OBJECT
public:
    LogTab(QWidget *parent = nullptr) : QWidget(parent) {
        auto *layout = new QVBoxLayout(this);
        auto *r = new QHBoxLayout();
        auto *btnLog = new QPushButton("Xem log");
        auto *btnClr = new QPushButton("Xoa");
        r->addWidget(btnLog); r->addWidget(btnClr); r->addStretch();
        layout->addLayout(r);
        m_view = new QTextEdit();
        m_view->setReadOnly(true);
        m_view->setFont(QFont("Consolas", 9));
        m_view->setStyleSheet("background-color:#1e1e1e;color:#cccccc;");
        layout->addWidget(m_view);
        connect(btnLog, &QPushButton::clicked, this, [this]() {
#ifdef _WIN32
            QProcess p;
            p.start("powershell", {"-Command",
                "Get-EventLog -LogName System -Newest 30 | Format-Table -AutoSize"});
            p.waitForFinished(5000);
            m_view->setPlainText(QString(p.readAllStandardOutput()).left(8000));
#else
            QProcess p;
            p.start("dmesg");
            p.waitForFinished(3000);
            m_view->setPlainText(QString(p.readAllStandardOutput()).right(8000));
#endif
        });
        connect(btnClr, &QPushButton::clicked, m_view, &QTextEdit::clear);
    }
private:
    QTextEdit *m_view;
};

// ============================================================
// Main
// ============================================================
int main(int argc, char *argv[]) {
    QApplication app(argc, argv);
    app.setStyle("Fusion");
    QPalette pal;
    pal.setColor(QPalette::Window, QColor(53,53,53));
    pal.setColor(QPalette::WindowText, Qt::white);
    pal.setColor(QPalette::Base, QColor(35,35,35));
    pal.setColor(QPalette::Text, Qt::white);
    pal.setColor(QPalette::Button, QColor(53,53,53));
    pal.setColor(QPalette::ButtonText, Qt::white);
    pal.setColor(QPalette::Highlight, QColor(42,130,218));
    app.setPalette(pal);

    QMainWindow win;
    win.setWindowTitle("IoT Gateway - Orange Pi Zero H3 [C++ Qt5]");
    win.resize(900, 550);
    auto *tabs = new QTabWidget();
    tabs->addTab(new MqttTab(), "MQTT");
    tabs->addTab(new ModbusTab(), "Modbus");
    tabs->addTab(new SystemTab(), "System");
    tabs->addTab(new LogTab(), "Log");
    win.setCentralWidget(tabs);
    win.statusBar()->showMessage("C++ Qt5 - Cross-platform");
    win.show();
    return app.exec();
}

#include "main.moc"
