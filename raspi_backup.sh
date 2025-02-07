#!/bin/bash
MOUNTPOINT=/mnt/backupdir
BAKDIR="${MOUNTPOINT}/${HOSTNAME}"
SCRIPTDIR=$(dirname $0)

echo -e "\n*************************"
echo -e   "* Raspi Backup Script v1.1 *"
echo -e   "*************************\n"
echo -e "Starting backup on $(date)\n"

if [ $(id -u) -ne 0 ]; then
	echo -e "Raspi Backup script must be run as root."
	echo -e "sudo $0\n"
    exit 1
fi

echo "Script dir is set to $SCRIPTDIR"

if [ -d $MOUNTPOINT ]; then
	echo "Mount point is set to ${MOUNTPOINT}"
	
	if [ -z "$(/bin/grep $MOUNTPOINT /proc/mounts)" ]; then
		echo "Mount point seems not to be mounted!"
		echo "Try to mount $MOUNTPOINT .."
		/bin/mount $MOUNTPOINT
		if [ $? -eq 1 ]; then
			echo "ERROR mounting $MOUNTPOINT !"				
		else
			echo "Successfully mounted $MOUNTPOINT"
		fi
	else
		echo "Mount point seems to be mounted correctly"
	fi
else
	echo "Mount point seems NOT to be valid!"	
	echo "Try to create $MOUNTPOINT .."
	/usr/bin/mkdir -p $MOUNTPOINT
	echo "Do run script again now!"
	exit 1
fi

$SCRIPTDIR/backup_dirs.sh $BAKDIR /home/pi /var/www /etc /var/spool/cron /root
$SCRIPTDIR/backup_db.sh $BAKDIR icinga2 icingaweb2

echo "Unmounting $MOUNTPOINT .."
/bin/umount $MOUNTPOINT

echo -e "Successfully finished Raspi Backup by $(date)!\n"