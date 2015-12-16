#!/usr/bin/env python

'''
    Simple CLI TODO program with time tracking
    by Stamat <stamatmail@gmail.com>
'''

import sys, os, re, time, string
from datetime import datetime, date, timedelta
import threading, atexit
import csv, ConfigParser

texttable_available = True
try:
    import texttable
except ImportError:
    try:
        import lib.texttable as texttable
    except ImportError:
        texttable_available = False

args = sys.argv
args.pop(0)
args = ' '.join(args)

version = '1.0.5'

#TODO: Preferences for argumentless display of tasks, default query
#TODO: add UID for tasks for server synchronisation, should be creation timestamp in combination with autoincrement ID, to prevent multidevice sync confusion
#synchronisation should happen by last modified has priority
#completed tasks has a special additional file for synchronisation newly finished tasks after last synchronisation, server appends to completed.csv on serverside. THINK ABOUT THIS, IT WILL BE A HUGE FILE.
#TODO: droplets gui for this TODO

fieldnames = ['task', 'created', 'important', 'due', 'time_spent', 'tasklist', 'tags', 'last_modified']
filename = 'todo.csv'
timefile = 'time.csv'
tmp_filename = 'tmp_todo.csv'
filename_completed = 'todo_completed.csv'
tmp_filename_completed = 'tmp_todo_completed.csv'

pat_cmds = re.compile(r"(\-\-?[a-zA-Z0-9\-]+\s?[^\-]*)")
pat_sepcmd = re.compile(r"(\-\-?)([a-zA-Z0-9\-]+)\s?([^\-]*)")
pat_tl = re.compile(r"^@([^@\s\-]+)")
pat_tg = re.compile(r"^\+([^\+\s\-]+)")

_TIME = 0 #global time var for storing time tracking delta

user_path = os.path.expanduser('~')
config_path = os.path.join(user_path, '.todo')
config_cfg = os.path.join(config_path, 'config.cfg')

# Recursive ask to set the directory untill the the pathe xists
def _bother(default):
    npath = raw_input('Enter directory to store data files (default='+default+'):').strip()
    if npath == "":
        print 'As you command sir, we\'ll be using the default path'
        return default

    try:
        assert os.path.exists(npath) and os.path.isdir(npath)
    except AssertionError:
        print 'Error: Sorry, the directory "'+npath+'" doesn\'t exits! Please try again.'
        return _bother(default)

    return npath

# Reads an INI file and returns a ConfigParser object that can be iterated
def _readconf(file_path):
    conf = ConfigParser.RawConfigParser()

    if not os.path.exists(file_path) and not os.path.isfile(file_path):
        return conf

    try:
        f = open(file_path)
        conf.readfp(f)
        f.close
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        raise

    return conf

# Sets a value of a INI ConfigParser object by a given section and key
def _setconf(conf, section, key, value):
    if not conf.has_section(section):
        conf.add_section(section)
    conf.set(section, key, value)

    return conf

# Writes INI ConfigParser object to a file
def _writeconf(file_path, conf):
    try:
        f = open(file_path, 'wb')
        conf.write(f)
        f.close
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)
        raise

    return True

def _UTCTimestamp():
    return int( time.mktime(time.gmtime()) )

def _UTC2LocalTimestamp(utc_timestamp):
    return utc_timestamp + (int(time.time()) - _UTCTimestamp())


conf = _readconf(config_cfg)


# FIRST INIT
if not os.path.exists(config_path):
    os.mkdir(config_path)

if not os.path.exists(config_cfg):
    uname = os.path.split(user_path) #XXX: Will this always work?
    uname = uname[-1]
    print '''
TODO v{ver}
the simple CLI task manager with time tracking
----------------------------------------------

        Oh hai, {name}!

It looks like it\'s your first time using this application!?
If you wish you can enter a directory where you would like to save the CSV todo data files. Saving them to Dropbox folder can be a good idea to backup them and access them across the devices.
'''.format(ver=version, name=uname.capitalize())

    npath = _bother(config_path)

    _setconf(conf, 'general', 'dir', npath)
    _setconf(conf, 'general', 'name', uname.capitalize())
    _writeconf(config_cfg, conf)

    print '''
Thanks, you're a real pal!


        ,d88b.d88b,
        88888888888
        `Y8888888Y'
          `Y888Y'
            `Y'
'''

