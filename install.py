#!/usr/bin/env python

import sys, os, shutil, stat
import pwd
import errno

print '''
TODO - CLI task manager with time tracking
<http://todotron.com>

** INSTALLATION **

Hey, you there, yes you!
Welcome to the installation of the simple command line tool for task management and time tracking!

Thanks for your interest!
'''

user_path = os.path.expanduser('~')
user_uid = os.getuid()
user_gid = os.getgid()

sudo_uid = os.getenv('SUDO_UID')
if sudo_uid:
   user = pwd.getpwuid(int(sudo_uid))
   user_path = user.pw_dir
   user_uid = user.pw_uid
   user_gid = user.pw_gid
   
def rchmod(path, mod, uid=None, gid=None):
   for root, dirs, files in os.walk(path):
      def setPriv(root, f):
         path = os.path.join(root, f)
         if uid is not None and gid is not None:
            os.chown(path, uid, gid)
         os.chmod(path, mod)
      
      for f in dirs:  
         setPriv(root, f)
      for f in files:
         setPriv(root, f)

if os.name == 'nt':
    print 'Sorry, installation is currently not supported on Windows :\'('
    sys.exit(1)


config_path = os.path.join(user_path, '.todo')
new_exec_path = os.path.join(config_path, 'todo.py')
lib_path = os.path.join(config_path, 'lib')
symln_path = '/usr/local/bin/todo'

if not os.path.exists(config_path):
   os.mkdir(config_path, 0777)
   os.chown(config_path, user_uid, user_gid)

#get the version from file todo.py
#check for version
if os.path.exists(new_exec_path):
   os.remove(new_exec_path)
shutil.copy('todo.py', config_path)

if os.path.exists(lib_path):
   shutil.rmtree(lib_path)
shutil.copytree('lib', lib_path)
rchmod(config_path, 0777, user_uid, user_gid)

try:
   os.symlink(new_exec_path, symln_path)
   st = os.stat(symln_path)
   os.chmod(symln_path, st.st_mode | stat.S_IEXEC)
   
except OSError as e:
   if e[0] == errno.EACCES or e[0] == errno.EPERM:
      print '''** OOPS, NO SUDO PRIVILEGES! **
      
You'll either need to run this install with sudo or the following command manually:

      sudo ln -s {0} {1}
      
This command creates the symlink so you can call this program in your terminal by typing "todo"
'''.format(new_exec_path, symln_path)
      sys.exit(1)
      
print '''** INSTALLATION PERFORMED SUCCESSFULLY! **

This application is now installed in "{0}", with symlink "{1}"
You can now discard the installation files and use this program by typing "todo" in your terminal. Try:

      todo -h

Cheers! ;)'''.format(new_exec_path, symln_path)