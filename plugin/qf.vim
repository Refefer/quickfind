function! QuickFind(...)
  if a:0 > 0
    let dir = a:1
  else
    let dir = ""
  endif

  let tmpfile=tempname()
  let command = "qf " . dir . " -o > " . tmpfile
  return s:evaluate(command, tmpfile)
endfunction
command! -nargs=* QF call QuickFind(<q-args>)

function! QuickFindC()
  let tmpfile=tempname()
  let command = "qf -c -o > " . tmpfile
  return s:evaluate(command, tmpfile)
endfunction
command! -nargs=0 TS call QuickFindC()

function! s:evaluate(command, tmpfile)
  execute "silent !".a:command
  if !filereadable(a:tmpfile)
    echo "Unable to load file!"
  else
    for someFile in readfile(a:tmpfile)
      exec "edit" someFile
    endfor
    "silent! call delete(a:tmpfile)
    redraw!
  endif
  return
endfunction