destination_dir = conf.get('general', 'dir')
filename = os.path.join(destination_dir, filename)
tmp_filename = os.path.join(destination_dir, tmp_filename)
filename_completed = os.path.join(destination_dir, filename_completed)
tmp_filename_completed = os.path.join(destination_dir, tmp_filename_completed)

# create the todo file if it doesn't exists
if not os.path.exists(filename):
    csv_out =  open(filename, 'w')
    writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()
    csv_out.close


# updated print, used when outputing spent time on a task
def _uprint(new):
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print(CURSOR_UP_ONE + ERASE_LINE + str(new))


# gets the current task number, if the value past is string "last" then it is the length of the CSV rows
def _parsenum(num, mod=None):
    num = num.split(',')
    last = 1

    try:
        reader
    except NameError:
        csv_in = open(filename)
        reader = csv.DictReader(csv_in)
        reader = list(reader)
        last = len(reader);
        csv_in.close

    for i in range(0, len(num)):
        if num[i] == 'last':
            num[i] = last
        num[i] = int(num[i])
        if mod:
            num[i] += mod

    return num


# Sets a value to a CSV file
def _set(num, field, value, value_array = True):
    csv_in = open(filename)
    csv_out =  open(tmp_filename, 'w')
    reader = csv.DictReader(csv_in)
    reader = list(reader)

    writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()

    if not isinstance(num, list):
        num = [int(num)-1]
        value = [value]

    for i in range(0, len(num)):
        try:
            if field:
                reader[num[i]][field] = value[i] if value_array else value
            else:
                reader[num[i]] = value[i] if value_array else value
            reader[num[i]]['last_modified'] = _UTCTimestamp()
        except IndexError:
            print 'Error: Nonexistent entry', str(num[i]+1)

    for row in reader:
        writer.writerow(row)

    csv_in.close
    csv_out.close
    os.rename(tmp_filename, filename)

# Gets a value from a csv file
def _get(num, field=None):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    reader = list(reader)

    one_result = False
    if not isinstance(num, list):
        num = [int(num)-1]
        one_result = True

    result = []

    for i in range(0, len(num)):
        try:
            if field:
                result.append(reader[num[i]][field])
            else:
                result.append(reader[num[i]])
        except IndexError:
            print 'Error: Nonexistent entry', str(num[i]+1)

    csv_in.close

    if one_result:
        return result[0]

    return result

# transforms CSV list value into a py list
def _csvlist(string):
    pat_inside = re.compile(r"^\[\'(.*)\'\]$")
    r = pat_inside.search(string)
    if not r:
        return None
    return re.split(r"\',\s?\'", r.group(1))

# executes a command from a dictionary of commands
def _execute(command, args=None):
    if command in fn:
        fn[command](value)
    else:
        print 'Error: Unknown command',command

#TODO savetime if tracking a task time and you exit a terminal
def _savetime():
    global _TIME
    if _TIME is not 0:
        _TIME = time.time() - _TIME
        _set(num, 'time_spent', _TIME)

#atexit.register(_savetime)


def _deltatime(string):
    if type(string) is str and string.strip() == '':
        return '0:00:00'
    time = timedelta(0, float(string))
    return re.sub(r"\.[0-9]+", '', str(time))


def _csvnum(val, fn):
    val = val.strip()
    if val and val != '':
        try:
            return fn(val)
        except Exception as ex:
            pass
    return 0

def _csvint(val, fn):
    return _csvnum(val, int)

def _csvint(val, fn):
    return _csvnum(val, float)

