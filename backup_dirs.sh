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
BACKUP_PREFIX=$HOSTNAME
USAGE="USAGE: sudo $0 /path/to/backup /path/to/source/dir1 [/path/to/source/dir2 [/path/to/source/dir3 [..]]]"

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
	echo -e "Backup path not specified."
	echo -e "${USAGE}\n"
    exit 1
fi

BACKUP_PATH=$1
shift

SRC_PATH=""

while [ $# -ne 0 ]  # ne = not equal
do
	if [ -d "$1" ]; then
		P="$1"
		if [ "${P:0:1}" == "/" ]; then
			SRC_PATH="${SRC_PATH} ${P:1}"
		else
			SRC_PATH="${SRC_PATH} ${P}"
		fi
	fi	
	shift
done

if [ "$SRC_PATH" == '' ]; then
	echo -e "No source path specified."
	echo -e "${USAGE}\n"
    exit 1
fi

echo -e "Backup path is set to ${BACKUP_PATH}"

if [ ! -d "$BACKUP_PATH" ]; then
	echo "${BACKUP_PATH} does not exist, creating.."
	mkdir -p $BACKUP_PATH
	if [ ! -d "$BACKUP_PATH" ]; then
		echo "Could not create ${BACKUP_PATH}!"
		exit 1
	fi
fi

#BACKUP_PREFIX=$(readlink -f $SRC_PATH)
#BACKUP_PREFIX=${BACKUP_PREFIX:1}
#BACKUP_PREFIX=${BACKUP_PREFIX////_}
echo -e "Using Prefix ${BACKUP_PREFIX}"

BACKUP_FILENAME="${BACKUP_PREFIX}.${BACKUP_SUFFIX}"
BACKUP_FILE="${BACKUP_PATH}/${BACKUP_FILENAME}"

OLD_BACKUP_FILENAME="${BACKUP_PREFIX}.0.${BACKUP_SUFFIX}"
OLD_BACKUP_FILE="${BACKUP_PATH}/${OLD_BACKUP_FILENAME}"

if [ -f "$OLD_BACKUP_FILE" ]; then
	echo -e "Removing $OLD_BACKUP_FILE (must not exist at this point!)"
	rm -f $OLD_BACKUP_FILE
	if [ $? -ne 0 ]; then
		echo -e "Error while removing $OLD_BACKUP_FILE!"
		exit 1
	fi				
fi

if [ -f "$BACKUP_FILE" ]; then
	echo -e "Moving file $BACKUP_FILE to $OLD_BACKUP_FILE"
	mv -n $BACKUP_FILE $OLD_BACKUP_FILE
	if [ $? -ne 0 ]; then
		echo -e "Error while moving $BACKUP_FILE to $OLD_BACKUP_FILE!"
		exit 1
	fi			
fi

counter=$BACKUPS

FILE="${BACKUP_PATH}/${BACKUP_PREFIX}.${counter}.${BACKUP_SUFFIX}"
if [ -f "$FILE" ]; then
	echo -e "Removing oldest file $FILE"
	rm -f $FILE
	if [ $? -ne 0 ]; then
		echo -e "Error while removing oldest file $FILE!"
	fi
fi

while [ $counter -ge 0 ]; do
	((counter--))
	PREVFILE=$FILE
	FILE="${BACKUP_PATH}/${BACKUP_PREFIX}.${counter}.${BACKUP_SUFFIX}"
		
	if [ -f "$FILE" ]; then
		echo -e "Moving $FILE to $PREVFILE"
		mv -n $FILE $PREVFILE
		if [ $? -ne 0 ]; then
			echo -e "Error while moving $FILE to $PREVFILE!"
		fi
	fi
done
	
echo -e "Packing and compressing into ${BACKUP_FILE}"

cd /

$COMPOSER $COMPOSER_OPTS $SRC_PATH | $COMPRESSOR > $BACKUP_FILE

cd $PWD

if [ $? -ne 0 ]; then
	echo -e "Error packing ${SRC_PATH}!"
	exit 1
fi

echo -e "Finished backup by $(date)!\n"
exit 0