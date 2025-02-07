#!/bin/bash
# author: Georg Wallisch
# contact: gw@phpco.de
# copyright: Copyright © 2025 by Georg Wallisch
# credits: Georg Wallisch
# date: 2025/02/07
# deprecated: False
# email: gw@phpco.de
# license: GPL
# maintainer: Georg Wallisch
# status: beta

BACKUP_SUFFIX=tar.gz
COMPOSER=/usr/bin/tar
COMPOSER_OPTS="-cpf -"
COMPRESSOR=/usr/bin/gzip
BACKUPS=5
USAGE="USAGE: sudo $0 /path/to/source/dir /path/to/backup"

echo -e "\n********************************"
echo -e   "* Directory Backup Script v1.4 *"
echo -e   "********************************\n"
echo -e "Starting backup on $(date)\n"

if [ $(id -u) -ne 0 ]; then
	echo -e "Backup script must be run as root."
	echo -e "${USAGE}\n"
    exit 1
fi

if [ "$1" == '' ]; then
	echo -e "Source path not specified."
	echo -e "${USAGE}\n"
    exit 1
fi

SRC_PATH=$1
shift

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

BACKUP_PREFIX=$(readlink -f $SRC_PATH)
BACKUP_PREFIX=${BACKUP_PREFIX:1}
BACKUP_PREFIX=${BACKUP_PREFIX////_}
echo -e "Using Prefix ${BACKUP_PREFIX}"

FILE="${BACKUP_PREFIX}.0.${BACKUP_SUFFIX}"

echo -e "Packing and compressing ${SRC_PATH} into ${BACKUP_PATH}/${FILE}"

$COMPOSER $COMPOSER_OPTS $SRC_PATH | $COMPRESSOR > $BACKUP_PATH/$FILE

if [ $? -ne 0 ]; then
	echo -e "Error packing ${SRC_PATH}!"
	exit 1
else
	
	counter=$BACKUPS
	PREVFILE=$BACKUP_PREFIX.$counter.$BACKUP_SUFFIX

	if [ -f $BACKUP_PATH/$PREVFILE ]; then
		if [ -w $BACKUP_PATH/$PREVFILE ]; then
			echo -e "Removing oldest file $PREVFILE"
			rm -f $BACKUP_PATH/$PREVFILE
			if [ $? -ne 0 ]; then
				echo -e "Error while removing oldest file $PREVFILE!"
			fi
		else
			echo -e "Cannot remove oldest file $PREVFILE! No write permission!"
		fi				
	fi
 
	((counter--))

	until [ $counter -lt 0 ]
	do
		FILE=$BACKUP_PREFIX.$counter.$BACKUP_SUFFIX
		if [ -f  $BACKUP_PATH/$FILE ]; then
			if [ -w $BACKUP_PATH/$FILE ]; then
				echo -e "Moving $FILE to $PREVFILE"
				mv -n $BACKUP_PATH/$FILE $BACKUP_PATH/$PREVFILE
				if [ $? -ne 0 ]; then
					echo -e "Error while moving $FILE to $PREVFILE!"
				fi
			else
				echo -e "Cannot move $FILE to $PREVFILE! No write permission!"
			fi
		fi
		PREVFILE=$FILE
		((counter--))
	done
fi

echo -e "Finished backup by $(date)!\n"
exit 0

