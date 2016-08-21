import curses
import itertools
from elasticsearch_dsl import Q, Search


def line_offsets(hit):
    return {ih.meta.nested.offset for ih in hit.meta.inner_hits.lines}


def relevant_line_numbers(lines, offsets, context):
    return set(itertools.chain.from_iterable(range(max(0, o - context), min(o + context, len(lines)))
                                             for o in offsets))


class HitsWindow:
    def __init__(self, screen, hits, context=5):
        self.screen = screen
        self.hits = hits
        self.context = context
        self.rows = sum(len(relevant_line_numbers(h.lines, line_offsets(h), context)) + 2 for h in hits)
        self.cols = max(len(l.content) for h in hits for l in h.lines)
        self.top = 0
        self.left = 0
        self.pad = curses.newpad(self.rows, self.cols)
        self.pad.keypad(1)

    def display(self):
        self.add_hits()
        self.refresh()
        while self.continue_display():
            pass

    def refresh(self):
        size = self.screen.getmaxyx()
        self.pad.refresh(self.top, self.left, 0, 0, size[0] - 1, size[1] - 2)

    def continue_display(self):
        ch = self.pad.getch()
        if ch == ord("q"):
            return False
        if ch in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
            if ch == curses.KEY_UP:
                self.top = max(self.top - 1, 0)
            elif ch == curses.KEY_DOWN:
                size = self.screen.getmaxyx()
                self.top = min(self.top + 1, self.rows - size[0])
            elif ch == curses.KEY_LEFT:
                self.left = max(self.left - 1, 0)
            elif ch == curses.KEY_RIGHT:
                size = self.screen.getmaxyx()
                self.left = min(self.left + 1, self.cols - size[1] + 1)
            self.refresh()
        return True

    def add_hits(self):
        y = 0
        for h in self.hits:
            y = self.add_hit(y, h)

    def add_hit(self, y, hit):
        self.pad.addstr(y, 0, 'commit {}'.format(hit.commit_sha), curses.color_pair(1))
        self.pad.addstr(y + 1, 0, 'path /{}'.format(hit.path), curses.A_BOLD)
        offsets = line_offsets(hit)
        line_nums = relevant_line_numbers(hit.lines, offsets, self.context)
        for i, line_pos in enumerate(sorted(line_nums)):
            line = hit.lines[line_pos]
            color = curses.color_pair(3) if line.type == '+' else curses.color_pair(2)
            text = line.type + line.content.rstrip()
            if line_pos in offsets:
                self.pad.addstr(y + 2 + i, 0, text, color | curses.A_BOLD)
            else:
                self.pad.addstr(y + 2 + i, 0, text, color)
        return y + 2 + len(line_nums)


def search(query):
    s = Search().query('nested', path='lines', inner_hits={}, query=Q({'match': {'lines.content': query}}) &
                                                                    Q({'term': {'lines.type': '+'}}))
    rv = s.execute()
    curses.wrapper(display, rv.hits)


def display(stdscr, hits):
    try:
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)
        hits_window = HitsWindow(stdscr, hits)
        hits_window.display()
    finally:
        curses.curs_set(1)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