# display all tags and number of tasks, number of important tasks, number of due soon tasks
def display_tags(args=None):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    res = {}
    
    for row in reader:
        tags = _csvlist(row['tags'])
        time_spent = row['time_spent'];

        if tags:
            for t in tags:
                if t in res:
                    r = res[t]
                    r['count'] += 1
                    if _isImportant(row['important']):
                        r['important'] += 1
                    if _isDue(row['due']):
                        r['due'] += 1

                    r['time'] += _csvint(row['time_spent'])
                else:
                    due = 1 if _isDue(row['due']) else 0
                    important = 1 if _isImportant(row['important']) else 0
                    
                    res[t] = {
                        'count': 1,
                        'important': important,
                        'due':  due,
                        'time': _csvint(row['time_spent'])
                    }

    if texttable_available:
        table = texttable.Texttable()
        table.header(['tag', 'tasks', 'important', 'due soon', 'time'])
        table.set_chars([' ',' ',' ','-'])
        table.set_deco(table.HEADER | table.VLINES)

        for r in res:
            name = r;
            r = res[r];
            table.add_row([name, r['count'], r['important'], r['due'], _deltatime(r['time'])])

        print
        print table.draw()
        print

    else:
        print
        for r in res:
            name = r;
            r = res[r];
            print '+'+name+' \t\t[ count: '+str(r['count'])+', important: '+str(r['important'])+', due: '+str(r['due'])+' ]';
        print

# display all tasklists and number of tasks, number of important tasks, number of due soon tasks
def display_tasklists(args=None):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    res = {}
    for row in reader:
        if row['tasklist'] in res:
            r = res[row['tasklist']]
            r['count'] += 1
            if _isImportant(row['important']):
                r['important'] += 1
            if _isDue(row['due']):
                r['due'] += 1
            if row['time_spent'] and row['time_spent'] != '':
                r['time'] += _csvint(row['time_spent'])
        else:
            due = 1 if _isDue(row['due']) else 0
            important = 1 if _isImportant(row['important']) else 0
            
            res[row['tasklist']] = {
                'count': 1,
                'important': important,
                'due':  due,
                'time': _csvint(row['time_spent'])
            }

    if texttable_available:
        table = texttable.Texttable()
        table.header(['list', 'tasks', 'important', 'due soon', 'time'])
        table.set_chars([' ',' ',' ','-'])
        table.set_deco(table.HEADER | table.VLINES)

        for r in res:
            name = r;
            r = res[r];
            table.add_row([name, r['count'], r['important'], r['due'], _deltatime(r['time'])])
            #print '@'+name+' ('+str(r['count'])+')      important: '+str(r['important'])+', due: '+str(r['due']);

        print
        print table.draw()
        print

    else:
        print
        for r in res:
            name = r;
            r = res[r];
            print '@'+name+' \t\t[ count: '+str(r['count'])+', important: '+str(r['important'])+', due: '+str(r['due'])+' ]';
        print

def _isImportant(string):
    if not string or string == '0':
        return False
    return True

def _isDue(string):
    if not string or string == '0' or string == 'later':
        return False

    #if string or string == '1' or string == 'soon':
    return True
    #TODO: compare due time with current time and by configuration treshold decide if it is soon or later

def _print(num, row, details=False):
    if not details:
        tl = ' @'+row['tasklist'] if row['tasklist'] and row['tasklist'].strip() != '' else '';
        print str(num) + '  ' +row['task']+tl
    else:
        tags = _csvlist(row['tags'])
        if tags:
            tags = ', '.join(tags)
        else:
            tags = ''
        time = _deltatime(row['time_spent'])
        details.add_row([num, row['task'], 'o' if int(row['important']) else '', 'o' if int(row['due']) else '', row['tasklist'], tags, time]);


def parseQuery(s):
    pat_tl = re.compile(r"@([^@\s\-\+]+)\s?")
    pat_tg = re.compile(r"\+([^@\s\-\+]+)\s?")
    pat_i = re.compile(r"unimportant|important")
    pat_d = re.compile(r"later|soon")
    
    res = {}
    
    tasklists = pat_tl.findall(s)
    if tasklists:
        res['tasklists'] = tasklists
        s = re.sub(pat_tl, '', s)
        
    tags = pat_tg.findall(s)
    if tags:
        res['tags'] = tags
        s = re.sub(pat_tg, '', s)
    
    i = pat_i.findall(s)
    if i:
        if i[0] == 'important':
            res['important'] = True
        else:
            res['important'] = False
    
    d = pat_d.findall(s)
    if d:
        if d[0] == 'soon':
            res['due'] = True
        else:
            res['due'] = False
    
    return res

