quickfind
=========

Fuzzy finder for the terminal.  `quickfind` can search both files in the file system
or a ctags file.

Install
-------

To install, clone the repo and type:

    python setup.py install

 in the directory.  
'sudo' might be needed, depending on permissions.

To Use
------

_quickfind_ has two forms: File search and CTags search, with File search as default.  

After installation, a new executable is added to the path 'qf'.  To use: 

    qf # for file search 

    qf -c # To search tags in CTags file

By default, file search automatically filters out files in .gitignore
