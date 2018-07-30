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

DB_USER=root
BACKUP_PREFIX=db
SQL_SUFFIX=sql
BACKUP_SUFFIX=$SQL_SUFFIX.gz
BACKUPS=5
USAGE="USAGE: sudo $0 /path/to/backup Database1 [[Database2] ..]"
SUCCESS_CNT=0
ERROR_CNT=0

echo -e "\n*************************"
echo -e   "* DB Backup Script v1.2 *"
echo -e   "*************************\n"
echo -e "Starting backup on $(date)\n"

if [ $(id -u) -ne 0 ]; then
	echo -e "DB Backup script must be run as root."
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

if [ $# -eq 0 ]; then
	echo -e "No Database(s) specified!\n"
	echo -e "${USAGE}\n"
	exit 1
fi

while [ $# -ne 0 ]  # ne = not equal
do
	echo "Making Backup for DB $1"
	
	SQLFILE="${BACKUP_PREFIX}_${1}.0.${SQL_SUFFIX}"
	FILE="${BACKUP_PREFIX}_${1}.0.${BACKUP_SUFFIX}"
	
	echo -e "Dumping DB $1 into $SQLFILE"
	mysqldump -u $DB_USER $1 > $BACKUP_PATH/$SQLFILE
	
	if [ $? -ne 0 ]; then
		echo -e "Error while dumping DB $1!"
		if [ -f $BACKUP_PATH/$SQLFILE ]; then
			rm -f $BACKUP_PATH/$SQLFILE
		fi
		((ERROR_CNT++))
	else
		echo -e "Gzipping ${SQLFILE}.."
		gzip -fq $BACKUP_PATH/$SQLFILE
		if [ $? -ne 0 ]; then
			echo -e "Error while gzipping ${SQLFILE}!"
			((ERROR_CNT++))
		else
			((SUCCESS_CNT++))
			counter=$BACKUPS
			PREVFILE="${BACKUP_PREFIX}_${1}.${counter}.${BACKUP_SUFFIX}"
			
			if [ -f $BACKUP_PATH/$PREVFILE ]; then
				echo -e "Removing oldest file $PREVFILE"
				rm -f $BACKUP_PATH/$PREVFILE
			fi
		 
			((counter--))
		
			until [ $counter -lt 0 ]
			do
				FILE="${BACKUP_PREFIX}_${1}.${counter}.${BACKUP_SUFFIX}"
			
				if [ -f  $BACKUP_PATH/$FILE ]; then
						mv  $BACKUP_PATH/$FILE $BACKUP_PATH/$PREVFILE
					echo -e "Moving $FILE to $PREVFILE"
				fi
				PREVFILE=$FILE
				((counter--))
			done
		fi
	fi

	shift       # next DB
done

echo -e "Successfully finished ${SUCCESS_CNT} DB Backup(s) by $(date)!\n"

if [ $ERROR_CNT -gt 0 ]; then
	echo -e "But encountered ${ERROR_CNT} error(s)!\n"
	exit 1
fi

exit 0

