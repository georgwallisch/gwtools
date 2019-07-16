#!/bin/bash
if [ -d "$1" ]; then
	echo Starting at $1
	echo with directories..
	find "$1" -type d -exec chmod 755 {} \;
	echo now files..
	find "$1" -type f -exec chmod 644 {} \;
	echo finished!
else 
	echo $! is not a directory!
fi

