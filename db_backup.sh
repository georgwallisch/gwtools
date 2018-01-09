#!/bin/bash

scriptname=db_backup.sh
DB_USER=root
BACKUP_PREFIX=db_
BACKUP_PATH=$PWD
BACKUPS=5
SUCCESS_CNT=0
ERROR_CNT=0

echo -e "\n*************************"
echo -e   "* DB Backup Script v1.1 *"
echo -e   "*************************\n"


if [ $(id -u) -ne 0 ]; then
	echo -e "DB Backup script must be run as root. Try 'sudo ./$scriptname'\n"
        exit 1
fi

if [ -d "$1" ]; then
	BACKUP_PATH="$1"	
	shift
fi

echo -e "Backup path is set to $BACKUP_PATH\n"

if [ ! -d $BACKUP_PATH ]; then
	mkdir -p $BACKUP_PATH	
fi

while [ "$1" != '' ]
  do  	  
	DB_NAME="$1"
	shift
	
	SQLFILE="${BACKUP_PREFIX}${DB_NAME}.sql"
	SQLFILEPATH="${BACKUP_PATH}/${SQLFILE}"
	echo -e "Dumping DB $DB_NAME into $SQLFILE"
	
	mysqldump -u $DB_USER $DB_NAME > "$SQLFILEPATH"
	
	if [ $? -gt 0 ]; then
		echo -e "Error while dumping Database $DB_NAME"
		rm -f "$SQLFILEPATH"
		((ERROR_CNT++))
	else
		gzip -fq "$SQLFILEPATH"
		
		if [ $? -gt 0 ]; then
			echo -e "Error while gzipping file $SQLFILEPATH"
			((ERROR_CNT++))
		else
			((SUCCESS_CNT++))
			PREVFILE="$SQLFILE.gz"
			for ((counter=1;counter<=$BACKUPS;counter++)); do
				STAGEFILE="${BACKUP_PREFIX}${DB_NAME}.${counter}.sql.gz"
				TMPFILE="${STAGEFILE}.tmp"
				if [ -f "${BACKUP_PATH}/${PREVFILE}" ]; then					
					if [ -f "${BACKUP_PATH}/${STAGEFILE}" ]; then
						if [ $counter -eq $BACKUPS ]; then
							rm -f "${BACKUP_PATH}/${STAGEFILE}"
						else
							mv "${BACKUP_PATH}/${STAGEFILE}" "${BACKUP_PATH}/${TMPFILE}" 
						fi
					fi					
					mv "${BACKUP_PATH}/${PREVFILE}" "${BACKUP_PATH}/${STAGEFILE}"				
				fi
				PREVFILE="$TMPFILE"
			done
		fi
	fi
done

echo -e "Successfully finished ${SUCCESS_CNT} DB Backup(s)!\n"

if [ $ERROR_CNT -gt 0 ]; then
	echo -e "But encountered ${ERROR_CNT} error(s)!\n"
	exit 1
fi

exit 0
