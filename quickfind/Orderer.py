from operator import add
from multiprocessing import Process, Pipe, cpu_count
import heapq

class Orderer(object):
    def push_query(self, query):
        raise NotImplementedError()

    def pop_query(self):
        raise NotImplementedError()

    def top_items(self, N):
        raise NotImplementedError()

    def item_count(self):
        raise NotImplementedError()

    def cleanup(self):
        raise NotImplementedError()

class STOrderer(Orderer):

    def __init__(self, ranker, items):
        self.ranker = ranker
        its = [(0, item) for item in items]
        its.sort()
        self.heaps = [its]
        heapq.heapify( self.heaps[0] )

    @property
    def lhq(self):
        return self.heaps[-1]

    def _ranker(self, ranker, curHeap):
        for _, item in curHeap:
            score = ranker.rank(item)
            if score is not None:
                yield score, item

    def cleanup(self):
        pass

    def push_query(self, query):
        rank = self.ranker(query)
        self.heaps.append( list(self._ranker(rank, self.lhq)) )

    def pop_query(self):
        self.heaps.pop()

    def top_items(self, N):
        return [item for _, item in self._top_items(N)]

    def _top_items(self, N):
        return heapq.nsmallest(N, self.lhq)
    
    def item_count(self):
        return len(self.lhq)

    def total_count(self):
        return len(self.heaps[0])

def m_target(ranker, items, pipe):
    orderer = STOrderer(ranker, items)
    while True:
        command, args = pipe.recv()
        if command == 'exit':
            pipe.close()
            return

        pipe.send(getattr(orderer, command)(*args))

class MTOrderer(Orderer):

    def __init__(self, ranker, items, count=cpu_count()):
        self._total_count = len(items)

        procs = []
        pipes = []
        batch_size = len(items) / count
        for i in xrange(count):
            start = batch_size * i
            end = None if i == (count - 1) else start + batch_size
            batch = items[slice(start, end)]

            parent, child = Pipe()
            procs.append(Process(target=m_target, args=(ranker, batch, child)))
            procs[-1].start()
            pipes.append(parent)

        self.procs = procs
        self.pipes = pipes

    def _evict_pipe(self):
        return [pipe.recv() for pipe in self.pipes]

    def _eval_func(self, name, args):
        for pipe in self.pipes:
            pipe.send([name, args])

    def push_query(self, query):
        self._eval_func('push_query', [query])
        self._evict_pipe()

    def pop_query(self):
        self._eval_func('pop_query', [])
        self._evict_pipe()

    def top_items(self, N):
        self._eval_func('_top_items', [N])
        top_items = []
        for ti in self._evict_pipe():
            top_items.extend(ti)
        
        heapq.heapify(top_items)
        return [item for _, item in heapq.nsmallest(N, top_items)]
        
    def item_count(self):
        self._eval_func('item_count', [])
        return reduce(add, self._evict_pipe())

    def item_count(self):
        self._eval_func('item_count', [])
        return reduce(add, self._evict_pipe())

    def total_count(self):
        return self._total_count

    def cleanup(self):
        self._eval_func('exit', [])
        for pipe in self.pipes:
            pipe.close()

        for proc in self.procs:
            proc.join()

def auto_select(ranker, items, N=10000):
    if len(items) > N:
        return MTOrderer(ranker, items)

    return STOrderer(ranker, items)
