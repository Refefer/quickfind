function! QuickFind()
  let tmpfile=tempname()
  let command = "qf -o > " . tmpfile
  execute "silent !".command

  if !filereadable(tmpfile)
    echo "Unable to load file!"
  else
    for someFile in readfile(tmpfile)
      exec "edit" someFile
    endfor
    silent! call delete(tmpfile)
    redraw!
  endif
endfunction
command! -nargs=0 -complete=file -bang -bar QF call QuickFind()
