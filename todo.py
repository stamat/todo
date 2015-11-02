#!/usr/bin/env python

'''
    Simple CLI TODO program with time tracking
    by Stamat <stamatmail@gmail.com>
'''

import sys, os, re, time
from datetime import datetime, date, timedelta
import threading
import csv

args = sys.argv
args.pop(0)
args = ' '.join(args)

fieldnames = ['task', 'created', 'important', 'due', 'time_spent', 'tasklist', 'tags', 'last_modified' ]
filename = 'todo.csv'
tmp_filename = 'tmp_todo.csv'
filename_completed = 'todo_completed.csv'
tmp_filename_completed = 'tmp_todo_completed.csv'

pat_cmds = re.compile(r"(\-\-?[a-zA-Z0-9\-]+\s?[^\-]*)")
pat_sepcmd = re.compile(r"(\-\-?)([a-zA-Z0-9\-]+)\s?([^\-]*)")
pat_tl = re.compile(r"^@([^@\s\-]+)")
pat_tg = re.compile(r"^\+([^\+\s\-]+)")
m = pat_cmds.findall(args)

#updated print
def _uprint(new):
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print(CURSOR_UP_ONE + ERASE_LINE + str(new))

def delete(num):
    csv_in = open(filename)
    csv_out =  open(tmp_filename, 'w')
    reader = csv.DictReader(csv_in)
    reader = list(reader)
    
    if num == 'last':
        num = len(reader)
    num = int(num)
    
    writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()
    
    count = 1
    for row in reader:
        if count is not num:
            writer.writerow(row)
        count += 1
        
    csv_in.close
    csv_out.close
    os.rename(tmp_filename, filename)

def _set(num, field, value):
    csv_in = open(filename)
    csv_out =  open(tmp_filename, 'w')
    reader = csv.DictReader(csv_in)
    reader = list(reader)
    
    if num == 'last':
        num = len(reader)
    else: 
        num = int(num)
    num -= 1
    
    writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
    writer.writeheader()
    
    try:
        if field:
            reader[num][field] = value
        else:
            reader[num] = value
        reader[num]['last_modified'] = time.time()
    except IndexError:
        print 'Error: Nonexistent entry ' + str(num+1)
    
    for row in reader:
        writer.writerow(row)
        
    csv_in.close
    csv_out.close
    os.rename(tmp_filename, filename)

def display_tasklist(tasklist):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    count = 1
    for row in reader:
        if tasklist == row['tasklist']:
            print str(count) + '  ' +row['task']
        count += 1
    csv_in.close


def display(args=None):
    if args:
        args = args.strip()
        tl = pat_tl.search(args)
        if tl:
            display_tasklist(tl.group(1))
    
    else:
        csv_in = open(filename)
        reader = csv.DictReader(csv_in)
        count = 1
        for row in reader:
            print str(count) + '  ' +row['task']
            count += 1
        csv_in.close

def _get(num, field='asd'):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    reader = list(reader)
    
    if num == 'last':
        num = len(reader)
    else: 
        num = int(num)
    num -= 1
    
    try:
        if field:
            return reader[num][field]
        else:
            return reader[num]
    except IndexError:
        print 'Error: Nonexistent entry ' + str(num+1)
        
    csv_in.close

def complete(arg): #on completion a task is moved to the other file todo_complete.csv where it's stored for later mining
    pass

def track(num): #task time tracking
    #get the previous value, if empty start tiem is time now
    st = _get(num, 'time_spent')
    if st is '':
        st = time.time()
    else:
        st = time.time()-float(st)
        
    def timed_output(st, delay):
        while True:
            d = timedelta(seconds=time.time() - st)
            _uprint(d)
            time.sleep(delay)
            
    delay = 1
    t = threading.Thread(target = timed_output, args = (st,delay))
    
    print
    t.daemon = True
    t.start()
    
    try:
        while True:
            time.sleep(delay)
    except KeyboardInterrupt:
        st = time.time() - st
        _set(num, 'time_spent', st)

def addtime(): #add hours to hours spent
    pass

def removetime(): #remove hours to hours spent
    pass

def due(): #set due of the task, keywords like today, tomorrow, day after tomorrow, next week, two days, two weeks, someday
    pass

def important(num): #set the importance flag
    #TODO multiple task asigns
    i = _get(num, 'important')
    if i is '':
        i = 0
    else:
        i = int(i)
    if i is 0:
        i +=1
        print 'Task "'+num+'" set to important' 
    else:
        i -=1
        print 'Task "'+num+'" set to unimportant' 
    _set(num, 'important', i)
    pass

def tasklist(args): #asigns a task to a task list / project
    #TODO multiple task asigns
    pts = args.split(' ', 2)
    if len(pts) < 2:
        print 'Error: tasklist option requires 2 parameters, first the task id, second tagnames separated by space'
        return
    pts[1] = re.sub(r"@",'',pts[1])
    _set(pts[0], 'tasklist', pts[1])

def _csvlist(string):
    pat_inside = re.compile(r"^\[\'(.*)\'\]$")
    r = pat_inside.search(string)
    if not r:
        return None
    return re.split(r"\',\s?\'", r.group(1))

def tag(args): #asigns tags to he task, add tags to a task list, remove the tags, etc..
    pts = args.split(' ', 1)
    
    if len(pts) < 2:
        print 'Error: tag option requires 2 parameters, first the task id, second tag names separated by space'
        return
    
    pts[1] = re.sub(r"\+",'',pts[1])
    ntags = pts[1].split(' ')
    
    tags = _get(pts[0], 'tags')
    
    if not tags == '':
        tags = _csvlist(tags)
        otags = set(tags)  
        ntags = set(ntags)
        ntags = tags + list(ntags-otags)
        
    _set(pts[0], 'tags', ntags)
    
def rmtag(args):
    pts = args.split(' ', 1)
    
    if len(pts) < 2:
        print 'Error: rmtag option requires 2 parameters, first the task id, second tag names separated by space'
        return
    
    pts[1] = re.sub(r"\+",'',pts[1])
    ntags = pts[1].split(' ')
    
    tags = _get(pts[0], 'tags')
    
    if not tags == '':
        tags = _csvlist(tags)
        otags = set(tags)  
        ntags = set(ntags)
        ntags = list(otags-ntags)
    _set(pts[0], 'tags', ntags)


def imprt(): #imports a CSV
    pass

def edit(): #edits task by a given id, asks user to dubmit the new title
    pass

def new(args):
    new_task = {'created': time.time(),
                'important': 0,
                'due': 'someday'}
    
    #TODO: check task for @tasklist #tag #tag
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
    print tg
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
        #print added task with the id 1
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
        #print added task with the id
        writer.writerow(new_task)
        csv_in.close
        csv_out.close
        os.rename(tmp_filename, filename)



fn = {
    'd': delete,
    'delete': delete,
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
    'rmtag': rmtag
}

def _execute(command, args=None):
    if command in fn:
        fn[command](value)
    else:
        print 'Error: Unknown command '+command


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