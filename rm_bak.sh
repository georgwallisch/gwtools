#!/bin/bash

echo -e "\n*** Recursively remove jEdit backup files (file~) script ***\n" 

if [ ! -d "$1" ]; then
	echo -e "No start path given!\n\nUsage: $0 [PATH]\n"
	exit 1
fi

echo -e "Starting at '$1'\n"

find $1 -type f -name "*~" -delete

echo -e "..done!\n"

exit 0
