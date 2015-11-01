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
m = pat_cmds.findall(args)

def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec) 
        func()  
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t

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

def display(args=None):
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

def add_time(): #add hours to hours spent
    pass

def due(): #set due of the task, keywords like today, tomorrow, day after tomorrow, next week, two days, two weeks, someday
    pass

def important(num): #set the importance flag
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
    
    pass

def tags(): #asigns tags to he task, add tags to a task list, remove the tags, etc..
    pass


def imprt(): #imports a CSV
    pass


def new(args):
    if not os.path.exists(filename):
        csv_out =  open(filename, 'w')
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'task': args,
                         'created': time.time(),
                         'important': 0,
                         'due': 'someday'})
        csv_out.close
    else:
        csv_in = open(filename)
        csv_out =  open(tmp_filename, 'w')
        reader = csv.DictReader(csv_in)
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            writer.writerow(row)
        writer.writerow({'task': args,
                         'created': time.time(),
                         'important': 0,
                         'due': 'someday'})
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
    'important': important
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
        print args
        new(args)