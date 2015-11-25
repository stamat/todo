#!/usr/bin/env python

'''
    Simple CLI TODO program with time tracking
    by Stamat <stamatmail@gmail.com>
'''

import sys, os, re, time, string
from datetime import datetime, date, timedelta
import threading, atexit
import csv, ConfigParser


# TEXTTABLE 0.8.4 by Gerome Fournier https://github.com/foutaise/texttable/
##########################################################################
# imported like this to preserve TODO in one file and independent

try:
    if sys.version >= '2.3':
        import textwrap
    elif sys.version >= '2.2':
        from optparse import textwrap
    else:
        from optik import textwrap
except ImportError:
    sys.stderr.write("Can't import textwrap module!\n")
    raise

if sys.version >= '2.7':
    from functools import reduce

def len(iterable):
    """Redefining len here so it will be able to work with non-ASCII characters
    """
    if not isinstance(iterable, str):
        return iterable.__len__()
    
    try:
        if sys.version >= '3.0':
            return len(str)
        else:
            return len(unicode(iterable, 'utf'))
    except:
        return iterable.__len__()

class ArraySizeError(Exception):
    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg, '')

    def __str__(self):
        return self.msg

class Texttable:

    BORDER = 1
    HEADER = 1 << 1
    HLINES = 1 << 2
    VLINES = 1 << 3

    def __init__(self, max_width=80):
        if max_width <= 0:
            max_width = False
        self._max_width = max_width
        self._precision = 3

        self._deco = Texttable.VLINES | Texttable.HLINES | Texttable.BORDER | \
            Texttable.HEADER
        self.set_chars(['-', '|', '+', '='])
        self.reset()

    def reset(self):
        self._hline_string = None
        self._row_size = None
        self._header = []
        self._rows = []

    def set_chars(self, array):
        if len(array) != 4:
            raise ArraySizeError("array should contain 4 characters")
        array = [ x[:1] for x in [ str(s) for s in array ] ]
        (self._char_horiz, self._char_vert,
            self._char_corner, self._char_header) = array

    def set_deco(self, deco):
        self._deco = deco

    def set_cols_align(self, array):
        self._check_row_size(array)
        self._align = array

    def set_cols_valign(self, array):

        self._check_row_size(array)
        self._valign = array

    def set_cols_dtype(self, array):
        self._check_row_size(array)
        self._dtype = array

    def set_cols_width(self, array):
        self._check_row_size(array)
        try:
            array = list(map(int, array))
            if reduce(min, array) <= 0:
                raise ValueError
        except ValueError:
            sys.stderr.write("Wrong argument in column width specification\n")
            raise
        self._width = array

    def set_precision(self, width):
        if not type(width) is int or width < 0:
            raise ValueError('width must be an integer greater then 0')
        self._precision = width

    def header(self, array):
        self._check_row_size(array)
        self._header = list(map(str, array))

    def add_row(self, array):
        self._check_row_size(array)

        if not hasattr(self, "_dtype"):
            self._dtype = ["a"] * self._row_size
            
        cells = []
        for i, x in enumerate(array):
            cells.append(self._str(i, x))
        self._rows.append(cells)

    def add_rows(self, rows, header=True):
        if header:
            if hasattr(rows, '__iter__') and hasattr(rows, 'next'):
                self.header(rows.next())
            else:
                self.header(rows[0])
                rows = rows[1:]
        for row in rows:
            self.add_row(row)

    def draw(self):
        if not self._header and not self._rows:
            return
        self._compute_cols_width()
        self._check_align()
        out = ""
        if self._has_border():
            out += self._hline()
        if self._header:
            out += self._draw_line(self._header, isheader=True)
            if self._has_header():
                out += self._hline_header()
        length = 0
        for row in self._rows:
            length += 1
            out += self._draw_line(row)
            if self._has_hlines() and length < len(self._rows):
                out += self._hline()
        if self._has_border():
            out += self._hline()
        return out[:-1]

    def _str(self, i, x):
        try:
            f = float(x)
        except:
            return str(x)

        n = self._precision
        dtype = self._dtype[i]

        if dtype == 'i':
            return str(int(round(f)))
        elif dtype == 'f':
            return '%.*f' % (n, f)
        elif dtype == 'e':
            return '%.*e' % (n, f)
        elif dtype == 't':
            return str(x)
        else:
            if f - round(f) == 0:
                if abs(f) > 1e8:
                    return '%.*e' % (n, f)
                else:
                    return str(int(round(f)))
            else:
                if abs(f) > 1e8:
                    return '%.*e' % (n, f)
                else:
                    return '%.*f' % (n, f)

    def _check_row_size(self, array):
        if not self._row_size:
            self._row_size = len(array)
        elif self._row_size != len(array):
            raise ArraySizeError("array should contain %d elements" \
                % self._row_size)

    def _has_vlines(self):
        return self._deco & Texttable.VLINES > 0

    def _has_hlines(self):
        return self._deco & Texttable.HLINES > 0

    def _has_border(self):
        return self._deco & Texttable.BORDER > 0

    def _has_header(self):
        return self._deco & Texttable.HEADER > 0

    def _hline_header(self):
        return self._build_hline(True)

    def _hline(self):
        if not self._hline_string:
            self._hline_string = self._build_hline()
        return self._hline_string

    def _build_hline(self, is_header=False):
        horiz = self._char_horiz
        if (is_header):
            horiz = self._char_header
        # compute cell separator
        s = "%s%s%s" % (horiz, [horiz, self._char_corner][self._has_vlines()],
            horiz)
        # build the line
        l = s.join([horiz * n for n in self._width])
        # add border if needed
        if self._has_border():
            l = "%s%s%s%s%s\n" % (self._char_corner, horiz, l, horiz,
                self._char_corner)
        else:
            l += "\n"
        return l

    def _len_cell(self, cell):
        cell_lines = cell.split('\n')
        maxi = 0
        for line in cell_lines:
            length = 0
            parts = line.split('\t')
            for part, i in zip(parts, list(range(1, len(parts) + 1))):
                length = length + len(part)
                if i < len(parts):
                    length = (length//8 + 1) * 8
            maxi = max(maxi, length)
        return maxi

    def _compute_cols_width(self):
        if hasattr(self, "_width"):
            return
        maxi = []
        if self._header:
            maxi = [ self._len_cell(x) for x in self._header ]
        for row in self._rows:
            for cell,i in zip(row, list(range(len(row)))):
                try:
                    maxi[i] = max(maxi[i], self._len_cell(cell))
                except (TypeError, IndexError):
                    maxi.append(self._len_cell(cell))
        items = len(maxi)
        length = reduce(lambda x, y: x+y, maxi)
        if self._max_width and length + items * 3 + 1 > self._max_width:
            maxi = [(self._max_width - items * 3 -1) // items \
                    for n in range(items)]
        self._width = maxi

    def _check_align(self):
        if not hasattr(self, "_align"):
            self._align = ["l"] * self._row_size
        if not hasattr(self, "_valign"):
            self._valign = ["t"] * self._row_size

    def _draw_line(self, line, isheader=False):
        line = self._splitit(line, isheader)
        space = " "
        out = ""
        for i in range(len(line[0])):
            if self._has_border():
                out += "%s " % self._char_vert
            length = 0
            for cell, width, align in zip(line, self._width, self._align):
                length += 1
                cell_line = cell[i]
                fill = width - len(cell_line)
                if isheader:
                    align = "c"
                if align == "r":
                    out += "%s " % (fill * space + cell_line)
                elif align == "c":
                    out += "%s " % (int(fill/2) * space + cell_line \
                            + int(fill/2 + fill%2) * space)
                else:
                    out += "%s " % (cell_line + fill * space)
                if length < len(line):
                    out += "%s " % [space, self._char_vert][self._has_vlines()]
            out += "%s\n" % ['', self._char_vert][self._has_border()]
        return out

    def _splitit(self, line, isheader):
        line_wrapped = []
        for cell, width in zip(line, self._width):
            array = []
            for c in cell.split('\n'):
                try:
                    if sys.version >= '3.0':
                        c = str(c)
                    else:
                        c = unicode(c, 'utf')
                except UnicodeDecodeError as strerror:
                    sys.stderr.write("UnicodeDecodeError exception for string '%s': %s\n" % (c, strerror))
                    if sys.version >= '3.0':
                        c = str(c, 'utf', 'replace')
                    else:
                        c = unicode(c, 'utf', 'replace')
                array.extend(textwrap.wrap(c, width))
            line_wrapped.append(array)
        max_cell_lines = reduce(max, list(map(len, line_wrapped)))
        for cell, valign in zip(line_wrapped, self._valign):
            if isheader:
                valign = "t"
            if valign == "m":
                missing = max_cell_lines - len(cell)
                cell[:0] = [""] * int(missing / 2)
                cell.extend([""] * int(missing / 2 + missing % 2))
            elif valign == "b":
                cell[:0] = [""] * (max_cell_lines - len(cell))
            else:
                cell.extend([""] * (max_cell_lines - len(cell)))
        return line_wrapped





#TODO
#############################################################################################

args = sys.argv
args.pop(0)
args = ' '.join(args)

version = '1.0.1'

#TODO: Display function displays a header with data: important count, unimportant count, due soon count, due later count
#TODO: display tasks by important, by due soon, by important-duesoon, by important-due later, by nonimportant...
#TODO: add UID for tasks for server synchronisation, should be creation timestamp in combination with autoincrement ID, to prevent multidevice sync confusion
#synchronisation should happen by last modified has priority
#completed tasks has a special additional file for synchronisation newly finished tasks after last synchronisation, server appends to completed.csv on serverside. THINK ABOUT THIS, IT WILL BE A HUGE FILE.
#TODO: time spent statistics in a file. THINK ABOUT THIS
#TODO: shorten timestamps to seconds only to save the storage space, except creation timestamp. WARCH THE TIMEZONES! REDUCE ALL TIMES TO GMT +0 to avoid server confusion
#TODO: droplets gui for this TODO

fieldnames = ['task', 'created', 'important', 'due', 'time_spent', 'tasklist', 'tags', 'last_modified']
filename = 'todo.csv'
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

        Hello, {name}!

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
    
filename = os.path.join(conf.get('general', 'dir'), filename)
tmp_filename = os.path.join(conf.get('general', 'dir'), tmp_filename)
filename_completed = os.path.join(conf.get('general', 'dir'), filename_completed)
tmp_filename_completed = os.path.join(conf.get('general', 'dir'), tmp_filename_completed)


# updated print, used when outputing spent time on a task
def _uprint(new):
    CURSOR_UP_ONE = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print(CURSOR_UP_ONE + ERASE_LINE + str(new))


# gets the current task number, if the value past is string "last" then it is the length of the CSV rows
def _parsenum(num, mod=None):
    num = num.split(',')
    for i in range(0, len(num)):
        if num[i] == 'last':
            num[i] = len(reader)
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
            reader[num[i]]['last_modified'] = time.time()
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

#savetime if tracking a task time and you exit a terminal
def _savetime():
    global _TIME
    if _TIME is not 0:
        _TIME = time.time() - _TIME
        _set(num, 'time_spent', _TIME)
        
atexit.register(_savetime)

def _deltatime(string):
    time = timedelta(0, float(string))
    return re.sub(r"\.[0-9]+", '', str(time))

# display all tags and number of tasks, number of important tasks, number of due soon tasks
def display_tags(args=None):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    res = {}
    for row in reader:
        tags = _csvlist(row['tags'])
        if tags:
            for t in tags:
                if t in res:
                    r = res[t]
                    r['count'] += 1
                    if int(row['important']):
                        r['important'] += 1
                    if int(row['due']):
                        r['due'] += 1
                    if row['time_spent'] and row['time_spent'] != '':
                        r['time'] += float(row['time_spent'])
                else:
                    res[t] = {
                        'count': 1,
                        'important':  1 if int(row['important']) else 0,
                        'due': 1 if int(row['due']) else 0,
                        'time': float(row['time_spent'])
                    }
            
    table = Texttable()
    table.header(['task list', 'tasks', 'important', 'due soon', 'time'])
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

    
# display all tasklists and number of tasks, number of important tasks, number of due soon tasks
def display_tasklists(args=None):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    res = {}
    for row in reader:
        if row['tasklist'] in res:
            r = res[row['tasklist']]
            r['count'] += 1
            if int(row['important']):
                r['important'] += 1
            if int(row['due']):
                r['due'] += 1
            if row['time_spent'] and row['time_spent'] != '':
                r['time'] += float(row['time_spent'])
        else:
            res[row['tasklist']] = {
                'count': 1,
                'important':  1 if int(row['important']) else 0,
                'due': 1 if int(row['due']) else 0,
                'time': float(row['time_spent'])
            }
    
    table = Texttable()
    table.header(['task list', 'tasks', 'important', 'due soon', 'time'])
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

def _print(num, row, details=False):
    if not details:
        print str(num) + '  ' +row['task']
    else:
        tags = _csvlist(row['tags'])
        if tags: 
            tags = ', '.join(tags)
        else:
            tags = ''
        time = _deltatime(row['time_spent'])
        details.add_row([num, row['task'], 'o' if int(row['important']) else '', 'o' if int(row['due']) else '', row['tasklist'], tags, time]);
        #print str(num) + '  ' +row['task'] + '\t\t@'+row['tasklist']+tags

# display all tasks in a tasklist
def display_tasklist(tasklist, reader, details=False):
    count = 1
    
    for row in reader:
        if tasklist == row['tasklist']:
            _print(count, row, details)
        count += 1


# display all tasks in a tasklist
def display_tag(tag, reader, details=False):
    count = 1
    
    for row in reader:
        tags = _csvlist(row['tags'])
        if tags:
            for t in tags:
                if tag == t:
                    _print(count, row, details)
        count += 1
        

def display(args=None, details=False):
    csv_in = open(filename)
    reader = csv.DictReader(csv_in)
    
    if details:
        details = Texttable()
        details.header(['id', 'task', '!', '*', 'task list', 'tags', 'time'])
        
        #TODO  = important | due soon
    if args:
        args = args.strip()
        tl = pat_tl.search(args)
        if tl:
            display_tasklist(tl.group(1), reader, details)
            
        tg = pat_tg.search(args)
        if tg:
            display_tag(tg.group(1), reader, details)
    else:
        print
        count = 1
        for row in reader:
            _print(count, row, details)
            count += 1
        print
        
    if details:
        details.set_cols_width([3, 30, 1, 1, 10, 8, 8])
        details.set_deco(details.HEADER | details.VLINES)
        details.set_chars([' ',' ',' ','-'])
        s = details.draw()
        print
        print s
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
    global _TIME
    _TIME = _get(num, 'time_spent')
    if _TIME is '':
        _TIME = time.time()
    else:
        _TIME = time.time()-float(_TIME)
        
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
        _set(num, 'time_spent', _TIME)
        _TIME = 0

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
        print 'Error: tasklist option requires 2 parameters, first the task id/ids, second tasklist name'
        return
    if len(pts) > 1:
        pts[1] = re.sub(r"@",'',pts[1])
    else:
        pts.insert(1, '')
        
    num = _parsenum(pts[0])
    _set(num, 'tasklist', pts[1], False)


#assigns tags to the task, add tags to a task list, remove the tags, etc..
def tag(args):
    pts = args.split(' ', 1)
    
    if len(pts) < 2:
        print 'Error: tag option requires 2 parameters, first the task id, second tag names separated by space'
        return
    
    pts[1] = re.sub(r"\+",'',pts[1])
    ntags = pts[1].split(' ')
    
    num = _parsenum(pts[0], -1)
    
    tags = _get(num, 'tags')
    
    result = []
    
    nntags = set(ntags)
    for i in range(0, len(num)):
        if not tags[i] == '':
            tg = _csvlist(tags[i])
            otags = set(tg)  
            result.append(tg + list(nntags-otags))
        else:
            result.append(ntags)
    
    _set(num, 'tags', result)
 
# removes given tags separated by space beginning with +   
def rmtag(args):
    pts = args.split(' ', 1)
    
    if len(pts) < 2:
        print 'Error: rmtag option requires 2 parameters, first the task id, second tag names separated by space'
        return
    
    pts[1] = re.sub(r"\+",'',pts[1])
    ntags = pts[1].split(' ')
    
    num = _parsenum(pts[0], -1)
    
    tags = _get(num, 'tags')
    
    result = []
    
    nntags = set(ntags)
    for i in range(0, len(num)):
        if not tags[i] == '':
            tg = _csvlist(tags[i])
            otags = set(tg)  
            result.append(list(otags-nntags))
        else:
            result.append('')
    
    _set(num, 'tags', result)
    

# imports a CSV
def imprt(): 
    #maybe parses your code for TODO: comments displays line number in task text
    pass

# edits task by a given id, asks user to dubmit the new title
def edit():
    pass

# adds a new task
def new(args):
    new_task = {'created': time.time(),
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


# prints a help text
def help(args=None):
    print '''
TODO v{ver} - CLI task manager with time tracking
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
    -i, --important ID[,ID]             toggles the important state
    -d, --due       ID[,ID]             toggles the due state (soon / later)
    -T, --tasklist  ID[,ID] [TASKLIST]  adds tasks to a tasklist
    --tag           ID[,ID] TAG[ TAG]   adds tags to tasks
    --rmtag         ID[,ID] TAG[ TAG]   removes existing tags from tasks
    --tasklists                         lists all tasklists
    --tags                              lists all tags
    -h, --help                          displays this help
'''.format(ver=version)

#TODO: Verson -v
#TODO: uninstall
#TODO: update
# Connects commands with real functions
fn = {
    'r': delete,
    'remove': delete,
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