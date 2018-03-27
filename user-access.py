import os
import subprocess
from datetime import datetime
import json
import sqlite3
import time
import argparse
import signal
import sys
import re
from datetime import timedelta


parser = argparse.ArgumentParser(description='Restrict user acces.')
parser.add_argument('--user', '-u', type=str, dest='user', default='user', help='user to analyze access')
parser.add_argument('--database', '-db', type=str, dest='database', default='access.log', help='database file name')
parser.add_argument('--rules', '-r', type=str, dest='rules', default='rules.json', help='file name with rules')
parser.add_argument('--sleep', '-s', type=int, dest='sleep', default=60*5, help='sleep seconds between access checks')
parser.add_argument('--debug', '-d', dest='debug', action='store_true', help='run in debug mode')
args = parser.parse_args()


user = args.user
rules_db_name = args.rules
access_log_name = args.database
sleep = args.sleep
debug = args.debug


file_path = os.path.realpath(__file__)
dir_path = os.path.dirname(file_path)
access_log_path = os.path.join(dir_path, access_log_name)
conn = sqlite3.connect(access_log_path)
c = conn.cursor()


c.execute('create table if not exists AccessLog(dt datetime default current_timestamp, user text, data text)')
c.execute('create table if not exists Log(dt datetime default current_timestamp, status text, user text, data text)')


def log(message, status='info'):
	if(debug):
		print(message)
	c.execute('insert into Log (status, user, data) values (?, ?, ?)', (status, user, message))
	conn.commit()


log('arguments = {}'.format(args))
	

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


print('Press Ctrl+C')


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
	c.execute('insert into AccessLog (user, data) values (?, ?)', (user, 'access'))
	conn.commit()

	
def shutdown():
	log('shuting down')
	#subprocess.run(['shutdown', '-l', '-f'])
	exit()

	
def wait():
	log('sleep {} seconds'.format(sleep))
	time.sleep(sleep);

	
def analyze(rules):
	exit = True
	for rule in rules:
		log('check rule = {}'.format(rule))
		if (
			is_allowed_date(rule) 
			and is_allowed_day(rule) 
			and is_allowed_time(rule) 
			and is_allowed_duration(rule)
			) :
			log('all parts access rules success')
			exit = False
			break
		else:
			log('one part of rule is deny access')
	if (exit):
		log('no rules to grant access')
		shutdown()
	
	
def get_access_time(rule):
	access_log = get_access_log_for_rule(rule)
	access_time = timedelta()
	prev_time = False
	while len(access_log) > 0: 
		rec = access_log.pop()
		rec_date = datetime.strptime(rec[0], '%Y-%m-%d %H:%M:%S')
		if (prev_time):
			if((prev_time - rec_date) < timedelta(seconds = sleep*2)):
				access_time += (prev_time - rec_date)
		prev_time = rec_date
	return access_time


def get_access_log_for_rule(rule):
	conn = sqlite3.connect(access_log_path)
	c = conn.cursor()
	date_rules = rule.get('access-date')
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
	
	c.execute(query)
	return c.fetchall()


def is_allowed_duration(rule):
	log('check access duration')
	duration_rule_str = rule.get('access-duration')
	if (duration_rule_str) :
		duration_rule = parse_time(duration_rule_str)
		access_time = get_access_time(rule)
		log('access time = {}'.format(access_time))
		log('duration rule = {}'.format(duration_rule))
		if access_time < duration_rule :
			log('duration rule access success')
			return True
	log('duration rule access denied')
	return False


def is_allowed_date(rule):
	log('check access date')
	current_date = datetime.today()
	log('current date {}'.format(current_date))
	date_rules = rule.get('access-date')
	if(date_rules):
		for date_rule in date_rules:
			if isinstance(date_rule, str):
				date = datetime.strptime(date_rule, '%Y.%m.%d')
				if(current_date == date):
					log('date rule access success')
					return True
			if isinstance(date_rule, dict):
				start_date_str = date_rule.get('start')
				stop_date_str = date_rule.get('stop')
				if (start_date_str and stop_date_str) :
					start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
					log('start date {}'.format(start_date))
					stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
					log('stop date {}'.format(stop_date))
					if (current_date <= stop_date) and (current_date >= start_date):
						log('date rule access success')
						return True
				elif (start_date_str and not stop_date_str):
					start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
					log('start date {}'.format(start_date))
					if(current_date >= start_date):
						log('date rule access success')
						return True
					
				elif (not start_date_str and stop_date_str):
					stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
					log('stop date {}'.format(stop_date))
					if (current_date <= stop_date):
						log('date rule access success')
						return True
		log('date rule access denied')
		return False
	log('date rule skiped')
	return True


def is_allowed_day(rule):
	log('check access day')
	current_day = datetime.isoweekday(datetime.now())
	log('current day {}'.format(current_day))
	day_rules = rule.get('access-day')
	if(day_rules):
		for day_rule in day_rules:
			if isinstance(day_rule, int):
				log('day rule {}'.format(day_rule))
				if(current_day == day_rule):
					log('day rule access success')
					return True
			if isinstance(day_rule, dict):
				start_day = day_rule.get('start')
				log('start day {}'.format(start_day))
				stop_day = day_rule.get('stop')
				log('stop day {}'.format(stop_day))
				if (start_day and stop_day and (current_day >= start_day) and (current_day <= stop_day)):
					log('day rule access success')
					return True

				elif (start_day and not stop_day and (current_day >= start_day)):
					log('day rule access success')
					return True
					
				elif (not start_day and stop_day and(current_day <= stop_day)):
					log('day rule access success')
					return True
		log('day rule access denied')
		return False
	log('day rule skiped')
	return True


def is_allowed_time(rule):
	log('check access time')
	current_time = datetime.now().time()
	log('current time {}'.format(current_time))
	time_rules = rule.get('access-time')
	if(time_rules):
		for i in range(0,len(time_rules)):
			time_rule = time_rules[i]
			if isinstance(time_rule, dict):
				start_time_str = time_rule.get('start')
				stop_time_str = time_rule.get('stop')
				if (start_time_str and stop_time_str):
					start_time = datetime.strptime(start_time_str, '%H:%M').time()
					log('start time {}'.format(start_time))
					stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
					log('stop time {}'.format(stop_time))
					if (current_time <= stop_time) and (current_time >= start_time):
						log('time rule access success')
						return True
					
				elif (start_time_str and not stop_time_str):
					start_time = datetime.strptime(start_time_str, '%H:%M').time()
					log('start_time = {}'.format(start_time))
					if(current_time >= start_time):
						log('time rule access success')
						return True
					
				elif (not start_time_str and stop_time_str):
					stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
					if (current_time <= stop_time):
						log('time rule access success')
						return True
		log('time rule access denied')
		return False
	log('time rule skiped')
	return True


def check_access(rules):
	analyze(rules)


def get_access_rules():
	rules_db_path = os.path.join(dir_path, rules_db_name)
	rules_file = open(rules_db_path, 'r')
	rules = json.load(rules_file)
	rules_file.close()
	return rules;


def main():
	rules = get_access_rules()
	while(True):
		log_access()
		check_access(rules)
		wait()

try:
	main()
except Exception as error:
	log(error)