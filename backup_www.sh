#!/bin/bash
# author: Georg Wallisch
# contact: gw@phpco.de
# copyright: Copyright © 2018 by Georg Wallisch
# credits: Georg Wallisch
# date: 2018/07/28
# deprecated: False
# email: gw@phpco.de
# license: GPL
# maintainer: Georg Wallisch
# status: beta

SRC_PATH=/var/www
BACKUP_SUFFIX=tar.gz
BACKUPS=5
USAGE="USAGE: sudo $0 /path/to/backup"

echo -e "\n**************************"
echo -e   "* WWW Backup Script v1.2 *"
echo -e   "**************************\n"
echo -e "Starting backup on $(date)\n"

if [ $(id -u) -ne 0 ]; then
	echo -e "WWW Backup script must be run as root."
	echo -e "${USAGE}\n"
    exit 1
fi

if [ "$1" == '' ]; then
	echo -e "Backup path not specified."
	echo -e "${USAGE}\n"
    exit 1
fi

BACKUP_PATH=$1
shift
echo -e "Backup path is set to ${BACKUP_PATH}"

if [ ! -d "$BACKUP_PATH" ]; then
	echo "${BACKUP_PATH} does not exist, creating.."
	mkdir -p $BACKUP_PATH
	if [ ! -d "$BACKUP_PATH" ]; then
		echo "Could not create ${BACKUP_PATH}!"
		exit 1
	fi
fi

if [ -d "$1" ]; then
	SRC_PATH=$1
	shift
	echo "Source path is set to ${SRC_PATH}"
else
	echo "Source path is ${SRC_PATH}"
fi

BACKUP_PREFIX=$(readlink -f $SRC_PATH)
BACKUP_PREFIX=${BACKUP_PREFIX:1}
BACKUP_PREFIX=${BACKUP_PREFIX////_}
echo -e "Using Prefix ${BACKUP_PREFIX}"

echo -e "Packing and compressing ${SRC_PATH} into ${BACKUP_PATH}/${FILE}"
FILE="${BACKUP_PREFIX}.0.${BACKUP_SUFFIX}"
tar -czf $BACKUP_PATH/$FILE $SRC_PATH

if [ $? -ne 0 ]; then
	echo -e "Error packing ${SRC_PATH}!"
	exit 1
else
	
	counter=$BACKUPS
	PREVFILE=$BACKUP_PREFIX.$counter.$BACKUP_SUFFIX

	if [ -f "$BACKUP_PATH/$PREVFILE" ]; then
		echo -e "Removing oldest file $PREVFILE"
		rm -f $BACKUP_PATH/$PREVFILE
	fi
 
	((counter--))

	until [ $counter -lt 0 ]
	do
		FILE=$BACKUP_PREFIX.$counter.$BACKUP_SUFFIX
		FP=""
		if [ -f $BACKUP_PATH/$FILE ]; then
				mv  $BACKUP_PATH/$FILE $BACKUP_PATH/$PREVFILE
			echo -e "Moving $FILE to $PREVFILE"
		fi
		PREVFILE="$FILE"
		((counter--))
	done
fi

echo -e "Finished backup by $(date)!\n"
exit 0

