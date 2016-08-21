import unittest
import unittest.mock as mock
from io import StringIO
from git_index.search import print_hit


class SearchTest(unittest.TestCase):
    maxDiff = None
    def create_inner_hit(self, offset):
        ih = mock.MagicMock()
        ih.meta.nested.offset = offset
        return ih

    def create_line(self, type, content):
        l = mock.MagicMock()
        l.type = type
        l.content = content
        return l

    def test_print_addition(self):
        hit = mock.MagicMock()
        hit.commit_sha = 'fake_sha'
        hit.path = 'fake_path'
        hit.meta.inner_hits.lines = [self.create_inner_hit(0)]
        hit.lines = [self.create_line('+', 'This is an addition')]
        hit.old_start = hit.new_start = 0
        file = StringIO()
        print_hit(hit, file, context=None)
        self.assertEqual(file.getvalue(), '\x1b[33mcommit fake_sha\x1b[0m\n\x1b[1mpath /fake_path\x1b[0m\n\x1b[36m@@ -0,0 +0,1 @@\x1b[0m\n\x1b[1m\x1b[32m+This is an addition\x1b[0m\n')

    def test_print_removal(self):
        hit = mock.MagicMock()
        hit.commit_sha = 'fake_sha'
        hit.path = 'fake_path'
        hit.meta.inner_hits.lines = [self.create_inner_hit(0)]
        hit.lines = [self.create_line('-', 'This is an removal')]
        hit.old_start = hit.new_start = 0
        file = StringIO()
        print_hit(hit, file, context=None)
        self.assertEqual(file.getvalue(), '\x1b[33mcommit fake_sha\x1b[0m\n\x1b[1mpath /fake_path\x1b[0m\n\x1b[36m@@ -0,1 +0,0 @@\x1b[0m\n\x1b[1m\x1b[31m-This is an removal\x1b[0m\n')

    def test_context_no_extra_lines(self):
        hit = mock.MagicMock()
        hit.commit_sha = 'fake_sha'
        hit.path = 'fake_path'
        hit.meta.inner_hits.lines = [self.create_inner_hit(0)]
        hit.lines = [self.create_line('-', 'This is an removal')]
        hit.old_start = hit.new_start = 0
        file = StringIO()
        print_hit(hit, file, context=5)
        self.assertEqual(file.getvalue(), '\x1b[33mcommit fake_sha\x1b[0m\n\x1b[1mpath /fake_path\x1b[0m\n\x1b[36m@@ -0,1 +0,0 @@\x1b[0m\n\x1b[1m\x1b[31m-This is an removal\x1b[0m\n')

    def test_context_extra_lines(self):
        hit = mock.MagicMock()
        hit.commit_sha = 'fake_sha'
        hit.path = 'fake_path'
        hit.meta.inner_hits.lines = [self.create_inner_hit(5)]
        hit.lines = [self.create_line('-', 'This is an removal'),
                     self.create_line('+', 'This is an addition'),
                     self.create_line('-', 'This is an removal'),
                     self.create_line('+', 'This is an addition'),
                     self.create_line('-', 'This is an removal'),
                     self.create_line('+', 'This is an addition'),
                     self.create_line('-', 'This is an removal'),
                     self.create_line('+', 'This is an addition'),
                     self.create_line('-', 'This is an removal'),
                     self.create_line('+', 'This is an addition')]
        hit.old_start = hit.new_start = 0
        file = StringIO()
        print_hit(hit, file, context=5)
        self.assertEqual(file.getvalue(), ('\x1b[33mcommit fake_sha\x1b[0m\n\x1b[1mpath /fake_path\x1b[0m\n'
                                           '\x1b[36m@@ -0,5 +0,5 @@\x1b[0m\n'
                                           '\x1b[31m-This is an removal\x1b[0m\n\x1b[32m+This is an addition\x1b[0m\n'
                                           '\x1b[31m-This is an removal\x1b[0m\n\x1b[32m+This is an addition\x1b[0m\n'
                                           '\x1b[31m-This is an removal\x1b[0m\n\x1b[1m\x1b[32m+This is an addition\x1b[0m\n'
                                           '\x1b[31m-This is an removal\x1b[0m\n\x1b[32m+This is an addition\x1b[0m\n'
                                           '\x1b[31m-This is an removal\x1b[0m\n\x1b[32m+This is an addition\x1b[0m\n'))
