quickfind
=========

Fuzzy finder for the terminal.  `quickfind` can search files in the file system, ctags files, or anything that can pipe.

Install
-------

To install from Pypi:

    pip install quickfind

To install the faster version with ctags from Pypi:

    pip install quickfind[ctags,fsnix]

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

Up and Down arrow keys selects which file to open.  Enter opens selects the highlighted file.

Stdin
-----
_quickfind_ can search on stdin when provided a naked '-':
    
    find . -type f | qf -

_quickfind_ can further be extended to execute custom commands after an item as been selected
    # To kill a process
    ps aux | qf - -f "kill -9 {2}"

_quickfind_ similarly can output to stdout with the '-o' flag rather than exec-ing the 
formatted command:
    
    # To view man a file
    man $(man -k . | qf - -f "man {1}" -o)

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
to open.

Tricks
-----
Add to your .bashrc:

    # To add ctrl+f as a qf hotkey.

    bind '"\C-f": "qf -w\n"'

    # To enable a new bash command, 'qcd', for quickly cd-ing to a directory.
    function qcd() {
        _OFILE=$(qf -d -o -f "{0}")
        if [ -n $_OFILE ]; then
            cd $_OFILE
        fi
        unset _OFILE
    }

    # To easily kill processes
    alias qkill="ps aux | qf - -f 'kill -f {2}'

