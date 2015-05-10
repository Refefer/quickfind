import os, re, fnmatch, sys
from collections import namedtuple
from itertools import islice

from .Source import Source
from quickfind.Searcher import Ranker, CString
from .Util import truncate_middle, rec_dir_up, highlight, StringRanker, simpleFormatter 

try:
    import fsnix.util as util
    walk = util.walk
except ImportError:
    walk = os.walk

if sys.version_info.major >= 3:
    xrange = range

File = namedtuple("File", "dir,name,sname")
class DirectorySource(Source):

    def __init__(self, dirs=".", ignore_directories=True, ignore_files=True, git_ignore=True):
        self.ignore_directories = ignore_directories
        self.ignore_files = ignore_files
        self.git_ignore = git_ignore
        self.startDirs = dirs

    def find_parent_gis(self, dir):
        dirs = rec_dir_up(os.path.abspath(dir))
        next(dirs)
        filters = []
        for dirname in dirs:
            pgi = os.path.join(dirname, '.gitignore')
            if os.path.isfile(pgi):
                filters.append((dirname, GitIgnoreFilter(dirname, '.gitignore')))

        return list(reversed(filters))

    def fetch(self):
        # optimize for the base case
        sd = set()
        lst = []
        if len(self.startDirs) == 1:
            return self.fetchDir(self.startDirs[0], sd)

        for d in self.startDirs:
            lst.extend(self.fetchDir(d, sd))

        return lst

    # Walk interface is annoying: to remove dirs, you have to del them from
    # the array
    def delDirs(self, dirs, f):
        for i in xrange(len(dirs) - 1, -1, -1):
            if not f(dirs[i]):
                del dirs[i]

    def fetchDir(self, d, seenDirs):
        lst = []
        ap = os.path.abspath
        filters = self.find_parent_gis(d) if self.git_ignore else []
        for dirname, dirs, filenames in walk(d):
            abspath = ap(dirname)
            if abspath in seenDirs:
                self.delDirs(dirs, lambda x: False)
                continue

            seenDirs.add(abspath)

            names = []
            if not self.ignore_files:
                names = filenames
            if not self.ignore_directories:
                names.extend(dirs)

            if self.git_ignore and '.gitignore' in filenames:
                gif = GitIgnoreFilter(abspath, '.gitignore')
                filters.append((abspath, gif))

            while filters:
                path, _ = filters[-1]
                if abspath.startswith(path): break
                filters.pop()

            fltr = filters[-1][1] if filters else None
            
            if fltr is None:
                files = (File(dirname, name, name.lower()) for name in names)
            else:
                files = (File(dirname, name, name.lower()) 
                        for name in names if fltr(name, abspath))

            lst.extend(files)

            # have to delete the names manually
            if fltr is not None:
                self.delDirs(dirs, lambda d: fltr(d, abspath))

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
            pf = pf.rstrip("/")

            dirname, basename = os.path.split(pf)
            dm = os.path.join(self.dirname, dirname.lstrip('/')).rstrip('/')
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

def ranker(inc_path):

    def rank(self, item):
        if self.inc_path:
            return os.path.join(item.dir.lower(), item.sname)
        else:
            return item.sname

    weight = lambda _, s: s.dir.count(os.sep) ** 0.5
    return StringRanker.new(weight, inc_path=inc_path, get_part=rank)

def dirFormatter(f, query, dims):
    return simpleFormatter(os.path.join(f.dir, f.name), query, dims)

