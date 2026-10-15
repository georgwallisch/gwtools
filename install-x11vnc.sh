#!/usr/bin/env bash

set -euo pipefail

ERROR=0
APTUPDATE=0
FORCEINSTALL=0
VNCPORT=5900
VNCPWFILE=".vncpass"
VNCPWDIR="/etc/x11vnc"
SDDMSCRIPTPATH="/usr/local/bin/x11vnc-sddm.sh"
SDUNITPATH="/etc/systemd/system/x11vnc.service"
VNCPWPATH="$VNCPWDIR/$VNCPWFILE"
PLACEHOLDERPATH="__VNCPWPATH__"
PLACEHOLDERPORT="__VNCPORT__"
VERSION="1.0"

echo -e "\n ***********************************"
echo -e   " * gw X11VNC service installer ${VERSION} *"
echo -e   " ***********************************\n"

if (( EUID != 0 )); then
	echo "Script must be run as root. Try 'sudo $0'"
	exit 1
fi

if systemctl cat x11vnc.service &>/dev/null; then
    echo "ERROR: The systemd service x11vnc.service already exists." >&2
    echo "Aborting to prevent overwriting an existing installation." >&2
    exit 1
fi

while getopts ":fuo:p:" opt; do
    case "$opt" in
        u)
            APTUPDATE=1
            ;;
        f)
            FORCEINSTALL=1
            ;;
        o)
            VNCPWPATH=$OPTARG
            VNCPWDIR=$(dirname -- "$VNCPWPATH")
            VNCPWFILE=$(basename -- "$VNCPWPATH")
            ;;
        p)
            if [[ "$OPTARG" =~ ^[0-9]+$ ]] &&
               (( OPTARG >= 1024 && OPTARG <= 65535 )); then
                VNCPORT=$OPTARG
            else
                echo "ERROR: Invalid TCP port: $OPTARG" >&2
                exit 1
            fi
            ;;
        :)
            echo "ERROR: Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
        \?)
            echo "ERROR: Unknown option: -$OPTARG" >&2
            exit 1
            ;;
    esac
done

if [[ "$VNCPWPATH" != /* ]]; then
    echo "ERROR: VNC password path must be absolute." >&2
    exit 1
fi

if (( FORCEINSTALL )); then
	echo "FORCE INSTALL option is set! Will overwrite exisiting files!"
else
 for FILE in "$VNCPWPATH" "$SDDMSCRIPTPATH" "$SDUNITPATH"; do
        if [[ -e "$FILE" ]]; then
            echo "ERROR: $FILE already exists." >&2
            echo "Remove it or use -f to overwrite existing files." >&2
            ERROR=1
        fi
    done

    if (( ERROR )); then
        echo "Aborting." >&2
        exit 1
    fi
fi

echo "==> x11vnc installieren"
if (( APTUPDATE )); then
	apt update
fi
apt install -y x11vnc

echo "==> Verzeichnis für VNC-Passwort anlegen"
install -d -m 700 "$VNCPWDIR"

echo "==> VNC-Passwort anlegen"
x11vnc -storepasswd "$VNCPWPATH"

if [[ ! -s "$VNCPWPATH" ]]; then
    echo "ERROR: VNC password file was not created correctly." >&2
    exit 1
fi

chmod 600 "$VNCPWPATH"

echo "==> Startskript installieren"

cat > "$SDDMSCRIPTPATH" <<'EOF'
#!/bin/bash

set -euo pipefail

for i in {1..10}; do
    XAUTH=$(find /run/sddm/ -type f -name "xauth_*" 2>/dev/null | sort | head -n 1)
    [ -n "$XAUTH" ] && break
    sleep 1
done

if [ -z "${XAUTH:-}" ]; then
    echo "ERROR: No SDDM XAUTH file found" >&2
    exit 1
fi

echo "Using XAUTH: $XAUTH"

export DISPLAY=:0
export XAUTHORITY="$XAUTH"

exec /usr/bin/x11vnc \
    -rfbauth __VNCPWPATH__ \
    -forever -noxdamage -repeat -rfbport __VNCPORT__ -shared
EOF

sed -i "s|$PLACEHOLDERPATH|$VNCPWPATH|g" "$SDDMSCRIPTPATH"
sed -i "s|$PLACEHOLDERPORT|$VNCPORT|g" "$SDDMSCRIPTPATH"

chmod 755 "$SDDMSCRIPTPATH"

echo "==> installing systemd-Unit"

cat > "$SDUNITPATH" <<EOF
[Unit]
Description=x11vnc remote desktop server
After=display-manager.service

[Service]
Type=simple
ExecStart=$SDDMSCRIPTPATH
Restart=always
RestartSec=2
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "==> reloading systemd"
systemctl daemon-reload

echo "==> enabling x11vnc service"
systemctl enable x11vnc

echo "==> starting x11vnc service"
systemctl start x11vnc

if systemctl is-active --quiet x11vnc; then
    echo "x11vnc is running."
else
    echo "ERROR: x11vnc did not start successfully." >&2
    echo "Check the service log with:" >&2
    echo "  journalctl -u x11vnc -b --no-pager" >&2
    exit 1
fi

systemctl --no-pager --full status x11vnc


echo -e "** Finished X11VNC service installer! **\n"
