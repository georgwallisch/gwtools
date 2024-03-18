#!/usr/bin/python3
# -*- coding: utf-8 -*-

""" Backup files cleanup script
"""

__author__ = "Georg Wallisch"
__contact__ = "gw@phpco.de"
__copyright__ = "Copyright © 2024 by Georg Wallisch"
__credits__ = ["Georg Wallisch"]
__date__ = "2024/03/18"
__deprecated__ = False
__email__ =  "gw@phpco.de"
__license__ = "Proprietary software"
__maintainer__ = "Georg Wallisch"
__status__ = "beta"
__version__ = "0.1"

import os
#import time
#import datetime
from datetime import date
from datetime import datetime
import sys
import subprocess
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--DEBUG", help="ONLY FOR DEBUGGING", action="store_true")
parser.add_argument("-d", "--delete", help="really delete unnecessary backup files", action="store_true")
parser.add_argument("--dry", help="don't delete anything", action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("backupdir", help="path where backup files located")
parser.add_argument("-p", "--prefix", help="backup filename starts with", default='LaborBak-')
parser.add_argument("-s", "--suffix", help="backup filename ends with", default='Labz')
args = parser.parse_args()

# Behalteregeln
# Die letzten n Sicherungen
stage_last_num = 5
# Die Sicherungen der letzten n Tage
stage_last_days = 14
# Die jeweils letzte Sicherung der n vergangenen Wochen
stage_last_weeks = 6
# Die letzte Sicherung der n vergangenen Monate
stage_last_months = 12
# Die letzte Sicherung der n vergangenen Jahre
stage_last_years = 2


dasidir = args.backupdir
dasiprefix = args.prefix
plen = len(dasiprefix)
dasisuffix = args.suffix
filelist = []
tokeep = []
todelete = []
today = date.today()

try:
	
	print("\n#########################\n#   DaSi-Cleanup v{}   #\n#########################\n".format(__version__))
	
	if args.DEBUG:
		print("\n### DEBUG MODE###\n")
	
	if args.verbose:
		print("Prefix: {}".format(dasiprefix))
		print("Suffix: {}".format(dasisuffix))
		
	for filename in os.listdir(dasidir):
		if filename.startswith(dasiprefix):
			if filename.endswith(dasisuffix):				
				filelist.append(filename)
			
	filelist.sort(reverse=True)
	
	i = 0
	m = -1
	w = -1
	y = -1
	
	if args.verbose:
		print("{} Datensicherungsdateien gefunden".format(len(filelist)))
	
	for filename in filelist:
		i += 1
		try:
			d = datetime.strptime(filename[plen:plen+10], '%Y-%m-%d').date()
		except:
			continue
			
		if i <= stage_last_num:
			if args.verbose:
				print("{} OK (n <= {})".format(filename, stage_last_num))
			tokeep.append(filename)
			m = d.month
			w = d.isocalendar()[1]
			y = d.year
			continue

		#d = date.fromtimestamp(datetime.strptime(subvol[5:5+10], '%Y-%m-%d'))
		#print subvol[5:5+10]
		
		#print 'm={} d={}'.format(m, d.month)
		
		diff = abs((today - d).days)
		if diff <= stage_last_days:
			if args.verbose:
				print('{} OK ({} <= {} Tage)'.format(filename, diff, stage_last_days))
			tokeep.append(filename)
			w = d.isocalendar()[1]
			m = d.month			
			y = d.year
			continue
			
		wdiff = today.isocalendar()[1] - d.isocalendar()[1] + (today.year - d.year)*52
		if w != d.isocalendar()[1] and wdiff <= stage_last_weeks:
			if args.verbose:
				print('{} OK ({} <= {} Wochen)'.format(filename, wdiff, stage_last_weeks))
			tokeep.append(filename)
			m = d.month
			w = d.isocalendar()[1]
			y = d.year
			continue
		
		mdiff = today.month - d.month + (today.year - d.year)*12
		if m != d.month and mdiff <= stage_last_months:
			if args.verbose:
				print('{} OK ({} <= {} Monate)'.format(filename, mdiff, stage_last_months))
			tokeep.append(filename)
			m = d.month
			y = d.year
			continue
		
		ydiff = today.year - d.year
		if y != d.year and ydiff <= stage_last_years:
			if args.verbose:
				print('{} OK ({} <= {} Jahre)'.format(filename, ydiff, stage_last_years))
			tokeep.append(filename)
			y = d.year
			continue
			
		if args.verbose:	
			print('{} kann weg'.format(filename))
		todelete.append(filename)
		
		if args.delete:
			p = dasidir + '/' + filename
			if args.dry:
				print(p)
			else:
				os.remove(p)				
				
	if args.delete and not args.dry:	
		print("\nVon {} Datensicherungsdateien sind {} OK und {} wurden gelöscht.".format(len(filelist), len(tokeep), len(todelete)))
	else:
		print("\nVon {} Datensicherungsdateien sind {} OK und {} können gelöscht werden.".format(len(filelist), len(tokeep), len(todelete)))
		
	print("\n..fertig!\n")	
	    
except OSError as err:
    print("OS error: {0}".format(err))