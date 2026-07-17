#!/usr/bin/env python3
'''Unit tests for the pure/logic functions in todo.py.

Run with: python3 -m unittest discover -s tests

todo.py reads ~/.todo/config.cfg and creates data files at import time, so we
point HOME at a throwaway dir with a pre-seeded config BEFORE importing it.
'''

import os
import io
import sys
import csv
import contextlib
import tempfile
import configparser
import unittest

# todo.py now runs its config/first-run side effects inside _init() (called from
# _main()), so the module imports cleanly. HOME is still pointed at a throwaway
# dir so nothing can touch a real ~/.todo if _init() ever runs.
_TMP = tempfile.mkdtemp(prefix='todo_test_')
os.environ['HOME'] = _TMP
os.makedirs(os.path.join(_TMP, '.todo'), exist_ok=True)
_cfg = configparser.ConfigParser()
_cfg['general'] = {'dir': _TMP, 'name': 'Test'}
with open(os.path.join(_TMP, '.todo', 'config.cfg'), 'w') as _f:
    _cfg.write(_f)

sys.argv = ['todo.py']  # empty command line; execution is guarded by __main__ anyway
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import todo  # noqa: E402


def _seed_csv(rows):
    '''Write rows to a fresh todo.csv and point todo's globals at it.'''
    d = tempfile.mkdtemp(prefix='todo_io_')
    path = os.path.join(d, 'todo.csv')
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=todo.fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    todo.destination_dir = d
    todo.filename = path
    todo.tmp_filename = os.path.join(d, 'tmp_todo.csv')
    return path


def _read_csv():
    with open(todo.filename, newline='') as f:
        return list(csv.DictReader(f))


class TestDeltatime(unittest.TestCase):
    def test_empty_string(self):
        self.assertEqual(todo._deltatime(''), '0:00:00')

    def test_seconds(self):
        self.assertEqual(todo._deltatime('90'), '0:01:30')

    def test_hours(self):
        self.assertEqual(todo._deltatime('3661'), '1:01:01')

    def test_strips_fraction(self):
        self.assertEqual(todo._deltatime('1.5'), '0:00:01')


class TestCsvlist(unittest.TestCase):
    def test_multiple(self):
        self.assertEqual(todo._csvlist("['a', 'b']"), ['a', 'b'])

    def test_single(self):
        self.assertEqual(todo._csvlist("['solo']"), ['solo'])

    def test_no_space_separator(self):
        self.assertEqual(todo._csvlist("['a','b']"), ['a', 'b'])

    def test_non_list_returns_none(self):
        self.assertIsNone(todo._csvlist(''))
        self.assertIsNone(todo._csvlist('not a list'))


class TestCsvNum(unittest.TestCase):
    def test_int(self):
        self.assertEqual(todo._csvint(' 5 '), 5)

    def test_int_empty(self):
        self.assertEqual(todo._csvint(''), 0)

    def test_int_garbage(self):
        self.assertEqual(todo._csvint('abc'), 0)

    def test_float(self):
        self.assertEqual(todo._csvfloat('1.5'), 1.5)

    def test_float_empty(self):
        self.assertEqual(todo._csvfloat('   '), 0)


class TestIsImportant(unittest.TestCase):
    def test_falsey(self):
        self.assertFalse(todo._isImportant(''))
        self.assertFalse(todo._isImportant('0'))
        self.assertFalse(todo._isImportant(None))

    def test_truthy(self):
        self.assertTrue(todo._isImportant('1'))
        self.assertTrue(todo._isImportant('42'))


class TestIsDue(unittest.TestCase):
    def test_falsey(self):
        self.assertFalse(todo._isDue(''))
        self.assertFalse(todo._isDue('0'))
        self.assertFalse(todo._isDue('later'))
        self.assertFalse(todo._isDue(None))

    def test_truthy(self):
        self.assertTrue(todo._isDue('1'))
        self.assertTrue(todo._isDue('soon'))


class TestParseQuery(unittest.TestCase):
    def test_tasklist_and_tag(self):
        q = todo.parseQuery('@work +urgent')
        self.assertEqual(q['tasklists'], ['work'])
        self.assertEqual(q['tags'], ['urgent'])

    def test_important_and_due(self):
        q = todo.parseQuery('important soon')
        self.assertTrue(q['important'])
        self.assertTrue(q['due'])

    def test_unimportant_and_later(self):
        q = todo.parseQuery('unimportant later')
        self.assertFalse(q['important'])
        self.assertFalse(q['due'])

    def test_empty(self):
        self.assertEqual(todo.parseQuery(''), {})


