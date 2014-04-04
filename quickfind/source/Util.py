import os

from quickfind.Searcher import CString, Ranker

def truncate_front(line, length=70):
    reduce_amt = len(line) - length
    # If it already fits
    if reduce_amt <= 0 or length <= 0:
        return line 

    reduce_amt += 3 # for the ellipsis
    return '...'+line[reduce_amt:]

def truncate_middle(line, length=70):
    reduce_amt = len(line) - length

    # If it already fits
    if reduce_amt <= 0 or length <= 0:
        return line 

    reduce_amt += 3 # for the ellipsis

    start = (len(line) / 2) - (reduce_amt / 2)
    end = start + reduce_amt
    return "%s...%s" % (line[:start], line[end:])

def rec_dir_up(dir):
    if os.path.isdir(dir):
        while True:
            yield dir 
            newdir = os.path.split(dir)[0]
            if newdir == dir: break
            dir = newdir

def highlight(v, query, color="green"):
    i = v.lower().rfind(query.lower())
    if query and i > -1:
        left = v[:i]
        lq = len(query)
        highlight = v[i:i+lq]
        right = v[i+lq:]
        return [ left, CString(highlight, color), right ]

    return [v]

class StringRanker(Ranker):

    ws_query = False
    weight_f = lambda x: len(x) ** .5

    def __init__(self, query):
        self.qs = query.lower()
        if self.ws_query:
            self.qs = self.qs.split()
        else:
            self.qs = [self.qs]

    def get_parts(self, item):
        raise NotImplementedError()

    def rank_part(self, q, part):
        if q not in part:
            return None

        # Don't do more interesting ranking with one character
        lq = len(q)
        lp = len(part)
        if lq == 1:
            return lp

        score = (lp) ** 0.5
        score -= 1.0 if part.startswith(q) else 0.0
        score -= 1.0 if part.endswith(q) else 0.0
        return score

    def rank(self, item):
        part = self.get_part(item)

        agg_score = 0.0
        for q in self.qs:
            score = self.rank_part(q, part)
            if score is None:
                return None
            agg_score += score
        
        return agg_score + self.weight_f(item)
    
    @staticmethod
    def new(ws_query, weight_f=lambda *x: 0, **kwargs):
        kwargs['ws_query'] = ws_query
        kwargs['weight_f'] = weight_f
        return type('StringRanker', (StringRanker,), kwargs)

def simpleFormatter(item, query, dims):
    v = truncate_middle(item, dims[0])
    return highlight(v, query)

