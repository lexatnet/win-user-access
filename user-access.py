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
    for (name, param) in iter(parts.items()):
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
	time.sleep(30);

def analyze(rules):
	log_access()
	exit = True
	for rule in rules:
		print('check rule = ', rule)
		if is_allowed_date(rule) and is_allowed_day(rule) and is_allowed_time(rule) and is_allowed_duration(rule) :
			print('why we wait:',rule)
			print('is_allowed_date(rule)', is_allowed_date(rule))
			print('is_allowed_day(rule)', is_allowed_day(rule))
			print('is_allowed_time(rule)', is_allowed_time(rule))
			print('is_allowed_duration(rule)', is_allowed_duration(rule))
			exit = False
			break
	if (exit):
		shutdown()
		
def get_access_time(rule):
	access_log = get_access_log_for_rule(rule)
	#print('access_log = ', access_log)
	access_time = timedelta()
	prev_time = False
	while len(access_log) > 0: 
		rec = access_log.pop()
		rec_date = datetime.strptime(rec[0], '%Y-%m-%d %H:%M:%S')
		if (prev_time):
			if((prev_time - rec_date) < timedelta(minutes = 10)):
				access_time += (prev_time - rec_date)
		prev_time = rec_date
	return access_time

def get_access_log_for_rule(rule):
	conn = sqlite3.connect(access_log_path)
	c = conn.cursor()
	date_rules = rule.get('access-date')
	user = os.getlogin()
	conditions = []
	for date_rule in date_rules:
		if isinstance(date_rule, str):
			date = datetime.strptime(date_rule, '%Y.%m.%d')
			conditions.append('((dt >= "{}") and (dt <= "{}"))'.format(date, date));
		if isinstance(date_rule, dict):
			subconditions = []
			
			start_date_str = date_rule.get('start')
			stop_date_str = date_rule.get('stop')
			
			if (start_date_str):
				start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
				subconditions.append('(dt >= "{}")'.format(start_date))
				
			if (stop_date_str):
				stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
				subconditions.append('(dt <= "{}")'.format(stop_date))
				
			conditions.append('({})'.format(' and '.join(subconditions)))

	time_rules = rule.get('access-time')
	if(time_rules):
		for time_rule in time_rules:
			if isinstance(time_rule, dict):
				start_time_str = time_rule.get('start')
				stop_time_str = time_rule.get('stop')
				subconditions = []
					
				if (start_time_str):
					start_time = datetime.strptime(start_time_str, '%H:%M').strftime('%H:%M')
					subconditions.append('(strftime("%H:%M", dt) >= "{}")'.format(start_time))
				
				if (stop_time_str):
					stop_time = datetime.strptime(stop_time_str, '%H:%M').strftime('%H:%M')
					subconditions.append('(strftime("%H:%M", dt) <= "{}")'.format(stop_time))
				
				conditions.append('({})'.format(' and '.join(subconditions)))
	
	day_rules = rule.get('access-day')
	if(day_rules):
		for day_rule in day_rules:
			if isinstance(day_rule, int):
				conditions.append('( strftime("%w", dt)) = {}'.format(day_rule))
			if isinstance(day_rule, dict):
				start_day = day_rule.get('start')
				stop_day = day_rule.get('stop')
				subconditions = []
				if (start_day):
					subconditions.append('( strftime("%w", dt)) >= {}'.format(start_day))
					
				if (stop_day):
					subconditions.append('( strftime("%w", dt)) <= {}'.format(stop_day))
			
				conditions.append('({})'.format(' and '.join(subconditions)))
	
	query = 'select * from AccessLog where (user = "{}") and ({}) order by dt asc'.format(user, ' or '.join(conditions))
	
	#print('query', query)
	
	c.execute(query)
	return c.fetchall()

def is_allowed_duration(rule):
	print('check duration')
	date_rule_str = rule.get('access-duration')
	if (date_rule_str) :
		date_rule = parse_time(date_rule_str)
		access_time = get_access_time(rule)
		print('access_time', access_time)
		if access_time < date_rule :
			return True
	return False

def is_allowed_date(rule):
	print('check date')
	current_date = datetime.today()
	date_rules = rule.get('access-date')
	if(date_rules):
		for date_rule in date_rules:
			if isinstance(date_rule, str):
				date = datetime.strptime(date_rule, '%Y.%m.%d')
				if(current_date == date):
					return True
			if isinstance(date_rule, dict):
				start_date_str = date_rule.get('start')
				stop_date_str = date_rule.get('stop')
				if (start_date_str and stop_date_str) :
					start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
					stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
					if (current_date <= stop_date) and (current_date >= start_date):
						return True
				elif (start_date_str and not stop_date_str):
					start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
					if(current_date >= start_date):
						return True
					
				elif (not start_date_str and stop_date_str):
					stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
					if (current_date <= stop_date):
						return True
		return False
	return True

def is_allowed_day(rule):
	print('check day')
	current_day = datetime.isoweekday(datetime.now())
	day_rules = rule.get('access-day')
	if(day_rules):
		for day_rule in day_rules:
			if isinstance(day_rule, int):
				if(current_day == day_rule):
					return True
			if isinstance(day_rule, dict):
				start_day = day_rule.get('start')
				stop_day = day_rule.get('stop')
				if (start_day and stop_day and (current_day >= start_day) and (current_day <= stop_day)):
					print('both days')
					return True

				elif (start_day and not stop_day and (current_day >= start_day)):
					return True
					
				elif (not start_day and stop_day and(current_day <= stop_day)):
					return True
		return False
	return True

def is_allowed_time(rule):
	print('check time')
	current_time = datetime.now().time()
	time_rules = rule.get('access-time')
	if(time_rules):
		for i in range(0,len(time_rules)):
			time_rule = time_rules[i]
			if isinstance(time_rule, dict):
				start_time_str = time_rule.get('start')
				stop_time_str = time_rule.get('stop')
				if (start_time_str and stop_time_str):
					start_time = datetime.strptime(start_time_str, '%H:%M').time()
					stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
					if (current_time <= stop_time) and (current_time >= start_time):
						return True
					
				elif (start_time_str and not stop_time_str):
					start_time = datetime.strptime(start_time_str, '%H:%M').time()
					print('start_time = ', start_time)
					if(current_time >= start_time):
						return True
					
				elif (not start_time_str and stop_time_str):
					stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
					if (current_time <= stop_time):
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