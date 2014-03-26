import os, re, fnmatch
from collections import namedtuple

from Source import Source
from quickfind.Searcher import Ranker

File = namedtuple("File", "dir,name,sname")
class DirectorySource(Source):

    def __init__(self, dir=".", ignore_directories=True, git_ignore=True):
        self.ignore_directories = ignore_directories
        self.git_ignore = git_ignore
        self.startDir = dir
        self.filters = []

    def fetch(self):
        lst = []
        for dirname, dirs, filenames in os.walk(self.startDir):
            names = filenames
            if not self.ignore_directories:
                names = dirs + filenames

            if self.git_ignore and '.gitignore' in filenames:
                gif = GitIgnoreFilter(dirname, '.gitignore')
                self.filters.append((dirname, gif))

            fltr = None
            if self.filters:
                path, _ = self.filters[-1]
                while self.filters and not dirname.startswith(path):
                    self.filters.pop()
                    if self.filters:
                        path, _ = self.filters[-1]

                if self.filters:
                    fltr = self.filters[-1][1]
            
            if fltr is None:
                files = (File(dirname, name, name.lower()) for name in names)
            else:
                files = (File(dirname, name, name.lower()) for name in names if fltr(name))
            lst.extend(files)

            # have to delete the names manually
            if self.filters:
                fltr = self.filters[-1][1]
                it = reversed([i for i, n in enumerate(dirs) if not fltr(n)])
                for idx in it:
                    del dirs[idx]

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

    def __init__(self, query):
        self.q = query.lower()

    def rank(self, item):
        if self.q not in item.sname:
            return None
        score = len(item.sname) - len(self.q)
        score += item.dir.count(os.sep) ** 0.5
        score -= 1.0 if item.sname.startswith(self.q) else 0.0
        return score

