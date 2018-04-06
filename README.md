# win-user-access

this is simple i use application to restrict access time users according rules


## Dependecies:
    - python 3.6 - [python.org downloads](https://www.python.org/downloads/)
    - pywin32 - [Github repo](https://github.com/mhammond/pywin32) (here some dowloadeble installers [Releases](https://github.com/mhammond/pywin32/releases) )

## Installation:

    - install dependencies
    - create directory for access control files. Better if this dir will be in the root of system disk. 
    For example: 
    ```
    C:/AccessControl
    ```
    - copy user-acces.py and rules.json.example in this directory
    - install service with command
    ```
    python <path-to_user-acces.py> install
    ```
    For Example:
    ```
    python C:/AccessControl/user-access.py install
    ```
    - rename rules.json.example in rules.json
    - configure rules in rules.json file with some text editor
    - create task in TaskScheduler
      - create subdirectory in 'Task Scheduler Library'
      
      ![TaskScheduler-tree](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-tree.PNG)
      
      
      - select created directory and create task in there
      
      ![TaskScheduler-actions](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-actions.PNG)
      
      
      - task user 'SYSTEM'
      
      ![TaskScheduler-task-general](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-general.PNG)
      
      
      - trigger 'At log on' user to control access
      
      ![TaskScheduler-task-triggers](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-triggers.PNG)
      ![TaskScheduler-task-trigger-edit](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-trigger-edit.PNG)
      
      
      - action 'Start a program'
          
          ![TaskScheduler-task-actions](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-actions.PNG)
          ![TaskScheduler-task-action-edit](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-action-edit.PNG)
          
          - Program/script 'python'
          - Add arguments '<path-to_user-acces.py> start --user <user-name-of-user-to-control> --registerUser <user-name-of-user-to-control>'
          For example:
          ```
          C:/AccessControl/user-access.py start --user test --registerUser test
          ```
      - ![TaskScheduler-task-conditions](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-conditions.PNG)
      - ![TaskScheduler-task-settings](https://github.com/lexatnet/win-user-access/blob/master/images/TaskScheduler-task-settings.PNG)

## Architecture:
#TODO

## Contents:
README.md - program description
user-acces.py - main file of program
rules.json.example - example of rules configuration
/imades - directory contained images for README.md

## Details:
### user-access.py start service command line arguments:
--user, -u, user to analyze access
--registerUser, -ru, user to init registeredUsers
--database, -db, database file name
--rules, -r, file name with rules
--shutdownDelay, -sd shutdown delay in seconds
--sleep, -s sleep seconds between access checks
--debug, -d, run in debug mode