def query(q, reader):
    res = []
    
    count = 1
    
    for row in reader:
        tags = _csvlist(row['tags'])
        tasklist = row['tasklist']
        
        def check(arr1, arr2):
            if arr1 and arr2:
                for a1 in arr1:
                    for a2 in arr2:
                        if a1 == a2:
                            return True
            return False
        
        tags_flag = True
        if 'tags' in q:
            tags_flag = check(tags, q['tags'])
            
        tasklists_flag =  True
        if 'tasklists'  in q:
            tasklists_flag = check([tasklist], q['tasklists'])
        
        i_flag = True
        if 'important' in q:
            i_flag = _isImportant(row['important']) == q['important']
        
        d_flag = True
        if 'due' in q:
            d_flag = _isDue(row['due']) == q['due']
        
        row['count'] = count
        
        if tags_flag and tasklists_flag and i_flag and d_flag:
            res.append(row)
        
        count += 1
        
    return res

#TODO: Complex queries, query tag, important and/or due inside a tasklist or a tag
def display(args=None, details=False):
    
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)

    if not texttable_available:
        details = False

    if details:
        details = texttable.Texttable()
        details.header(['id', 'task', '*', '!', 'task list', 'tags', 'time'])
    
    regular = True
    if args:
        q = parseQuery(args)
        if q:
            regular = False
            rows = query(q, reader)
            
            if not details:
                print
            
            for row in rows:
                _print(row['count'], row, details)
                
            if not details:
                print
    
    if regular:
        count = 1
        if not details:
                print
                
        for row in reader:
            _print(count, row, details)
            count += 1

        if not details:
                print

    if details:
        details.set_cols_width([3, 30, 1, 1, 10, 8, 8])
        details.set_deco(details.HEADER | details.VLINES)
        details.set_chars([' ',' ',' ','-'])

        print
        print details.draw()
        print

    csv_in.close


def display_detailed(args=None):
    display(args, True);


# deletes a task
def delete(num):
    csv_in = open(filename)
    csv_out =  open(tmp_filename, 'w')
    reader = csv.DictReader(csv_in)
    reader = list(reader)

    num = _parsenum(num)

    writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()

    count = 1
    for row in reader:
        flag = True
        for i in range(0, len(num)):
            if count is num[i]:
                flag = False
                break

        if flag:
            writer.writerow(row)
        count += 1

    csv_in.close
    csv_out.close
    os.rename(tmp_filename, filename)


# on completion a task is moved to the other file todo_complete.csv where it's stored for later mining
def complete(arg):
    pass

#task time tracking
def track(num):
    #TODO: log of times per day / statistics
    global _TIME, _SPENT_TIME
    _TIME = _get(num, 'time_spent')
    cdif = time.time();
    
    if _TIME is '':
        _TIME = time.time()
    else:
        _TIME = time.time() - int(_TIME)

    def timed_output(st, delay):
        while True:
            _uprint(_deltatime(time.time() - st))
            time.sleep(delay)

    delay = 1
    t = threading.Thread(target = timed_output, args = (_TIME, delay))

    print
    t.daemon = True
    t.start()

    try:
        while True:
            time.sleep(delay)
    except KeyboardInterrupt:
        _TIME = time.time() - _TIME
        _set(num, 'time_spent', int(_TIME))
        logtime(timefile, int(time.time() - cdif), num)
        _TIME = 0

def _filepath(filename):
    return os.path.join(destination_dir, filename)

def _tmppath(filename):
    return os.path.join(destination_dir, 'tmp_'+filename)

def logtime(filename, sec, taskid):
    path = _filepath(filename)
    taskid = int(taskid)
    task = _get(taskid)
    fieldnames = ['time', 'start_timestamp', 'task', 'tasklist', 'day', 'month', 'year', 'end_timestamp', 'task_creation_timestamp', 'tags']
    ctime = _UTCTimestamp()
    
    log = {}
    log['time'] = sec
    log['end_timestamp'] = ctime
    log['start_timestamp'] = ctime - sec
    log['task'] = task['task']
    log['tasklist'] = task['tasklist']
    log['tags'] = task['tags']
    log['task_creation_timestamp'] = task['created']
    d = date.fromtimestamp(_UTC2LocalTimestamp(log['start_timestamp']))
    log['day'] = d.day
    log['month'] = d.month
    log['year'] = d.year
    
    if not os.path.exists(path):
        csv_out =  open(path, 'w')
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(log)
        csv_out.close
    else:
        tmp = _tmppath(filename)
        csv_in = open(path)
        csv_out =  open(tmp, 'w')
        reader = csv.DictReader(csv_in)
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        
        count = 1
        for row in reader:
            writer.writerow(row)
            count += 1

        writer.writerow(log)
        csv_in.close
        csv_out.close
        os.rename(tmp, path)

