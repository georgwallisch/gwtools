#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import io
import re
import sys
import time
import argparse
from pilight import pilight


def handle_code(code):	# Simply  print received data from pilight
	global args

	msg = code['message']
	
	if args.verbose:
		print "Got code"
		
	if args.raw:
		print(code)
	else:
		if args.protocol:
			searchObj = re.search(args.protocol, code['protocol'], re.M|re.I)
			if searchObj:
				if args.verbose:
					print "Got right Protocol"
			else:
				if args.verbose:
					print "Wrong Protocol"
				return
				
		mkey = True
		
		if args.message_key == True:
			mkey = False
		
		s = "{0}:\t".format(code['protocol'])
		
		for k, v in msg.iteritems():
			if args.message_key == k:
				mkey = True
			s += "{0}: {1}, ".format(k,v)
	
		if mkey == True:
			print s
		elif args.blink:			
			print "."
		elif args.verbose:
			print "Message key not found"

# pylint: disable=C0103
def main():
	global args

	pilight_client = None
	
	try:
		parser = argparse.ArgumentParser(description='Test for 433Mhz sensors')
		parser.add_argument('--raw', help='show raw sensor readings', action="store_true")
		parser.add_argument('-S' , '--server', help='Server to connect with pilight daemon', default='127.0.0.1')
		parser.add_argument('-P' , '--port', help='Port to connect with pilight daemon', default=5000)
		parser.add_argument('-p' , '--protocol', help='show only sensor readings with this protocol')
		parser.add_argument('-m' , '--message-key', help='show only sensor readings containing this key in the message')
		parser.add_argument('-v' , '--verbose', help='show verbose output', action="store_true")
		parser.add_argument('--blink', help='say anything on receiving', action="store_true")
	
		args = parser.parse_args()
		
		server433 = args.server
		port433 = args.port

		print "\n*** gw 433Mhz Testprogramm zum Sensorempfang ***"
		print "Verbinde zu pilight-daemon an {0} über Port {1}\n".format(server433, port433)
		# Create new pilight connection
		pilight_client = pilight.Client(host=server433, port=port433)
		
		# Set a data handle that is called on received data
		pilight_client.set_callback(handle_code)
		pilight_client.start()	# Start the receiver		
		print "Beginne Überwachung..\n"
		if args.raw:
			print "Zeige Rohdaten..\n"
		
		while True:			
			time.sleep(5)		

	except KeyboardInterrupt:
		print "\nAbbruch durch Benutzer Ctrl+C\n"
	except RuntimeError,e:
		print "RuntimeError {0}".format(e)
	except:
		print "Unexpected error:", sys.exc_info()[0]
	finally:
		if pilight_client:
			pilight_client.stop() # Stop the receiver
		
if __name__ == "__main__":
	main()