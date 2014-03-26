import os.path
from collections import namedtuple
from Source import Source
from itertools import islice

import ctags

ENTRY_FIELDS = ("name", "file", "pattern", "lineNumber", "kind", "fileScope")
Entry = namedtuple("Entry", ENTRY_FIELDS)

class CtagsSource(Source):
    def __init__(self, filename):
        self.tag_file = ctags.CTags(filename)

    def _entry_to_Entry(self, entry):
        ed = dict((f, entry[f]) for f in ENTRY_FIELDS)
        ed['file'] = os.path.abspath(os.path.join(self.base_dir, ed['file']))
        return Entry(**ed)

    def _query(self, query):
        entry = ctags.TagEntry()
        if self.tag_file.first(entry):
            yield self.entry_to_Entry(entry)
            while self.tag_file.next(entry):
                yield self.entry_to_Entry(entry)

    def fetch(self):
        return map(self._query, self._entry_to_Entry)

class CompactEntryFormatter(object):
    
    def __init__(self, columns, surrounding=False):
        self.detail_cache = {}
        self.columns = columns
        self.surrounding = surrounding

    def format(self, entry):
        line_prefix = entry.name
        filename = self.truncate_middle(entry.file, self.columns - len(line_prefix))
        results = "%s  %s" % (line_prefix, filename)

        if self.surrounding:
            details = self.get_details(entry)
            if details is not None:
                idetails = self.indent(details, line_prefix.index(':')+5)
                results.append(idetails)

        return '\n'.join(results)


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
            with file(entry.file) as f:
                response = self.read_line_at(f, lineNum)
                if response is None:
                    response = entry.pattern
                self.detail_cache[entry] = response.strip()
        
        return self.detail_cache[entry]

    def truncate_middle(self, line, length=70):
        reduce_amt = len(line) - length

        # If it already fits
        if reduce_amt <= 0 or length <= 0:
            return line 

        reduce_amt += 3 # for the ellipsis

        start = (len(line) / 2) - (reduce_amt / 2)
        end = start + reduce_amt
        return "%s...%s" % (line[:start], line[end:])

    def indent(self, s, indent):
        return s.rjust(len(s) + indent)

