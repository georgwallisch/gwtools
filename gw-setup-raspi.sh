#!/bin/bash

BLACKLIST=/etc/modprobe.d/raspi-blacklist.conf
CONFIG=/boot/config.txt
TIMEZONE="Europe/Berlin"
COUNTRY="DE"

disable_raspi_config_at_boot() {
  if [ -e /etc/profile.d/raspi-config.sh ]; then
    rm -f /etc/profile.d/raspi-config.sh
    if [ -e /etc/systemd/system/getty@tty1.service.d/raspi-config-override.conf ]; then
      rm /etc/systemd/system/getty@tty1.service.d/raspi-config-override.conf
    fi
    telinit q
  fi
}

set_config_var() {
  lua - "$1" "$2" "$3" <<EOF > "$3.bak"
local key=assert(arg[1])
local value=assert(arg[2])
local fn=assert(arg[3])
local file=assert(io.open(fn))
local made_change=false
for line in file:lines() do
  if line:match("^#?%s*"..key.."=.*$") then
    line=key.."="..value
    made_change=true
  end
  print(line)
end

if not made_change then
  print(key.."="..value)
end
EOF
mv "$3.bak" "$3"
}

clear_config_var() {
  lua - "$1" "$2" <<EOF > "$2.bak"
local key=assert(arg[1])
local fn=assert(arg[2])
local file=assert(io.open(fn))
for line in file:lines() do
  if line:match("^%s*"..key.."=.*$") then
    line="#"..line
  end
  print(line)
end
EOF
mv "$2.bak" "$2"
}

get_config_var() {
  lua - "$1" "$2" <<EOF
local key=assert(arg[1])
local fn=assert(arg[2])
local file=assert(io.open(fn))
local found=false
for line in file:lines() do
  local val = line:match("^%s*"..key.."=(.*)$")
  if (val ~= nil) then
    print(val)
    found=true
    break
  end
end
if not found then
   print(0)
end
EOF
}

echo -e "\n**********************************"
echo -e "* GW Setup Script for Raspi v0.1 *"
echo -e "**********************************\n"

if [ $(id -u) -ne 0 ]; then
	echo -e "Script must be run as root. Try 'sudo $0'\n"
	exit 1
fi

whiptail --msgbox "\
Please note: RFCs mandate that a hostname's labels \
may contain only the ASCII letters 'a' through 'z' (case-insensitive), 
the digits '0' through '9', and the hyphen.
Hostname labels cannot begin or end with a hyphen. 
No other symbols, punctuation characters, or blank spaces are permitted.\
" 20 70 1

CURRENT_HOSTNAME=`cat /etc/hostname | tr -d " \t\n\r"`
NEW_HOSTNAME=$(whiptail --inputbox "Please enter a hostname" 20 60 "$CURRENT_HOSTNAME" 3>&1 1>&2 2>&3)
if [ $? -eq 0 ]; then
	echo $NEW_HOSTNAME > /etc/hostname
    sed -i "s/127.0.1.1.*$CURRENT_HOSTNAME/127.0.1.1\t$NEW_HOSTNAME/g" /etc/hosts
fi
  
apt-get update &&
apt-get -y -f dist-upgrade &&
apt-get -y install git samba-common samba tdb-tools

echo -e "\nÄndere Zeitzone nach $TIMEZONE"
rm /etc/localtime
echo "$TIMEZONE" > /etc/timezone
dpkg-reconfigure -f noninteractive tzdata

echo -e "\nÄndere Land nach $COUNTRY"
if [ -e /etc/wpa_supplicant/wpa_supplicant.conf ]; then
	if grep -q "^country=" /etc/wpa_supplicant/wpa_supplicant.conf ; then
		sed -i --follow-symlinks "s/^country=.*/country=$COUNTRY/g" /etc/wpa_supplicant/wpa_supplicant.conf
		else
			sed -i --follow-symlinks "1i country=$COUNTRY" /etc/wpa_supplicant/wpa_supplicant.conf
		fi
	else
		echo "country=$COUNTRY" > /etc/wpa_supplicant/wpa_supplicant.conf
	fi
fi

echo -e "\nAktiviere SPI"
set_config_var dtparam=spi on $CONFIG &&
if ! [ -e $BLACKLIST ]; then
	touch $BLACKLIST
fi
sed $BLACKLIST -i -e "s/^\(blacklist[[:space:]]*spi[-_]bcm2708\)/#\1/"
dtparam spi=on

echo -e "\nAktiviere I2C"
set_config_var dtparam=i2c_arm on $CONFIG &&
if ! [ -e $BLACKLIST ]; then
	touch $BLACKLIST
	fi
sed $BLACKLIST -i -e "s/^\(blacklist[[:space:]]*i2c[-_]bcm2708\)/#\1/"
sed /etc/modules -i -e "s/^#[[:space:]]*\(i2c[-_]dev\)/\1/"
if ! grep -q "^i2c[-_]dev" /etc/modules; then
	printf "i2c-dev\n" >> /etc/modules
fi
dtparam i2c_arm=on
modprobe i2c-dev

echo -e "\nAktiviere OneWire"
sed $CONFIG -i -e "s/^#dtoverlay=w1-gpio/dtoverlay=w1-gpio/"
if ! grep -q -E "^dtoverlay=w1-gpio" $CONFIG; then
	printf "dtoverlay=w1-gpio\n" >> $CONFIG
fi

cd /home/pi
git clone git://git.drogon.net/wiringPi
cd wiringPi
./build
 
disable_raspi_config_at_boot
echo -e "\n*** Fertig ***\n\nStarte in 10 sek neu.."
sleep 10
sync
reboot




