#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
#import time
#import datetime
from datetime import date
from datetime import datetime
import sys
import subprocess
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--delete", help="realy delete unnecessary subvolumes", action="store_true")
parser.add_argument("--dry", help="dont delete anything", action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
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
stage_last_years = 5


dasidir = '/mnt/hyperspace'
dasiprefix = 'DaSi-'
subvolumes = []
tokeep = []
todelete = []
today = date.today()

try:
	
	for filename in os.listdir(dasidir):
		if filename.startswith(dasiprefix):
			#print filename
			subvolumes.append(filename)
			
	subvolumes.sort(reverse=True)
	
	i = 0
	m = -1
	w = -1
	y = -1
	
	for subvol in subvolumes:
		i += 1
		try:
			d = datetime.strptime(subvol[5:5+10], '%Y-%m-%d').date()
		except:
			continue
			
		if i <= stage_last_num:
			if args.verbose:
				print "{} OK (n <= {})".format(subvol, stage_last_num)
			tokeep.append(subvol)
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
				print '{} OK ({} <= {} Tage)'.format(subvol, diff, stage_last_days)
			tokeep.append(subvol)
			w = d.isocalendar()[1]
			m = d.month			
			y = d.year
			continue
			
		wdiff = today.isocalendar()[1] - d.isocalendar()[1] + (today.year - d.year)*52
		if w != d.isocalendar()[1] and wdiff <= stage_last_weeks:
			if args.verbose:
				print '{} OK ({} <= {} Wochen)'.format(subvol, wdiff, stage_last_weeks)
			tokeep.append(subvol)
			m = d.month
			w = d.isocalendar()[1]
			y = d.year
			continue
		
		mdiff = today.month - d.month + (today.year - d.year)*12
		if m != d.month and mdiff <= stage_last_months:
			if args.verbose:
				print '{} OK ({} <= {} Monate)'.format(subvol, mdiff, stage_last_months)
			tokeep.append(subvol)
			m = d.month
			y = d.year
			continue
		
		ydiff = today.year - d.year
		if y != d.year and ydiff <= stage_last_years:
			if args.verbose:
				print '{} OK ({} <= {} Jahre)'.format(subvol, ydiff, stage_last_years)
			tokeep.append(subvol)
			y = d.month
			continue
			
		if args.verbose:	
			print '{} kann weg'.format(subvol)
		todelete.append(subvol)
		
		if args.delete:
			p = dasidir + '/' + subvol
			if args.dry:
				print p
			else:
				subprocess.call(['btrfs','subvolume','delete',p])				
				
	if args.delete and not args.dry:	
		print "Von {} Subvolumes sind {} OK und {} wurden gelöscht".format(len(subvolumes), len(tokeep), len(todelete))
	else:
		print "Von {} Subvolumes sind {} OK und {} können gelöscht werden".format(len(subvolumes), len(tokeep), len(todelete))
    
except OSError as err:
    print("OS error: {0}".format(err))