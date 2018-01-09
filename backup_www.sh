#!/bin/bash

scriptname=backup_www.sh
SRC_PATH=/var/www
BACKUP_PATH=/media/usbstick/backup/www
BACKUP_PREFIX=www
BACKUP_SUFFIX=tar.gz
BACKUPS=5

echo -e "\n*******************************"
echo -e "* WWW Backup Script v1.0 *"
echo -e "*******************************\n"

if [ $(id -u) -ne 0 ]; then
	echo -e "WWW Backup script must be run as root. Try 'sudo ./$scriptname'\n"
    exit 1
fi

if [ -d "$1" ]; then
	BACKUP_PATH="$1"	
	shift
fi

if [ ! -d $BACKUP_PATH ]; then
	mkdir -p $BACKUP_PATH	
fi

counter=$BACKUPS
PREVFILE=$BACKUP_PREFIX.$counter.$BACKUP_SUFFIX

if [ -f $BACKUP_PATH/$PREVFILE ]; then
	echo -e "Removing oldest file $PREVFILE"
	rm -f $BACKUP_PATH/$PREVFILE
fi
 
((counter--))

until [ $counter -lt 1 ]
do
	FILE=$BACKUP_PREFIX.$counter.$BACKUP_SUFFIX
	FP="$BACKUP_PATH/$FILE"
	if [ -f "$FP" ]; then
        	mv  "$FP" "$BACKUP_PATH/$PREVFILE"
		echo -e "Moving $FILE to $PREVFILE"
	fi
	PREVFILE="$FILE"
	((counter--))
done

echo -e "Packing Dir from $SRC_PATH into $BACKUP_PATH/$FILE"
tar -vczf "$FP" $SRC_PATH
echo -e "Finished Dir Backup!\n"

