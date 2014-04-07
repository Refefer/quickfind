function! QuickFind()
  let tmpfile=tempname()
  let command = "qf -o > " . tmpfile
  return s:evaluate(command, tmpfile)
endfunction
command! -nargs=0 -complete=file -bang -bar QF call QuickFind()

function! QuickFindC()
  let tmpfile=tempname()
  let command = "qf -c -o > " . tmpfile
  return s:evaluate(command, tmpfile)
endfunction

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
command! -nargs=0 -complete=file -bang -bar TS call QuickFindC()


