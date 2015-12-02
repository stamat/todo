![alt text](https://dl.dropboxusercontent.com/u/2808807/img/todo-cover.png "todo")
## Simple command line task manager with time tracking

* **Covey's quadrant** - query tasks by important and due soon
* **Time tracking** - track the time of every task
* **CSV storage** - you can easily backup or edit as a spreadsheet
* **Task lists and tags** - task can have one task list and many tags
* **Simple and complex views**

### Installation

Requires **Python 2.6**

Works on **Linux** and **Mac OS X**, should work on Windows too, except the install

0. Download https://github.com/stamat/todo/archive/master.zip
  * `wget https://github.com/stamat/todo/archive/master.zip`
0. Extract and `cd` to the extracted directory
  * `unzip mater.zip && cd todo-master`
0. `sudo ./install.py` - installs to *~/.todo* and creates a symlink */usr/local/bin/todo*
0. `todo`

Running `todo` will prompt you to enter the location for task CSV files to be saved. Personal recommendation would be your *dropbox* folder. This can be changed by editing a configuration file `~/.todo/config.cfg`

### Usage

Example usage in a form of a little tutorial. To learn how to use `todo` follow these sample steps

`todo -h` - displays help

#### Managing tasks

`todo My first task` - adds a task titled: *My first task*

`todo My second task @Home +groceries` - creates a new task *My second task*, adds it to *Home* task list and adds a tag *groceries*

`todo My third task` - adds a task titled: *My third task*

`todo --tasklist 1,3 @Work` - puts the first and third task to the task list *Work*

`todo --tag 1,3 +cool +super` - tag the first and third task with *cool* and *super* tags

`todo --rmtag 1,3 +super` - remove the tag *super* from the first and third

`todo --tasklist 1` - removes the first task from the task list *Work*

`todo -e 1 My first edited task` - first task becomes *My first edited task* all other details are preserved

`todo -i 1,3` - sets the first and third task to be important

`todo -i 1` - sets the first task to be unimportant

`todo -d 3` - sets the first task to be due soon

`todo -r 1` - removes the first task, the second task now becomes the first one and the third one becomes the second one

#### Listing tasks

`todo` - lists all tasks without clutter, in this case it would show *1 My second task 2 My third task*

`todo -l @Home` - displays all the task from task list *Work*

`todo -l +groceries` - displays all the task with the tag *groceries*

`todo -l important soon` - displays all the task that are important and due soon

`todo -l important` - displays all the task that are important

`todo -a` - displays the task table with details

`todo -a @Home` - displays the tasks in the task list in form of a table with details

`todo --tasklists` - list all task list with details

`todo --tags` - list all tags with details

#### Time tracking

`todo -t 1` - starts the time tracking

`Ctrl + C` - to end it


### Future development

* **Default view** - set a custom query to be your default view when you type `todo`
* **Complex queries** - query all the tasks in the task list which have a some tag and are important and due soon
* **Time tracking statistics** - how many time you spent per day/week/month/year on a single task, single task list, single tag
* **Completed tasks archive**
* **Import CSV** - there will be extendable definitions of CSV head to head extension
* **Server synchronisation**
* **Web client**
* **Desctop and Mobile apps**

### Why?

* **managing your time well makes you successful**
* **you cant fix what you can't measure**
* **time is money**

I used to think the last one is some capitalist bullshit, but it really means you need to value your time as something you need to live, like you need and love to eat and sleep. If you take into consideration the simple truth **LIFE IS TIME SPENT in between birth and death** then why wouldn't your time be precious?

##### This project was heavily influenced by:

**Randy Pausch Lecture: Time Management**
( https://www.youtube.com/watch?v=oTugjssqOT0 )

**Stephen Covey's Quadrant** ( https://en.wikipedia.org/wiki/First_Things_First_(book) )
