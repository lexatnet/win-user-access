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
import win32serviceutil
import win32service
import win32event
import win32ts
import win32security
import servicemanager
import socket


class AccessControlSvc (win32serviceutil.ServiceFramework):
	_svc_name_ = "AccessControlService"
	_svc_display_name_ = "Access Control Service"
	
	def __init__(self, args):
		try:
			self.userList = []
			self.log('service init args = {}'.format(args))
			self.regex = re.compile(r'((?P<hours>\d+?)hr)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')
			
			self.parseArgs()
			self.initDB()
			log('arguments = {}'.format(self.args))

			win32serviceutil.ServiceFramework.__init__(self, args)
			self.stop_event = win32event.CreateEvent(None, 0, 0, None)
			socket.setdefaulttimeout(60)
			self.stop_requested = False
			servicemanager.RegisterServiceCtrlHandler(args[0], self.serviceCtrl, True)
		except Exception as err:
			logging.error("error: {}".format(err))
			self.SvcStop()

	def parseArgs(self)
		parser = argparse.ArgumentParser(description='Restrict user acces.')
		parser.add_argument('--user', '-u', action='append', type=str, dest='users', default='user', help='user to analyze access')
		parser.add_argument('--database', '-db', type=str, dest='database', default='access.log', help='database file name')
		parser.add_argument('--rules', '-r', type=str, dest='rules', default='rules.json', help='file name with rules')
		parser.add_argument('--sleep', '-s', type=int, dest='sleep', default=60*5, help='sleep seconds between access checks')
		parser.add_argument('--debug', '-d', dest='debug', action='store_true', help='run in debug mode')
		self.args = parser.parse_args()	
	
	def parse_time(self, time_str):
		parts = self.regex.match(time_str)
		if not parts:
			return
		parts = parts.groupdict()

		time_params = {}
		for (name, param) in iter(parts.items()):
			if param:
				time_params[name] = int(param)
		return timedelta(**time_params)

	
	def log(self, message, status='info'):
		if(self.args.debug):
			print(message)
		cursor = self.conn.cursor()
		cursor.execute('insert into Log (status, user, data) values (?, ?, ?)', (status, user, message))
		self.conn.commit()

	def shutdown(self):
		self.log('shuting down')
		subprocess.run(['shutdown', '-l', '-f'])
		#self.SvcStop()
		
	def wait(self):
		sleep = self.args.sleep
		self.log('sleep {} seconds'.format(sleep))
		for sec in range(0,sleep)
			if (self.stop_requested):
				break
			time.sleep(1);
	
	def getAccesLogPath(self):
		file_path = os.path.realpath(__file__)
		dir_path = os.path.dirname(file_path)
		return os.path.join(dir_path, self.args.access_log_name)
	
	def initDB(self):
		access_log_path = self.getAccesLogPath()
		self.conn = sqlite3.connect(access_log_path)
		
		cursor = self.conn.cursor()
		cursor.execute('create table if not exists AccessLog(dt datetime default current_timestamp, user text, data text)')
		cursor.execute('create table if not exists Log(dt datetime default current_timestamp, status text, user text, data text)')

	
	
	def serviceCtrl(self, control, controlType, controlData):
		try:
			self.log('serviceCtrl control = {} , controlType = {}, controlData = {}'.format(control, controlType, controlData))
			
			if(control == win32service.SERVICE_CONTROL_STOP): 
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_STOP'))
				self.SvcStop()
			elif(control == win32service.SERVICE_CONTROL_SHUTDOWN):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_SHUTDOWN'))
				self.SvcStop()
			elif(control == win32service.SERVICE_CONTROL_SESSIONCHANGE):
				userInfo = self.GetUserInfo(controlData[0])	
				userName = userInfo['UserName']
				self.log('serviceCtrl control = {}, userInfo = {}'.format('SERVICE_CONTROL_SESSIONCHANGE', userInfo))
				types = {
					'WTS_CONSOLE_CONNECT': 0x1,# The session identified by lParam was connected to the console terminal or RemoteFX session.
					'WTS_CONSOLE_DISCONNECT': 0x2 # The session identified by lParam was disconnected from the console terminal or RemoteFX session.
					'WTS_REMOTE_CONNECT': 0x3 # The session identified by lParam was connected to the remote terminal.
					'WTS_REMOTE_DISCONNECT': 0x4 # The session identified by lParam was disconnected from the remote terminal.
					'WTS_SESSION_LOGON': 0x5 # A user has logged on to the session identified by lParam.
					'WTS_SESSION_LOGOFF': 0x6 # A user has logged off the session identified by lParam.
					'WTS_SESSION_LOCK': 0x7 # The session identified by lParam has been locked.
					'WTS_SESSION_UNLOCK': 0x8 # The session identified by lParam has been unlocked.
					'WTS_SESSION_REMOTE_CONTROL': 0x9 # The session identified by lParam has changed its remote controlled status. To determine the status, call GetSystemMetrics and check the SM_REMOTECONTROL metric.
					'WTS_SESSION_CREATE': 0xA # Reserved for future use.
					'WTS_SESSION_TERMINATE': 0xB # Reserved for future use.
				}
				if(controlType == types.WTS_SESSION_LOGON):
					self.startCheckingForUser(userName)
				elif(controlType == types.WTS_SESSION_LOGOFF):
					self.stopCheckingForUser(userName)
				elif(controlType == types.WTS_SESSION_LOCK):
					self.stopCheckingForUser(userName)
				elif(controlType == types.WTS_SESSION_UNLOCK):
					self.startCheckingForUser(userName)
					
					
			elif(control == win32service.SERVICE_CONTROL_PRESHUTDOWN):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_PRESHUTDOWN'))
			elif(control == win32service.SERVICE_CONTROL_CONTINUE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_CONTINUE'))
			elif(control == win32service.SERVICE_CONTROL_POWEREVENT):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_POWEREVENT'))
			elif(control == win32service.SERVICE_CONTROL_DEVICEEVENT):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_DEVICEEVENT'))
			elif(control == win32service.SERVICE_CONTROL_HARDWAREPROFILECHANGE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_HARDWAREPROFILECHANGE'))
			elif(control == win32service.SERVICE_CONTROL_INTERROGATE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_INTERROGATE'))
			elif(control == win32service.SERVICE_CONTROL_NETBINDADD):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_NETBINDADD'))
			elif(control == win32service.SERVICE_CONTROL_NETBINDDISABLE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_NETBINDDISABLE'))
			elif(control == win32service.SERVICE_CONTROL_NETBINDENABLE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_NETBINDENABLE'))
			elif(control == win32service.SERVICE_CONTROL_NETBINDREMOVE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_NETBINDREMOVE'))
			elif(control == win32service.SERVICE_CONTROL_PARAMCHANGE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_PARAMCHANGE'))
			elif(control == win32service.SERVICE_CONTROL_PAUSE):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_PAUSE'))
			elif(control == win32service.SERVICE_CONTROL_POWEREVENT):
				self.log('serviceCtrl control = {}'.format('SERVICE_CONTROL_POWEREVENT'))
		except Exception as err:
			logging.error(err)
			self.SvcStop()

	def startCheckingForUser(self, userName):
		self.userList.append(userName)
	
	def stopCheckingForUser(self, userName):
		self.userList.remove(userName)
	

	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.stop_event)
		self.log('Stopping service ...')
		self.stop_requested = True

	def SvcDoRun(self):
		servicemanager.LogMsg(
			servicemanager.EVENTLOG_INFORMATION_TYPE,
			servicemanager.PYS_SERVICE_STARTED,
			(self._svc_name_,'')
		)
		self.main()
		self.ReportServiceStatus(win32service.SERVICE_STOPPED)
			
	def GetUserInfo(self, sess_id):
		sessions = win32security.LsaEnumerateLogonSessions()[:-5]
		for sn in sessions:
			sn_info = win32security.LsaGetLogonSessionData(sn)
			if sn_info['Session'] == sess_id:
				return sn_info

	def GetAcceptedControls(self):
		# Accept SESSION_CHANGE control
		try:
			rc = win32serviceutil.ServiceFramework.GetAcceptedControls(self)
			rc |= win32service.SERVICE_ACCEPT_SESSIONCHANGE
			return rc
		except Exception as err:
			logging.error(err)
	
	def main(self):
		self.log(' ** Hello PyWin32 World ** ')
		# Simulate a main loop
		while(True):
			if self.stop_requested:
				self.log('A stop signal was received: Breaking main loop ...')
				break
			rules = get_access_rules()
			for userName in self.userList:
				self.log_access(userName)
				if(userName in self.args.users):
					self.check_access(userName, rules)
			self.wait()
		self.log('service finished.')
		return
		
	def log_access(self, userName):
		cursor = self.conn.cursor()
		cursor.execute('insert into AccessLog (user, data) values (?, ?)', (userName, 'access'))
		self.conn.commit()

	def get_access_time(self, rule):
		access_log = self.get_access_log_for_rule(rule)
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

	def get_access_log_for_rule(self, rule):
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
		cursor = self.conn.cursor()
		cursor.execute(query)
		return cursor.fetchall()

	def is_allowed_duration(self, rule):
		log('check access duration')
		duration_rule_str = rule.get('access-duration')
		if (duration_rule_str) :
			duration_rule = self.parse_time(duration_rule_str)
			access_time = self.get_access_time(rule)
			self.log('access time = {}'.format(access_time))
			self.log('duration rule = {}'.format(duration_rule))
			if access_time < duration_rule :
				self.log('duration rule access success')
				return True
		self.log('duration rule access denied')
		return False

	def is_allowed_date(self, rule):
		self.log('check access date')
		current_date = datetime.today()
		self.log('current date {}'.format(current_date))
		date_rules = rule.get('access-date')
		if(date_rules):
			for date_rule in date_rules:
				if isinstance(date_rule, str):
					date = datetime.strptime(date_rule, '%Y.%m.%d')
					if(current_date == date):
						self.log('date rule access success')
						return True
				if isinstance(date_rule, dict):
					start_date_str = date_rule.get('start')
					stop_date_str = date_rule.get('stop')
					if (start_date_str and stop_date_str) :
						start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
						self.log('start date {}'.format(start_date))
						stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
						self.log('stop date {}'.format(stop_date))
						if (current_date <= stop_date) and (current_date >= start_date):
							self.log('date rule access success')
							return True
					elif (start_date_str and not stop_date_str):
						start_date = datetime.strptime(start_date_str, '%Y.%m.%d')
						self.log('start date {}'.format(start_date))
						if(current_date >= start_date):
							log('date rule access success')
							return True
						
					elif (not start_date_str and stop_date_str):
						stop_date = datetime.strptime(stop_date_str, '%Y.%m.%d')
						self.log('stop date {}'.format(stop_date))
						if (current_date <= stop_date):
							self.log('date rule access success')
							return True
			self.log('date rule access denied')
			return False
		self.log('date rule skiped')
		return True

	def analyze(self, userName, rules):
		exit = True
		for rule in rules:
			self.log('check rule = {}'.format(rule))
			if (
				self.is_allowed_date(rule) 
				and self.is_allowed_day(rule) 
				and self.is_allowed_time(rule) 
				and self.is_allowed_duration(rule)
				) :
				self.log('all parts access rules success')
				exit = False
				break
			else:
				self.log('one part of rule is deny access')
		if (exit):
			self.log('no rules to grant access')
			self.shutdown()

	def is_allowed_day(self, rule):
		self.log('check access day')
		current_day = datetime.isoweekday(datetime.now())
		self.log('current day {}'.format(current_day))
		day_rules = rule.get('access-day')
		if(day_rules):
			for day_rule in day_rules:
				if isinstance(day_rule, int):
					self.log('day rule {}'.format(day_rule))
					if(current_day == day_rule):
						self.log('day rule access success')
						return True
				if isinstance(day_rule, dict):
					start_day = day_rule.get('start')
					self.log('start day {}'.format(start_day))
					stop_day = day_rule.get('stop')
					self.log('stop day {}'.format(stop_day))
					if (start_day and stop_day and (current_day >= start_day) and (current_day <= stop_day)):
						self.log('day rule access success')
						return True

					elif (start_day and not stop_day and (current_day >= start_day)):
						self.log('day rule access success')
						return True
						
					elif (not start_day and stop_day and(current_day <= stop_day)):
						self.log('day rule access success')
						return True
			self.log('day rule access denied')
			return False
		self.log('day rule skiped')
		return True

	def is_allowed_time(self, rule):
		self.log('check access time')
		current_time = datetime.now().time()
		self.log('current time {}'.format(current_time))
		time_rules = rule.get('access-time')
		if(time_rules):
			for i in range(0,len(time_rules)):
				time_rule = time_rules[i]
				if isinstance(time_rule, dict):
					start_time_str = time_rule.get('start')
					stop_time_str = time_rule.get('stop')
					if (start_time_str and stop_time_str):
						start_time = datetime.strptime(start_time_str, '%H:%M').time()
						self.log('start time {}'.format(start_time))
						stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
						self.log('stop time {}'.format(stop_time))
						if (current_time <= stop_time) and (current_time >= start_time):
							self.log('time rule access success')
							return True
						
					elif (start_time_str and not stop_time_str):
						start_time = datetime.strptime(start_time_str, '%H:%M').time()
						self.log('start_time = {}'.format(start_time))
						if(current_time >= start_time):
							self.log('time rule access success')
							return True
						
					elif (not start_time_str and stop_time_str):
						stop_time = datetime.strptime(stop_time_str, '%H:%M').time()
						if (current_time <= stop_time):
							self.log('time rule access success')
							return True
			self.log('time rule access denied')
			return False
		self.log('time rule skiped')
		return True

	def get_access_rules(self):
		rules_db_path = os.path.join(dir_path, self.args.rules_db_name)
		rules_file = open(rules_db_path, 'r')
		rules = json.load(rules_file)
		rules_file.close()
		return rules;

	def check_access(self, userName, rules):
			self.analyze(userName, rules)

if __name__ == '__main__':
	try :
		win32serviceutil.HandleCommandLine(AccessControlSvc)
	except Exception as err:
		print("error: {}".format(err))
		

def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


print('Press Ctrl+C')
