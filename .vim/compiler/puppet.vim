" Vim compiler file
" Compiler:     Puppet syntax checks (puppet --debug --noop) v1.0
" Maintainer:   Joshua Barratt <jbarratt@serialized.net>
" Last Change:  2009 Apr 1

" Changelog:
"
" 1.0: initial version
" 

if exists("current_compiler")
  finish
endif
let current_compiler = "puppet"

" there is no pipes under windows, vi use temp file
" and as perl outputs to stderr this have to be handled corectly
if has("win32")
    setlocal shellpipe=1>&2\ 2>
endif

setlocal makeprg=puppet\ --debug\ --noop\ %

" Sample errors:
" Perl: Type of arg 1 to push must be array (not hash element) at NFrame.pm line 129, near ");"
" setlocal errorformat=%m\ at\ %f\ line\ %l%.%#,
                    "\%-G%.%# " ignore any lines that didn't match one of the patterns above
" Puppet: Could not parse for environment production: Syntax error at '}' at /home/jbarratt/home_resource.pp:14
setlocal errorformat=%m\ at\ %f:%l
