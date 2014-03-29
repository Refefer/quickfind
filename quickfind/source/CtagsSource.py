import os
from collections import namedtuple
from Source import Source
from itertools import islice

from quickfind.Searcher import Ranker,CString
from Util import truncate_middle, truncate_front, highlight

import ctags

ENTRY_FIELDS = ("name", "file", "disp", "pattern", "lineNumber", "kind", "fileScope")
Entry = namedtuple("Entry", ENTRY_FIELDS)

class CtagsSource(Source):
    def __init__(self, filename):
        self.tag_file = ctags.CTags(filename)
        self.base_dir = os.path.split(filename)[0]

    def _entry_to_Entry(self, entry):
        ed = dict((f, entry[f]) for f in ENTRY_FIELDS)
        ed['file'] = os.path.abspath(os.path.join(self.base_dir, ed['file']))
        return Entry(**ed)

    def _query(self):
        entry = ctags.TagEntry()
        if self.tag_file.first(entry):
            yield self._entry_to_Entry(entry)
            while self.tag_file.next(entry):
                yield self._entry_to_Entry(entry)

    def fetch(self):
        return list(self._query())

class CtagsFormatter(object):
    
    def __init__(self, columns, surrounding=True):
        self.detail_cache = {}
        self.surrounding = surrounding

    def __call__(self, entry, query, dims):
        line_prefix = '%s %s   ' % (entry.kind, entry.name)

        columns = dims[0]

        details = ""
        if self.surrounding and columns >= 80:
            dets = self.get_details(entry)
            if dets is not None:
                details = "   " + dets

        trunc_len = columns - (len(line_prefix) + len(details))
        if details:
            filename = truncate_front(entry.file, trunc_len)
        else:
            filename = truncate_middle(entry.file, trunc_len)

        lens = len(line_prefix)
        res  = highlight(line_prefix, query)
        res.append(CString(filename, "cyan"))
        res.append(details)
        return res

    def read_line_at(self, f, num):
        return next(islice(f, num - 1, num), None)

    def get_details(self, entry):
        # If a file, print nothing
        if entry.kind == 'F':
            return None

        # If -R or not a real line
        if entry.lineNumber == 0:
            return entry.pattern

        if entry not in self.detail_cache:
            lineNum = entry.lineNumber
            if not os.path.isfile(entry.file):
                self.detail_cache[entry] = None
            else:
                with file(entry.file) as f:
                    response = self.read_line_at(f, lineNum)
                    if response is None:
                        response = entry.pattern
                    self.detail_cache[entry] = response.strip()
        
        return self.detail_cache[entry]

    def indent(self, s, indent):
        return s.rjust(len(s) + indent)

class CtagsRanker(Ranker):

    def __init__(self, query):
        self.q = query.lower()

    def rank(self, item):
        sname = item.name.lower()
        if self.q not in sname:
            return None

        score = len(item.name) - len(self.q)
        score += item.file.count(os.sep) ** 0.5
        score -= 1.0 if sname.startswith(self.q) else 0.0
        return score

