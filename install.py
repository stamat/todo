#!/usr/bin/env python

import sys, os, shutil
import pwd
import errno

is_windows = False

sudo_uid = os.getenv('SUDO_UID')
if sudo_uid:
   print pwd.getpwuid(int(sudo_uid))
print pwd.getpwuid(os.geteuid())
sys.exit()

#get the version from file todo.py
if os.name == 'nt':
    print 'Sorry, installation is currently not supported on Windows'
    sys.exit(1)

user_path = os.path.expanduser('~')
config_path = os.path.join(user_path, '.todo')
new_exec_path = os.path.join(config_path, 'todo.py')

if not os.path.exists(config_path):
    os.mkdir(config_path)

#check for version
shutil.copy('todo.py', config_path)

try:
    os.remove('/usr/local/bin/todo')
    #os.symlink(os.path.join(config_path, 'todo.py'), '/usr/local/bin/todo')
except OSError as e:
    if e[0] == errno.EACCES or e[0] == errno.EPERM:
       print "You need root permissions to do this, laterz!"
       #sys.exit(1)