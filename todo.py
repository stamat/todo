#!/usr/bin/env python

import sys, os, re, datetime, time
import csv

args = sys.argv
args.pop(0)
args = ' '.join(args)

fieldnames = ['task', 'created', 'important', 'due', 'time_spent', 'tasklist', 'tags' ]
filename = 'todo.csv'
tmp_filename = 'tmp_todo.csv'
filename_completed = 'todo_completed.csv'
tmp_filename_completed = 'tmp_todo_completed.csv'

pat_cmds = re.compile(r"(\-\-?[a-zA-Z0-9\-]+\s?[^\-]*)")
pat_sepcmd = re.compile(r"(\-\-?)([a-zA-Z0-9\-]+)\s?([^\-]*)")
m = pat_cmds.findall(args)

def delete(num):
    num = int(num)
    csv_in = open(filename)
    csv_out =  open(tmp_filename, 'w')
    reader = csv.DictReader(csv_in)
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


def list(args=None):
    csv_in = open('todo.csv')
    reader = csv.DictReader(csv_in)
    count = 1
    for row in reader:
        print str(count) + ') ' +row['task']
        count += 1
    csv_in.close

def complete(arg):
    pass

def track(): #task time tracking
    pass

def add_time(): #add hours to hours spent
    pass

def due(): #set due of the task, keywords like today, tomorrow, day after tomorrow, next week, two days, two weeks, someday
    pass

def important(): #set the importance flag
    pass

def tasklist(): #asigns a task to a task list / project
    pass

def tags(): #asigns tags to he task, add tags to a task list, remove the tags, etc..
    pass

def new(args):
    if not os.path.exists(filename):
        csv_out =  open(filename, 'w')
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'task': args, 'created': time.time()})
        csv_out.close
    else:
        csv_in = open(filename)
        csv_out =  open(tmp_filename, 'w')
        reader = csv.DictReader(csv_in)
        writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
        writer.writeheader()
        for row in reader:
            writer.writerow(row)
        writer.writerow({'task': args, 'created': time.time()})
        csv_in.close
        csv_out.close
        os.rename(tmp_filename, filename)



fn = {
    'd': delete,
    'delete': delete,
    'c': complete,
    'complete': complete,
    'l': list,
    'list': list
}

def execute(command, args=None):
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
                    execute(cm, value)
            else:
                execute(command, value)
            
else:
    #add new todo
    if args.strip() == '':
       list()
    else:
        print args
        new(args)