class TestQuery(unittest.TestCase):
    def _rows(self):
        return [
            {'tasklist': 'work', 'tags': "['urgent']", 'important': '1', 'due': '1'},
            {'tasklist': 'home', 'tags': "['chore']", 'important': '0', 'due': '0'},
            {'tasklist': 'work', 'tags': "['chore']", 'important': '0', 'due': 'soon'},
        ]

    def test_filter_by_tasklist(self):
        res = todo.query({'tasklists': ['work']}, self._rows())
        self.assertEqual(len(res), 2)
        self.assertEqual([r['count'] for r in res], [1, 3])

    def test_filter_by_tag(self):
        res = todo.query({'tags': ['chore']}, self._rows())
        self.assertEqual(len(res), 2)

    def test_filter_important(self):
        res = todo.query({'important': True}, self._rows())
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]['count'], 1)

    def test_combined(self):
        res = todo.query({'tasklists': ['work'], 'due': True}, self._rows())
        self.assertEqual([r['count'] for r in res], [1, 3])


class TestSetconf(unittest.TestCase):
    def test_creates_section_and_sets(self):
        conf = configparser.ConfigParser()
        todo._setconf(conf, 'general', 'dir', '/tmp/x')
        self.assertEqual(conf.get('general', 'dir'), '/tmp/x')

    def test_overwrites_existing(self):
        conf = configparser.ConfigParser()
        todo._setconf(conf, 'general', 'dir', '/a')
        todo._setconf(conf, 'general', 'dir', '/b')
        self.assertEqual(conf.get('general', 'dir'), '/b')


class TestDetailsRegression(unittest.TestCase):
    '''--details used int(row['due']); 'soon'/'later'/'' raised ValueError.'''
    def test_details_survives_non_int_status(self):
        _seed_csv([
            {'task': 'a', 'important': '', 'due': 'soon',
             'tasklist': 'work', 'tags': "['x']", 'time_spent': '90'},
            {'task': 'b', 'important': '1', 'due': 'later',
             'tasklist': '', 'tags': '', 'time_spent': ''},
        ])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            todo.display_detailed()  # must not raise
        out = buf.getvalue()
        self.assertIn('a', out)
        self.assertIn('b', out)


class TestParsenum(unittest.TestCase):
    def setUp(self):
        _seed_csv([{'task': 't1'}, {'task': 't2'}, {'task': 't3'}])

    def test_valid(self):
        self.assertEqual(todo._parsenum('2'), [2])

    def test_last(self):
        self.assertEqual(todo._parsenum('last'), [3])

    def test_mod(self):
        self.assertEqual(todo._parsenum('2', -1), [1])

    def test_skips_garbage(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(todo._parsenum('1,abc,3'), [1, 3])
        self.assertIn('invalid task id', buf.getvalue())

    def test_all_garbage_returns_empty(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(todo._parsenum('nope'), [])


class TestGetSet(unittest.TestCase):
    def test_roundtrip(self):
        _seed_csv([{'task': 'old'}, {'task': 'two'}])
        todo._set([0], 'task', 'new', False)  # 0-based list, like _parsenum(x, -1)
        self.assertEqual(todo._get(1, 'task'), 'new')
        self.assertEqual(todo._get(2, 'task'), 'two')


class TestDelete(unittest.TestCase):
    def test_delete_middle(self):
        _seed_csv([{'task': 'a'}, {'task': 'b'}, {'task': 'c'}])
        with contextlib.redirect_stdout(io.StringIO()):
            todo.delete('2')
        self.assertEqual([r['task'] for r in _read_csv()], ['a', 'c'])


class TestNew(unittest.TestCase):
    def test_parses_tasklist_and_tags(self):
        _seed_csv([])  # header only
        with contextlib.redirect_stdout(io.StringIO()):
            todo.new('buy milk @home +urgent')
        rows = _read_csv()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['task'], 'buy milk')
        self.assertEqual(rows[0]['tasklist'], 'home')
        self.assertEqual(todo._csvlist(rows[0]['tags']), ['urgent'])


if __name__ == '__main__':
    unittest.main()
