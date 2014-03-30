import os, re, fnmatch, sys
from collections import namedtuple
from itertools import islice

from .Source import Source
from quickfind.Searcher import Ranker, CString
from .Util import truncate_middle, rec_dir_up, highlight

try:
    import fsnix.util as util
    walk = util.walk
except ImportError:
    walk = os.walk

if sys.version_info.major >= 3:
    xrange = range

File = namedtuple("File", "dir,name,sname")
class DirectorySource(Source):

    def __init__(self, dir=".", ignore_directories=True, ignore_files=True, git_ignore=True):
        self.ignore_directories = ignore_directories
        self.ignore_files = ignore_files
        self.git_ignore = git_ignore
        self.startDir = dir
        self.filters = []
        if git_ignore:
            self.find_parent_gis()

    def find_parent_gis(self):
        dirs = rec_dir_up(self.startDir)
        next(dirs)
        for dirname in dirs:
            pgi = os.path.join(dirname, '.gitignore')
            if os.path.isfile(pgi):
                self.filters.append(GitIgnoreFilter(dirname, '.gitignore'))
        self.filters.reverse()

    def fetch(self):
        lst = []
        for dirname, dirs, filenames in walk(self.startDir):
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
                files = (File(dirname, name, name.lower()) 
                        for name in names if fltr(name, dirname))
            lst.extend(files)

            # have to delete the names manually
            if fltr is not None:
                for i in xrange(len(dirs) - 1, -1, -1):
                    if not fltr(dirs[i], dirname):
                        del dirs[i]

        return lst

class GitIgnoreFilter(object):
    # Optimization
    lastdir = None
    last_path_filter = None

    globchars = re.compile('[*\[\]?]')
    def __init__(self, dirname, filename):
        self.dirname = dirname
        self.fn = os.path.join(dirname, filename)
        path_filters = []
        glob_filters = []
        exact_filters = set(['.git'])
        with open(self.fn) as f:
            gc = self.globchars
            for fn in f:
                if fn.startswith('#'): 
                    continue

                fn = fn.strip()
                if fn.startswith('/'):
                    path_filters.append(fn)
                elif gc.search(fn) is not None:
                    glob_filters.append(fnmatch.translate(fn.strip()))
                else:
                    exact_filters.add(fn)
            
        if glob_filters:
            self.glob_filters = [re.compile('|'.join(glob_filters))]
        else:
            self.glob_filters = []

        self.exact_filters = exact_filters
        self.path_filters = self.setup_path_filters(path_filters)

    def setup_path_filters(self, path_filters):
        # We can currently glob on only filename positions
        dirmaps = {}
        for pf in path_filters:
            while pf.endswith('/'):
                pf = pf[:-1]

            dirname, basename = os.path.split(pf)
            dm = os.path.join(self.dirname, dirname.lstrip('/'))
            glob = fnmatch.translate(basename.strip())
            if dm in dirmaps:
                dirmaps[dm].append(glob)
            else:
                dirmaps[dm] = [glob]

        # Build glob maps
        for k in dirmaps:
            dirmaps[k] = re.compile('|'.join(dirmaps[k]))

        return dirmaps 

    def __call__(self, fn, dirname):
        # check exact
        if fn in self.exact_filters:
            return False
        # Check global globs
        for f in self.glob_filters:
            if f.match(fn) is not None:
                return False

        lpf = self.path_filters.get(dirname)

        # check path dependent globs
        if lpf is not None and lpf.match(fn) is not None:
            return False

        return True

class SimpleRanker(Ranker):

    ws_query = False
    inc_path = False

    def __init__(self, query):
        self.qs = query.lower()
        if self.ws_query:
            self.qs = self.qs.split()
        else:
            self.qs = [self.qs]

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
        
        return agg_score + item.dir.count(os.sep) ** 0.5
    
    @staticmethod
    def new(ws_query, inc_path):
        return type('SimpleRanker', (SimpleRanker,), 
                    dict(ws_query=ws_query, inc_path=inc_path))

def formatter(f, query, dims):
    v = truncate_middle(os.path.join(f.dir, f.name), dims[0])
    return highlight(v, query)

