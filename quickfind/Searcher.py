from __future__ import print_function
import sys, tty, termios, os
import heapq
from contextlib import contextmanager
import curses
import multiprocessing

if sys.version_info.major >= 3:
    textize = str
else:
    textize = lambda x: unicode(x, errors="ignore")


class Output(object):
    def init(self):
        raise NotImplementedError()

    def dimensions(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def getChr(self):
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
        self.getChar = GetchUnix()

    def init(self):
        pass

    def cleanup(self):
        pass

    def dimensions(self):
        return self.cols, self.rows

    def clear(self):
        print("")

    def printQuery(self, q):
        print("$ " + q)

    def printItem(self, idx, item, selected, query):
        prefix = "*" if selected else " "
        print("%s - %s" % (prefix, self.printf(item, query, self.dimensions())))

    def printCount(self, total, current):
        print("[%s / %s]" % (current, total))

    def flush(self):
        pass

class CursesPrinter(Output):
    
    def __init__(self, printf):
        self.printf = printf
        self.querylen = 0
        self.getChar = GetchUnix()
        self.colors = {}
        self.TAB = CString("~", fcolor="red")

    def init(self):
        self.window = curses.initscr()
        self.window.nodelay(0)
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
        newQ = []
        for p in q.split('\t'):
            newQ.extend((p, self.TAB))
        newQ = self.convert(newQ[:-1])

        self.querylen = len(q)
        for nq in newQ:
            self._printText(nq, len(q))
    
    def _printText(self, t, maxX, flags=curses.A_NORMAL):
        text = t.text[:(maxX - self.window.getyx()[1])]
        if not text: return
        if t.fcolor == t.bcolor == -1:
            self.window.addstr(text, t.weight | flags)
        else:
            cp = (t.fcolor, t.bcolor)
            if cp not in self.colors:
                num = 1 if not self.colors else max(self.colors.values()) + 1 
                self.colors[cp] = num
                curses.init_pair(num, t.fcolor, t.bcolor)

            self.window.addstr(text, curses.color_pair(self.colors[cp]) | t.weight | flags)

    def printItem(self, idx, item, selected, query):
        flags = curses.A_BOLD if selected else curses.A_NORMAL
        self.window.move(1 + idx, 0)
        colors = {}
        num = 1
        x, y = self.dimensions()
        for t in self.convert(self.printf(item, query, (x,y))):
            self._printText(t, x, flags)

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
        self.colors.clear()

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
        self.text = textize(text)
        self.fcolor = self.colors.get(fcolor, -1)
        self.bcolor = self.colors.get(bcolor, -1)
        self.weight = self.weights[weight]

class GetchUnix(object):
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

    def _ranker(self, ranker, curHeap):
        for w, item in curHeap:
            score = ranker.rank(item)
            if score is not None:
                yield (score, item)

    def _newHeap(self, query, curHeap):
        return list(self._ranker(self.ranker(query), curHeap)) 

    def _topItems(self, heap, N):
        items = []
        for (_, item) in heapq.nsmallest(N, heap):
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
                    h = self._topItems(curHeaps[-1], selected + 1)
                    try:
                        return h[selected]
                    except IndexError:
                        return None

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


    @contextmanager
    def redirStdout(self):
        stdout = os.dup(sys.stdout.fileno())
        os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
        yield
        os.dup2(stdout, sys.stdout.fileno())

    def run(self, items):
        with self.redirStdout():
            self.output.init()
            try:
                heap = [(0, i) for i in items]
                heap.sort()
                self._echo("", heap, 0, len(items))
                return self._loop([heap], self.output.getChar)
            finally:
                self.output.cleanup()

