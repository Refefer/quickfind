import sys, tty, termios, os
import heapq
from contextlib import contextmanager
import curses

class Output(object):
    def init(self):
        raise NotImplementedError()

    def dimensions(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def printQuery(self, q):
        raise NotImplementedError()

    def printItem(self, item, selected, query):
        raise NotImplementedError()

    def printCount(self, total, current):
        raise NotImplementedError()

    def flush(self):
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()

class ScreenPrinter(Output):
    def __init__(self, printf, cols, rows):
        self.printf = printf
        self.cols = cols
        self.rows = rows

    def init(self):
        pass

    def cleanup(self):
        pass

    def dimensions(self):
        return self.cols, self.rows

    def clear(self):
        print ""

    def printQuery(self, q):
        print "$ " + q

    def printItem(self, idx, item, selected, query):
        prefix = "*" if selected else " "
        print "%s - %s" % (prefix, self.printf(item, query, self.dimensions()))

    def printCount(self, total, current):
        print "[%s / %s]" % (current, total)

    def flush(self):
        pass

class CursesPrinter(Output):
    def __init__(self, printf):
        self.printf = printf
        self.querylen = 0

    def init(self):
        self.window = curses.initscr()
        curses.start_color()
        curses.use_default_colors()
        curses.noecho()

    def cleanup(self):
        curses.echo()
        curses.endwin()

    def dimensions(self):
        y, x = self.window.getmaxyx()
        return x, y

    def printQuery(self, query):
        q = "$ " + query
        self.querylen = len(q)
        self.window.addstr(0, 0, q)

    def printItem(self, idx, item, selected, query):
        flags = curses.A_BOLD if selected else curses.A_NORMAL
        self.window.move(1 + idx, 0)
        for t in self.convert(self.printf(item, query, self.dimensions())):
            if not t.text:
                continue
            if t.fcolor == t.bcolor == -1:
                self.window.addstr(t.text, t.weight | flags)
            else:
                curses.init_pair(1, t.fcolor, t.bcolor)
                self.window.addstr(t.text, curses.color_pair(1) | t.weight | flags)

    def printCount(self, total, current):
        x, y = self.dimensions()

        counts = "[%s / %s]" % (current, total)
        self.window.addstr(y-1, x - len(counts)-1, counts)

    def convert(self, text):
        if not isinstance(text, list):
            text = [text]

        r = []
        for t in text:
            r.append(t if isinstance(t, CString) else CString(t))

        return r

    def clear(self):
        self.window.clear()

    def flush(self):
        self.window.move(0, self.querylen)
        self.window.refresh()

class CString(object):
    __slots__ = ('text', 'fcolor', 'bcolor', "weight")
    
    colors = {
        "default": -1, 
        "black": curses.COLOR_BLACK,
        "cyan": curses.COLOR_CYAN,
        "magenta": curses.COLOR_MAGENTA,
        "white": curses.COLOR_WHITE,
        "blue": curses.COLOR_BLUE,
        "green": curses.COLOR_GREEN,
        "red": curses.COLOR_RED,
        "yellow": curses.COLOR_YELLOW
    }

    weights = {
        "alt": curses.A_ALTCHARSET,
        "blink": curses.A_BLINK,
        "bold": curses.A_BOLD,
        "dim": curses.A_DIM,
        "normal": curses.A_NORMAL,
        "reverse": curses.A_REVERSE,
        "standout": curses.A_STANDOUT,
        "underlined": curses.A_UNDERLINE
    }

    def __init__(self, text, fcolor="default", bcolor="default", weight="normal"):
        self.text = unicode(text)
        self.fcolor = self.colors.get(fcolor, -1)
        self.bcolor = self.colors.get(bcolor, -1)
        self.weight = self.weights[weight]

class CharInput(object):
    def __call__(self):
        raise NotImplementedError()

class GetchUnix(CharInput):
    def __init__(self):
        import tty, sys
        self.fd = sys.stdin.fileno()

    def __call__(self):
        old_settings = termios.tcgetattr(self.fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(self.fd, termios.TCSADRAIN, old_settings)
        return ch

class Ranker(object):
    def __init__(self, query):
        self.query = query

    def rank(self, item):
        raise NotImplementedError()

class Searcher(object):
    def __init__(self, ranker, output):
        self.ranker = ranker
        self.output = output

    def _newHeap(self, query, curHeap):
        items = []
        ranker = self.ranker(query)
        for w, item in curHeap:
            score = ranker.rank(item)
            if score is not None:
                items.append((score, item))
        return sorted(items) 

    def _topItems(self, heap, N):
        items = []
        for i, (_, item) in enumerate(heap):
            if i == N: break
            items.append(item)
        return items

    def _loop(self, curHeaps, getchar):
        heapq.heapify(curHeaps[0])

        cur = ""
        selected = 0
        while True:
            nextchar = getchar()
            cols, rows = self.output.dimensions()

            # Ansi escape for arrows
            if ord(nextchar) == 27:
                getchar()
                nextchar = ord(getchar())

                # Up/down
                if nextchar == 66:
                    itemsShown = min(rows, len(curHeaps[-1])) - 1
                    selected = min(itemsShown, selected + 1)
                elif nextchar == 65:
                    selected = max(0, selected - 1)

            else :
                # Selected
                if nextchar == '\r':
                    h = curHeaps[-1]
                    for _ in xrange(selected):
                        if not h: break
                        heapq.heappop(h)

                    return heapq.heappop(h)[1] if h else None

                selected = 0
                
                # Escape code
                if ord(nextchar) in (3,4, 28, 26):
                    raise KeyboardInterrupt()

                # Delete/backspace
                if ord(nextchar) in (8, 127):
                    if cur != "":
                        cur = cur[:-1]
                        curHeaps.pop()
                else:
                    cur += nextchar
                    curHeaps.append(self._newHeap(cur, curHeaps[-1]))

            self._echo(cur, curHeaps[-1], selected, len(curHeaps[0]))

    def _echo(self, query, heap, selected, totalItems):
        self.output.clear()
        self.output.printQuery(query)

        cols, rows = self.output.dimensions()
        
        for i, item in enumerate(self._topItems(heap, rows-2)):
            self.output.printItem(i, item, i==selected, query)

        self.output.printCount(totalItems, len(heap))
        self.output.flush()


    def run(self, items, input=GetchUnix):
        self.output.init()
        try:
            heap = [(0, i) for i in items]
            heap.sort()
            self._echo("", heap, 0, len(items))
            return self._loop([heap], GetchUnix())
        finally:
            self.output.cleanup()
