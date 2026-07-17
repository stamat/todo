#!/usr/bin/env python3
'''Unit tests for the pure/logic functions in todo.py.

Run with: python3 -m unittest discover -s tests

todo.py reads ~/.todo/config.cfg and creates data files at import time, so we
point HOME at a throwaway dir with a pre-seeded config BEFORE importing it.
'''

import os
import sys
import tempfile
import configparser
import unittest

# --- make todo.py importable without triggering the interactive first-run setup
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


if __name__ == '__main__':
    unittest.main()
