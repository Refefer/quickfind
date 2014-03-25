import sys, tty, termios, os
import heapq

class Output(object):
    def init(self):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def printQuery(self, q):
        raise NotImplementedError()

    def printItem(self, item, selected):
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()

class ScreenPrinter(Output):
    def __init__(self, printf):
        self.printf = printf

    def init(self):
        pass

    def cleanup(self):
        pass

    def clear(self):
        print ""

    def printQuery(self, q):
        print "Query: " + q

    def printItem(self, item, selected):
        prefix = "*" if selected else " "
        print "%s - %s" % (prefix, self.printf(item))

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
        newHeap = []
        ranker = self.ranker(query)
        for w, item in curHeap:
            score = ranker.rank(item)
            if score is not None:
                heapq.heappush(newHeap, (score, item))
        return newHeap

    def _topItems(self, heap, N=5):
        h = heap[:]
        items = []
        for _ in xrange(N):
            if len(h) == 0:
                break
            w, item  = heapq.heappop(h)
            items.append(item)
        return items

    def _loop(self, items, getchar):
        curHeaps = [ [(0, i) for i in items] ]
        heapq.heapify(curHeaps[0])

        cur = ""
        selected = -1
        while True:
            nextchar = getchar()

            # Ansi escape for arrows
            if ord(nextchar) == 27:
                getchar()
                nextchar = ord(getchar())

                # Up/down
                if nextchar == 66:
                    selected = min(4,selected + 1)
                elif nextchar == 65:
                    selected = max(0,selected - 1)

            else :
                # Selected
                if nextchar == '\r':
                    idx = max(selected, 0)
                    h = curHeaps[-1]

                    for _ in xrange(idx):
                        if not h: break
                        heapq.heappop(h)

                    return heapq.heappop(h)[1] if h else None

                selected = -1
                
                # Escape code
                if ord(nextchar) in (3,4, 28, 26):
                    raise KeyboardInterrupt()

                # Delete/backspace
                if ord(nextchar) in (8, 127):
                    cur = cur[:-1]
                    if cur != "":
                        curHeaps.pop()
                else:
                    cur += nextchar
                    curHeaps.append(self._newHeap(cur, curHeaps[-1]))

            self.output.clear()
            self.output.printQuery(cur)
            
            for i, item in enumerate(self._topItems(curHeaps[-1], 5)):
                self.output.printItem(item, i==selected)

    def run(self, items, input=GetchUnix):
        self.output.init()
        try:
            return self._loop(items, GetchUnix())
        finally:
            self.output.cleanup()
