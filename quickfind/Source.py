import os, re, fnmatch
from collections import namedtuple

class Source(object):
    def fetch(self):
        raise NotImplementedError()

File = namedtuple("File", "dir,name,sname")
class DirectorySource(object):

    def __init__(self, dir=".", ignore_directories=True, git_ignore=True):
        self.ignore_directories = ignore_directories
        self.git_ignore = git_ignore
        self.startDir = dir
        self.filters = []

    def _visit(self, agg, dirname, names):

        fltr = lambda x: True
        if self.ignore_directories:
            fltr = lambda n: os.path.isfile(os.path.join(dirname, n)) 

        if self.git_ignore and '.gitignore' in names:
            gif = GitIgnoreFilter(dirname, '.gitignore')
            self.filters.append((dirname, gif))

        elif self.filters:
            path, _ = self.filters[-1]
            while self.filters and not dirname.startswith(path):
                self.filters.pop()

            if self.filters:
                _fltr = fltr
                fltr = lambda x: _fltr(x) and self.filters[-1][1](x)
        
        agg.extend(File(dirname, name, name.lower()) 
                for name in names if fltr(name))

        # have to delete the names manually
        if self.filters:
            fltr = self.filters[-1][1]
            it = reversed([i for i, n in enumerate(names) if not fltr(n)])
            for idx in it:
                del names[idx]

    def fetch(self):
        lst = []
        os.path.walk(self.startDir, self._visit, lst)
        return lst

class GitIgnoreFilter(object):

    def __init__(self, dirname, filename):
        self.fn = os.path.join(dirname, filename)
        self.filters = []
        with file(self.fn) as f:
            for fn in f:
                if fn.startswith('#'): 
                    continue
                rx = re.compile(fnmatch.translate(fn.strip()))
                self.filters.append(rx)
            self.filters.append(re.compile(r'\.git'))

    def __call__(self, fn):
        for f in self.filters:
            if f.match(fn) is not None:
                return False
        return True

