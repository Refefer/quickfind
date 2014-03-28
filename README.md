quickfind
=========

Fuzzy finder for the terminal.  `quickfind` can search both files in the file system
or a ctags file.  
Install
-------

To install from Pypi:

    pip install quickfind.

To install from source, clone the repo and type:

    python setup.py install

 in the directory.  

'sudo' might be needed, depending on permissions.

To Use
------

_quickfind_ has two forms: File search and CTags search, with File search as default.  

After installation, a new executable is added to the path 'qf'.  To use: 

    qf # for file search 

    qf -c # To search tags in CTags file

and start typing!  _quickfind_ can be configured to match against file name and/or path
while selecting either files, directories, or both.  By default, it filters out files listed
in a tree's .gitignore.

Up and Down arrow keys selects which file to open.  Enter opens the current file with $EDITOR.
If -s FILENAME is specified, quickfind writes the selected file to disk.

Tricks
-----
Add to your .bashrc:

    bind '"\C-f": "qf\n"'

to add ctrl+f as a qf hotkey.

Add to your .bashrc:

    function goto() {
        _OFILE=/tmp/qf.$$
        qf -d -s $_OFILE
        if [ -f $_OFILE ]; then
            cd `cat $_OFILE`
            rm $_OFILE
        fi
        unset _OFILE
    }

to enable a new bash command, 'goto', for quickly cd-ing to a directory.

Have a lot of files with similar names?  Add the '-w' flag to allow multiple searchers.  '-w'
splits queries by white space: a query for "hello world" would result in two filters: 
"hello" and "world", requiring a file to match both.  This can be useful for specifying 
part of a filename and then the file extension.