def addtime(): #add hours to hours spent
    pass

def settime(): #replaces time spent with user given value
    pass

#set due of the task, for now only true and false
def due(num):
    #TODO: today, tomorrow, two weeks, two days, someday
    num = _parsenum(num, -1)

    res = _get(num, 'due')

    for i in range(0, len(num)):
        if res[i] is '':
            res[i] = 0
        else:
            res[i] = int(res[i])
        if res[i] is 0:
            res[i] +=1
            print 'Task {0} set to due soon'.format(num[i]+1)
        else:
            res[i] -=1
            print 'Task {0} set to due later'.format(num[i]+1)

    _set(num, 'due', res)


#task importance toggle
def important(num):
    num = _parsenum(num, -1)

    res = _get(num, 'important')

    for i in range(0, len(num)):
        if res[i] is '':
            res[i] = 0
        else:
            res[i] = int(res[i])
        if res[i] is 0:
            res[i] +=1
            print 'Task {0} set to important'.format(num[i]+1)
        else:
            res[i] -=1
            print 'Task {0} set to unimportant'.format(num[i]+1)

    _set(num, 'important', res)


#asigns a task to a task list / project
def tasklist(args):
    pts = args.split(' ', 2)
    if len(pts) < 1:
        _err('tasklist option requires 2 parameters, first the task id/ids, second tasklist name', 'invalid argument')
        return
    if len(pts) > 1:
        pts[1] = re.sub(r"@",'',pts[1])
    else:
        pts.insert(1, '')

    num = _parsenum(pts[0], -1)
    _set(num, 'tasklist', pts[1], False)


#assigns tags to the task, add tags to a task list, remove the tags, etc..
def tag(args):
    pts = args.split(' ', 1)

    if len(pts) < 2:
        _err('tag option requires 2 parameters, first the task id, second tag names separated by space', 'invalid argument')
        return

    pts[1] = re.sub(r"\+",'',pts[1])
    ntags = pts[1].split(' ')

    num = _parsenum(pts[0], -1)

    tags = _get(num, 'tags')

    result = []

    nntags = set(ntags)
    for i in range(0, len(num)):
        if tags[i]:
            tg = _csvlist(tags[i])
            if tg:
                otags = set(tg)
                result.append(tg + list(nntags-otags))
            else:
                result.append(ntags)
        else:
            result.append(ntags)

    _set(num, 'tags', result)

# removes given tags separated by space beginning with +
def rmtag(args):
    pts = args.split(' ', 1)

    if len(pts) < 2:
        _err('rmtag option requires 2 parameters, first the task id, second tag names separated by space','invalid argument')
        return

    pts[1] = re.sub(r"\+",'',pts[1])
    ntags = pts[1].split(' ')

    num = _parsenum(pts[0], -1)

    tags = _get(num, 'tags')

    result = []

    nntags = set(ntags)
    for i in range(0, len(num)):
        if tags[i]:
            tg = _csvlist(tags[i])
            if tg:
                otags = set(tg)
                result.append(list(otags-nntags))
            else:
                result.append('')
        else:
            result.append('')

    _set(num, 'tags', result)


# imports a CSV
def imprt():
    #maybe parses your code for TODO: comments displays line number in task text
    pass

def _err(string, code=None):
    code = ' ['+code+']' if code else ''
    print 'Error{1}: {0}'.format(string, code)

# edits task by a given id, asks user to dubmit the new title
def edit(args):
    if not args:
        _err('You need to pass an ID of a task you would like to edit', 'invalid argument')
        pass
    pat_edit = re.compile(r"^([1-9]{1}[0-9]*|last)\s(.*)")
    mo = pat_edit.match(args)
    if mo:
        num = _parsenum(mo.group(1), -1)
        task = mo.group(2).strip()
        if task:
            _set(num, 'task', task, False)
        else:
            _err('Task text cannot be empty','invalid argument')
    else:
        _err('Pass an integer ID of the task you wish to edit and task text separated by space', 'invalid argument')

