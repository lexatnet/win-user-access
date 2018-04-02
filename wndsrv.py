import win32serviceutil
import win32service
import win32event
import win32ts
import win32security
import servicemanager
import socket
import time
import logging

logging.basicConfig(
	filename = 'c:\\Temp\\hello-service.log',
	level = logging.DEBUG, 
	format = '[helloworld-service] %(levelname)-7.7s %(message)s'
)


class HelloWorldSvc (win32serviceutil.ServiceFramework):
	_svc_name_ = "HelloWorld-Service"
	_svc_display_name_ = "HelloWorld Service"
	
	def __init__(self,args):
		self.userList = []
		logging.info('service init args = {}'.format(args))
		try:
			win32serviceutil.ServiceFramework.__init__(self,args)
			self.stop_event = win32event.CreateEvent(None,0,0,None)
			socket.setdefaulttimeout(60)
			self.stop_requested = False
			servicemanager.RegisterServiceCtrlHandler(args[0], self.serviceCtrl, True)
		except Exception as err:
			logging.error("error: {}".format(err))
		
	def serviceCtrl(self, control, controlType, controlData):
		args = (control, controlType, controlData)
		
		svcCtrls = [
		'SERVICE_CONTROL_DEVICEEVENT',
		'SERVICE_CONTROL_HARDWAREPROFILECHANGE',
		'SERVICE_CONTROL_INTERROGATE',
		'SERVICE_CONTROL_NETBINDADD',
		'SERVICE_CONTROL_NETBINDDISABLE',
		'SERVICE_CONTROL_NETBINDENABLE',
		'SERVICE_CONTROL_NETBINDREMOVE',
		'SERVICE_CONTROL_PARAMCHANGE',
		'SERVICE_CONTROL_PAUSE',
		'SERVICE_CONTROL_POWEREVENT'
		]
		
		logging.info('serviceCtrl control = {} , controlType = {}, controlData = {}, userInfo = {}'.format(control, controlType, controlData, self.GetUserInfo(controlData[0])))
		
		if(control == win32service.SERVICE_CONTROL_STOP): 
			logging.info('serviceCtrl control = {}'.format('SERVICE_CONTROL_STOP'))
			self.SvcStop()
		elif(control == win32service.SERVICE_CONTROL_SHUTDOWN):
			logging.info('serviceCtrl control = {}'.format('SERVICE_CONTROL_SHUTDOWN'))
			self.SvcStop()
		elif(control == win32service.SERVICE_CONTROL_SESSIONCHANGE):
			logging.info('serviceCtrl control = {}'.format('SERVICE_CONTROL_SESSIONCHANGE'))
		elif(control == win32service.SERVICE_CONTROL_PRESHUTDOWN):
			logging.info('serviceCtrl control = {}'.format('SERVICE_CONTROL_PRESHUTDOWN'))
		elif(control == win32service.SERVICE_CONTROL_CONTINUE):
			logging.info('serviceCtrl control = {}'.format('SERVICE_CONTROL_CONTINUE'))
		elif(control == win32service.SERVICE_CONTROL_POWEREVENT):
			logging.info('serviceCtrl control = {}'.format('SERVICE_CONTROL_POWEREVENT'))
		
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

	def startCheckingForUser(self, userName):
		self.userList.append(userName)
	
	def stopCheckingForUser(self, userName):
		self.userList.remove(userName)
	

	def SvcStop(self):
		self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
		win32event.SetEvent(self.stop_event)
		logging.info('Stopping service ...')
		self.stop_requested = True

	def SvcDoRun(self):
		servicemanager.LogMsg(
			servicemanager.EVENTLOG_INFORMATION_TYPE,
			servicemanager.PYS_SERVICE_STARTED,
			(self._svc_name_,'')
		)
		self.main()
		self.ReportServiceStatus(win32service.SERVICE_STOPPED)

	# All extra events are sent via SvcOtherEx (SvcOther remains as a
	# function taking only the first args for backwards compat)	
	def SvcOtherEx(self, control, event_type, data):
		# This is only showing a few of the extra events - see the MSDN
		# docs for "HandlerEx callback" for more info.
		try:
			if control == win32service.SERVICE_CONTROL_SESSIONCHANGE:
				sess_id = data[0]
				if event_type == 5: # logon
					msg = "Logon event: type=%s, sessionid=%s\n" % (event_type, sess_id)
					user_token = win32ts.WTSQueryUserToken(int(sess_id))
				elif event_type == 6: # logoff
					msg = "Logoff event: type=%s, sessionid=%s\n" % (event_type, sess_id)
				else:
					msg = "Other session event: type=%s, sessionid=%s\n" % (event_type, sess_id)
				try:
					for key, val in self.GetUserInfo(sess_id).items():
						msg += '%s : %s\n'%(key, val)
				except Exception as e:
					msg += '%s'%e
				logging.info(msg)
		except Exception as err:
			logging.info(err)
			
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
		logging.info(' ** Hello PyWin32 World ** ')
		# Simulate a main loop
		for i in range(0,50):
			if self.stop_requested:
				logging.info('A stop signal was received: Breaking main loop ...')
				break
			time.sleep(5)
			logging.info("Hello at %s" % time.ctime())
		logging.info('service finished.')
		return

if __name__ == '__main__':
	try :
		win32serviceutil.HandleCommandLine(HelloWorldSvc)
	except Exception as err:
		print("error: {}".format(err))