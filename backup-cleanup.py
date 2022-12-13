#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from datetime import date
from datetime import datetime
import sys
import subprocess
import argparse
import smbclient


parser = argparse.ArgumentParser()
parser.add_argument("-d", "--delete", help="really delete unnecessary files", action="store_true")
parser.add_argument("--dry", help="dont delete anything", action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")

# Stage rules
# Die letzten n Sicherungen
parser.add_argument('-ln', '--stage_last_num', "Number of recent backups to keep at least", default = 5)
# Die Sicherungen der letzten n Tage
parser.add_argument('-ld', '--stage_last_days', "Keep backups of at least n days", default = 14)
# Die jeweils letzte Sicherung der n vergangenen Wochen
parser.add_argument('-lw', '--stage_last_weeks', "Keep the newest backups of each week from the last n weeks", default = 6)
# Die letzte Sicherung der n vergangenen Monate
parser.add_argument('-lm', '--stage_last_months', "Keep the newest backups of each month from the last n months", default = 12)
# Die letzte Sicherung der n vergangenen Jahre
parser.add_argument('-ly', '--stage_last_years', "Keep the newest backups of each year from the last n year", default = 5)

# Dateiname-Regex
parser.add_argument('-f', '--file_name', "Regular expression of the filename", default = ".+")

# Pfad
parser.add_argument('path', "Path of backup directory")

# SMB Benutzername
parser.add_argument('-u', '--username', "SMB username")
# SMB Passwort
parser.add_argument('-p', '--password', "SMB password")

args = parser.parse_args()

tokeep = []
todelete = []
today = date.today()