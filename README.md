# win-user-access

this is simple i use application to restrict access time users according rules


## Dependecies:
- python 3.6 - https://www.python.org/downloads/
- pywin32 - https://github.com/mhammond/pywin32 (here some dowloadeble installers https://github.com/mhammond/pywin32/releases)

## Installation:

install dependencies


create directory for access control files. Better if this dir will be in the root of system disk.

For example:
```
C:/AccessControl
```

copy user-acces.py and rules.json.example in this directory

install service with command
```
python <path-to_user-acces.py> install
```
For Example:
```
python C:/AccessControl/user-access.py install
```

rename rules.json.example in rules.json

configure rules in rules.json file with some text editor

create task in TaskScheduler:

create subdirectory in 'Task Scheduler Library'

![TaskScheduler-tree](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-tree.PNG)

select created directory and create task in there

![TaskScheduler-actions](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-actions.PNG)

task user 'SYSTEM'

![TaskScheduler-task-general](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-general.PNG)

trigger 'At log on' user to control access

![TaskScheduler-task-triggers](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-triggers.PNG)

![TaskScheduler-task-trigger-edit](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-trigger-edit.PNG)

action 'Start a program'

![TaskScheduler-task-actions](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-actions.PNG)

![TaskScheduler-task-action-edit](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-action-edit.PNG)

Program/script 'python'

Add arguments '<path-to_user-acces.py> start --user <user-name-of-user-to-control> --registerUser <user-name-of-user-to-control>'

For example:
```
C:/AccessControl/user-access.py start --user test --registerUser test
```
![TaskScheduler-task-conditions](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-conditions.PNG)

![TaskScheduler-task-settings](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-settings.PNG)


## Contents:

- README.md - program description
- user-acces.py - main file of program
- rules.json.example - example of rules configuration
- /imades - directory contained images for README.md


## Details:

### user-access.py start service command line arguments:

- --user, -u, user to analyze access
- --registerUser, -ru, user to init registeredUsers
- --database, -db, database file name
- --rules, -r, file name with rules
- --shutdownDelay, -sd shutdown delay in seconds
- --sleep, -s sleep seconds between access checks
- --debug, -d, run in debug mode

### rules.json configuration time params


configuration this is array of rules: []
(if any of rules allow access for user then access for user is granted )
Example:
```
  [
    <rule>,
    ...
    <ruleN>
  ]
```

where each rule this is object: {}

with set optional descriptions
(if any aspect doesn't allow access then rule not grant access for user)
example:
```
 {
   <description>,
   ...
   <descriptionN>,
 }
```

each description this is consist form name of aspect and restrictions for aspect

aspects:

"users" - list allowed users. if user name in list then access is granted for user otherwise access denied
example:
```
"users": ["user1", "user2"]
```

"access-date" - list of allowed dates or dates intervals. if current date belong to dates interval described in restrictions or it one of specified dates then access is granted for user otherwise access denied
example:
```
"access-date":[
  {
    "start": "2018.02.18",
    "stop": "2018.03.29"
  },
  "2018.04.02"
]
```

"access-day" - list allowed days of week on intervals days of week
1 - Monday
...
7 - Sunday
if current day belong to one of day of week intervals or specified day then user access is granted otherwise access denied

example:
```
"access-day":[
  {
    "start": 1,
    "stop": 4
  },
  6
],
```

"session-duration" - allowed session duration in format: "XhrYmZs"
hr - hours
m - minutes
s - seconds
if current session duration less then specified time interval then access for user is granted otherwise access denied
example:
```
"session-duration": "1hr"
```

"pause-duration": minimal allowed time between sessions in format: "XhrYmZs"
hr - hours
m - minutes
s - seconds
if previous sesson ended more then specified time interval ago then user access is granted otherwise access denied
example:
```
"pause-duration": "15m"
```

"access-duration" - limit access time
hr - hours
m - minutes
s - seconds
example:
```
"access-duration": [
  {
    "limit": "1hr15m",
    "period": "24hr"
  }
]
```

"access-time" - list access time restrictions
example:
```
"access-time": [
  {
    "start": "18:00",
    "stop": "21:00"
  },
  {
    "start": "0:15",
    "stop": "4:00"
  }
]
```




## Architecture:

# TODO
* rewrite read/write db in thread
