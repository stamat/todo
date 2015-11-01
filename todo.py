#!/usr/bin/env python

import sys, os, re, datetime, time
import csv

args = sys.argv
args.pop(0)
args = ' '.join(args)

fieldnames = ['task', 'created', 'important', 'due', 'time_spent', 'tasklist', 'tags' ]
filename = 'todo.csv'
tmp_filename = 'tmp_todo.csv'

pat_cmds = re.compile(r"\-\-?([a-z0-9\-]+\s?[^\s\-]*)", re.IGNORECASE)
pat_sepcmd = re.compile(r"([a-z\-]+)\s?([^\s\s]*)", re.IGNORECASE)
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


def list(arg):
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

def get(): #method of getting all kinds of tasks
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
        os.rename('tmp_todo.csv', 'todo.csv')



fn = {
    'd': delete,
    'delete': delete,
    'c': complete,
    'complete': complete,
    'l': list,
    'list': list
}

if m:
    #execute commands
    for cmd in m:
        c = pat_sepcmd.search(cmd)
        #TODO: if it has one dash and multiple letters break the letters as commands and pass them the same value
        if c:
            command = c.group(1)
            value = c.group(2)
            if command in fn:
                fn[command](value)
            else:
                print 'Error: Unknown command '+command
            
else:
    #add new todo
    if args.strip() == '':
       list()
    else:
        print args
        new(args)
            # with open('todo.csv') as csvfile:
            #     reader = csv.DictReader(csvfile)
        