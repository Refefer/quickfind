# To add ctrl+f as a qf hotkey.

bind '"\C-f": "qf\n"'
bind '"\C-e": "cd `qf -d`\n"'

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

# To easily delete files
alias grm="qf -m -f 'rm -rI {1}'"
