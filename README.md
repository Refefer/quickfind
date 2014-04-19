quickfind
=========

Fuzzy finder for the terminal.  `quickfind` can search files in the file system, ctags files, or anything that can pipe.

Install
-------

To install from Pypi:

    pip install quickfind

To install the faster version with ctags from Pypi:

    pip install quickfind[ctags,fsnix]

To upgrade to the latest version:
    
    pip install quickfind --upgrade

To install from source, clone the repo and type:

    python setup.py install

 in the directory.  

'sudo' might be needed, depending on permissions.

To Use
------

_quickfind_ has two builtin forms: File search and CTags search, with File search as default.  

After installation, a new executable is added to the path 'qf'.  To use: 

    qf # for file search 

    qf -c # To search tags in CTags file

and start typing!  _quickfind_ can be configured to match against file name and/or path
while selecting either files, directories, or both.  By default, it filters out files listed
in a tree's .gitignore.

The Up/Down (or Alt-P/Alt-N) keys selects which file to open.  Enter opens selects the highlighted file.  In multiple select mode, toggles the inclusion of the selected file.

Sometimes a single query isn't enough to differentiate between the files.  By pressing Tab, _quickfind_ will add another 'searcher' query for additional filtering.


Multiple files
--------------
Multiple entries can be selected when the '-m' flag is provided.  In multiselect mode, 
'Enter' adds the highlighted file to the selection.  After all selections have been made, ctrl+D exits _quickfind_ with the selected entries.

Stdin
-----
_quickfind_ can search on stdin:
    
    find . -type f | qf

_quickfind_ can further be extended to execute custom commands after an item as been selected
    # To kill a process
    ps aux | qf -f "kill -9 {2}"

_quickfind_ similarly can output to stdout with the '-o' flag rather than exec-ing the 
formatted command:
    
    # To view man a file
    man $(man -k . | qf -f "{1}" -o)

Commands
--------
By default, _quickfind_ will execute "$EDITOR {0}", where "{0}" represents the entire 
selected record.  In "{N}", N represents the Nth piece split by the delimiter specified
by -D.  By default, the delimiter is whitespace.  

Vim
---
A basic vim plugin has been developed to open files up with _quickfind_.  To install,
copy `plugin/qf.vim` to your vim plugin directory (usually ~/.vim/plugin/).  To use,
simply type `:QF` in normal mode to open up the _quickfind_ daemon and choose the file
to open.  :TS triggers _quickfind_ with ctags.

Tricks
-----
Add to your .bashrc:

    # To add ctrl+f as a qf hotkey.

    bind '"\C-f": "qf\n"'

    # To enable a new bash command, 'qcd', for quickly cd-ing to a directory.
    function qcd() {
        _OFILE=$(qf -d -o -f "{0}")
        if [ -n "$_OFILE" ]; then
            cd $_OFILE
        fi
        unset _OFILE
    }

    # To easily kill processes
    alias qkill="ps aux | qf - -f 'kill -f {2}'"

    # To easily git add a file
    alias gadd="git status --short | qf -m -f 'git add {2}'"

