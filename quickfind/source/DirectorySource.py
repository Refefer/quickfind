import os, re, fnmatch
from collections import namedtuple

from Source import Source
from quickfind.Searcher import Ranker
from Util import truncate_middle

File = namedtuple("File", "dir,name,sname")
class DirectorySource(Source):

    def __init__(self, dir=".", ignore_directories=True, ignore_files=True, git_ignore=True):
        self.ignore_directories = ignore_directories
        self.ignore_files = ignore_files
        self.git_ignore = git_ignore
        self.startDir = dir
        self.filters = []

    def fetch(self):
        lst = []
        for dirname, dirs, filenames in os.walk(self.startDir):
            names = []
            if not self.ignore_files:
                names = filenames
            if not self.ignore_directories:
                names.extend(dirs)

            if self.git_ignore and '.gitignore' in filenames:
                gif = GitIgnoreFilter(dirname, '.gitignore')
                self.filters.append((dirname, gif))

            while self.filters:
                path, _ = self.filters[-1]
                if dirname.startswith(path): break
                self.filters.pop()

            fltr = None
            if self.filters:
                fltr = self.filters[-1][1]
            
            if fltr is None:
                files = (File(dirname, name, name.lower()) for name in names)
            else:
                files = (File(dirname, name, name.lower()) for name in names if fltr(name))
            lst.extend(files)

            # have to delete the names manually
            if fltr is not None:
                for i in xrange(len(dirs) - 1, -1, -1):
                    if not fltr(dirs[i]):
                        del dirs[i]

        return lst

class GitIgnoreFilter(object):

    def __init__(self, dirname, filename):
        self.fn = os.path.join(dirname, filename)
        filters = []
        with file(self.fn) as f:
            for fn in f:
                if fn.startswith('#'): 
                    continue
                rx = re.compile(fnmatch.translate(fn.strip()))
                filters.append(fnmatch.translate(fn.strip()))
            filters.append(r'\.git')
            
        self.filters = [re.compile('|'.join(filters))]

    def __call__(self, fn):
        for f in self.filters:
            if f.match(fn) is not None:
                return False
        return True

class SimpleRanker(Ranker):

    ws_query = False
    inc_path = False
    weight_f = staticmethod(lambda f: f.dir.count(os.sep) ** 0.5)

    def __init__(self, query):
        self.qs = query.lower()
        if self.ws_query:
            self.qs = self.qs.split()
        else:
            self.qs = [self.qs]

    def rank_part(self, q, part):
        if q not in part:
            return None

        score = len(part) - len(q)
        score -= 1.0 if part.startswith(q) else 0.0
        score -= 0.5 if part.endswith(q) else 0.0
        return score

    def rank(self, item):
        if self.inc_path:
            part = os.path.join(item.dir.lower(), item.sname)
        else:
            part = item.sname

        agg_score = 0.0
        for q in self.qs:
            score = self.rank_part(q, part)
            if score is None:
                return None
            agg_score += score

        
        return agg_score + self.weight_f(item)
    
    @staticmethod
    def new(ws_query, inc_path):
        return type('SimpleRanker', (SimpleRanker,), 
                    dict(ws_query=ws_query, inc_path=inc_path))


def FilePrinter(f, length):
    return truncate_middle(os.path.join(f.dir, f.name), length)