def show(args):
    #shows a single task with all the details
    pass

# adds a new task
def new(args):
    new_task = {'created': _UTCTimestamp(),
                'important': 0,
                'due': 0}

    #check task for @tasklist #tag #tag
    pat_all_tl = re.compile(r"^@[^@\s\-]+\s?|\s@[^@\s\-]+\s?")
    pat_all_tg = re.compile(r"\s?\+[^\+\s\-]+\s?")

    def tlrepl(mo):
       if mo.group(0).startswith(' ') and mo.group(0).endswith(' '): return ' '
       else: return ''

    tl = pat_all_tl.findall(args)
    if tl:
        args = re.sub(pat_all_tl, tlrepl, args)
        new_task['tasklist'] = re.sub(r"[\s@]", '', tl[0])

    tg = pat_all_tg.findall(args)

    if tg:
        args = re.sub(pat_all_tg, tlrepl, args)
        for i in range(0,len(tg)):
            tg[i] = re.sub(r"[\s\+]", '', tg[i])
        new_task['tags'] = tg

    new_task['task'] = args.strip()

    if not os.path.exists(filename):
        csv_out =  open(filename, 'w')
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(new_task)
        
        print 'Added task 1'
        csv_out.close
    else:
        csv_in = open(filename)
        csv_out =  open(tmp_filename, 'w')
        reader = csv.DictReader(csv_in)
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        
        count = 1
        for row in reader:
            writer.writerow(row)
            count += 1
        print 'Added task ' + str(count)

        writer.writerow(new_task)
        csv_in.close
        csv_out.close
        os.rename(tmp_filename, filename)


# prints a help text
def help(args=None):
    print '''
TODO - CLI task manager with time tracking
<http://todotron.com>

Usage:  todo ...TITLE...[@TASKLIST][+TAG]
        Add a new task, it can have one task list and multiple tags

        todo
        Lists all the tasks

        todo [OPTION] ...PARAMS...
        Performs an option


    -l, --list      [TASKLIST [TAG]]    lists all tasks, or all task within a list or with a tag
    -a, --details   [TASKLIST [TAG]]    lists all tasks with details
    -r, --remove    ID[,ID]             removes a task by a given task ID
    -c, --complete  ID[,ID]             completes a task by a given ID
    -t, --track     ID                  time track single task, exit keyboard interupt
    -e, --edit      ID                  edit the text of a single task
    -i, --important ID[,ID]             toggles the important state
    -d, --due       ID[,ID]             toggles the due state (soon / later)
    -T, --tasklist  ID[,ID] [TASKLIST]  adds tasks to a tasklist
    --tag           ID[,ID] TAG[ TAG]   adds tags to tasks
    --rmtag         ID[,ID] TAG[ TAG]   removes existing tags from tasks
    --tasklists                         lists all task lists
    --tags                              lists all tags
    -h, --help                          displays this help
    -v, --version                       displays version
'''

#TODO: uninstall
#TODO: update

def vers(args=None):
    print 'version: ' + version

# Connects commands with real functions
fn = {
    'r': delete,
    'remove': delete,
    's': show,
    'show': show,
    'v': vers,
    'version': vers,
    'e': edit,
    'edit': edit,
    'd': due,
    'due': due,
    'c': complete,
    'complete': complete,
    'l': display,
    'list': display,
    't': track,
    'track': track,
    'i': important,
    'important': important,
    'T': tasklist,
    'tasklist': tasklist,
    'tag': tag,
    'rmtag': rmtag,
    'h': help,
    'help': help,
    'tasklists': display_tasklists,
    'tags': display_tags,
    'a': display_detailed,
    'details': display_detailed
}

# parse commands passed as arguments
m = pat_cmds.findall(args)

if m:
    #execute commands
    for cmd in m:
        c = pat_sepcmd.search(cmd.strip())
        if c:
            dashes = c.group(1)
            command = c.group(2)
            value = c.group(3)

            if len(dashes) is 1:
                for cm in command:
                    _execute(cm, value)
            else:
                _execute(command, value)

else:
    #add new todo
    if args.strip() == '':
       display()
    else:
        new(args)
