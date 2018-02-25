import os
import subprocess
from datetime import datetime
import json
import sqlite3
import time

import signal
import sys

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

print('Press Ctrl+C')

rules_db_name = 'rules.json'
access_log_name = 'access.log'
file_path = os.path.realpath(__file__)
dir_path = os.path.dirname(file_path)
access_log_path = os.path.join(dir_path, access_log_name)
conn = sqlite3.connect(access_log_path)
c = conn.cursor()

c.execute('create table if not exists AccessLog(dt datetime default current_timestamp, user text, data text)')

import re
from datetime import timedelta


regex = re.compile(r'((?P<hours>\d+?)hr)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')


def parse_time(time_str):
    parts = regex.match(time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)


def log_access():
	user = os.getlogin()
	c.execute('insert into AccessLog (user, data) values (?, ?)', (user, 'access'))
	conn.commit()

def shutdown():
	print('shutdown')
	#subprocess.run(['shutdown', '-l', '-f'])
	exit()

def wait():
	print('sleep')
	time.sleep(5);

def analyze(rules):
	log_access()
	exit = True
	for i in range(0,len(rules)):
		rule = rules[i]
		print('rule = ', rule)
		if is_allowed_date(rule) and is_allowed_day(rule) and is_allowed_time(rule) :
			print('why we wait:',rule)
			exit = False
	if (exit):
		shutdown()

def is_allowed_duration(rule):
	date_rules = rule.get('access-duration')
	
	conn = sqlite3.connect(access_log_path)
	c = conn.cursor()

	c.execute('select from AccessLog(dt datetime default current_timestamp, user text, data text)')

	if date_rule :
		pass

def is_allowed_date(rule):
	current_date = datetime.today()
	date_rules = rule.get('access-date')
	print('date-rules = ', date_rules)
	if(date_rules):
		print('processing-date-rules')
		for i in range(0,len(date_rules)):
			date_rule = date_rules[i]
			if isinstance(date_rule, str):
				date = datetime.strptime(date_rule, '%Y.%m.%d')
				if(current_date == date):
					print('true-rule = ',rule)
					return True
			if isinstance(date_rule, dict):
				start_date_str = date_rule.get('start')
				stop_date_str = date_rule.get('stop')
				if (start_date_str):
					start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
					if(current_date <= start_date):
						print('true-rule = ',rule)
						return True
					
				if (stop_date_str):
					stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
					if (current_date <= stop_date):
						print('true-rule = ',rule)
						return True
		return False
	return True

def is_allowed_day(rule):
	current_day = datetime.isoweekday(datetime.now())
	day_rules = rule.get('access-day')
	print('day-rules = ', day_rules)
	if(day_rules):
		for i in range(0,len(day_rules)):
			day_rule = day_rules[i]
			if isinstance(day_rule, int):
				if(current_day == day_rule):
					print('true-rule = ',rule)
					return True
			if isinstance(day_rule, dict):
				start_day = day_rule.get('start')
				stop_day = day_rule.get('stop')
				if (start_day and (current_day >= start_day)):
					print('true-rule = ',rule)
					return True
					
				if (stop_day and (current_day <= stop_day)):
					print('true-rule = ',rule)
					return True
		return False
	return True

def is_allowed_time(rule):
	current_time = datetime.now().time()
	time_rules = rule.get('access-time')
	print('time-rules = ', time_rules)
	if(time_rules):
		for i in range(0,len(time_rules)):
			time_rule = time_rules[i]
			if isinstance(time_rule, dict):
				start_time_str = time_rule.get('start')
				stop_time_str = time_rule.get('stop')
				if (start_time_str):
					start_time = datetime.strptime(start_time_str, '%H:%M').time()
					print('start_time = ', start_time)
					if(current_time >= start_time):
						print('true-rule = ',rule)
						return True
					
				if (stop_time_str):
					stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
					if (current_time <= stop_time):
						print('true-rule = ',rule)
						return True
		return False
	return True


def check_access():
	rules_db_path = os.path.join(dir_path, rules_db_name)
	rules_file = open(rules_db_path, 'r')
	rules = json.load(rules_file)
	rules_file.close()
	analyze(rules)
	
def main():
	while(True):
		check_access()
		wait()

main()