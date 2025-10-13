syntax on
set nu "Enables line numbers
set relativenumber "Enables showing relative line numbers so you can jump around quickly (e.g. 5k or 3j)
set encoding=UTF-8
set smartindent "Will indent correct amount depending on language and wher eother code indents are
set tabstop=4
set softtabstop=4
set expandtab "Replace tab characters with spaces
set nowrap "Prevents long lines of text from wrapping
set incsearch "Will highlight text as you search within a file using /
set belloff=all
set mouse=a "Allow to use mouse in the editor
set cursorline

"Vim plugin manager settings. Run :PlugInstall in Vim to install plugins
call plug#begin('~/.vim/plugged')
Plug 'junegunn/vim-plug'
Plug 'vim-syntastic/syntastic'
Plug 'nvie/vim-flake8'
Plug 'Vimjas/vim-python-pep8-indent'

Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'

"Color schemes
Plug 'morhetz/gruvbox' "Retro groove color scheme for Vim

Plug 'preservim/nerdtree'
Plug 'junegunn/fzf', { 'do': { -> fzf#install() } } "Dependencies: brew install fzf bat ripgrep the_silver_searcher perl universal-ctags
Plug 'junegunn/fzf.vim'
Plug 'sheerun/vim-polyglot'
Plug 'prabirshrestha/vim-lsp'

"Jump between 'hunks' i.e. modified pieces of code with `]c` or `[c`
"While at a hunk, either add/stage changes with <leader>hs or revert/undo with <leader>hu.
"Preview the change <leader>hp.
Plug 'airblade/vim-gitgutter'
Plug 'tpope/vim-fugitive'

call plug#end()

let python_highlight_all=1
set background=dark
colorscheme gruvbox

"KEYBINDINGS
"nnoremap (non-recursive mapping) prevents infinite loops if <C-n> is defined elsewhere
"and it only affects Normal mode (no conflict with insert/visual mode mappings). 
"Recommended for plugin mappings to avoid side effects.

nnoremap <leader>n :NERDTreeFocus<CR>
nnoremap <C-n> : NERDTreeToggle<CR>
"This reveals current file in NERDTree and highlights it in the tree
nnoremap <C-f> :NERDTreeFind<CR>
nnoremap <silent> <C-p> :Files<CR>
nnoremap <silent> <C-g> :RG<CR>

" Toggle comment with Ctrl + / in visual mode
xnoremap <C-_> :<C-u>call ToggleComment()<CR>

" switch tabs with Tab and Shift + Tab.
nnoremap <Tab> :tabnext<CR>
nnoremap <S-Tab> :tabprev<CR>

let NERDTreeIgnore=['\.pyc$', '\~$'] "Ignore files in NERDTree

"Default Leader <leader> in Vim is \ backlash. Many users set it to , like this.
let mapleader='' "echo mapleader - should return current leader.
"Empty return means '\' default.
"Open NERDTree automatically when Vim starts and leave cursor in it.
"autocmd VimEnter * NERDTree

let g:airlinetheme='tomorrow'
let g:airline#extensions#tabline#enabled = 1 "Enables list of buffers.

" Customize fzf layout
let g:fzf_layout = { 'window' : {
  \ 'width': 0.9,
  \ 'height': 0.6,
  \ 'highlight': 'Comment',
  \ 'relative': v:true} } "If you want fzf's window to be relative to current window, set relative=true.

if executable('ruff')
  au User lsp_setup call lsp#register_server({
     \ 'name': 'ruff',
     \ 'cmd': {server_info->['ruff', 'server']},
     \ 'allowlist': ['python'],
     \ 'workspace_config': {},
     \ })
endif

function! ToggleComment()
  let start = line("'<")
  let end = line("'>")

  let cs = &commentstring != '' ? substitute(&commentstring, '%s', '', '') : '//'
  let cs_esc = escape(cs, '/\*.^$~[]')

  let all_commented = 1
  for lnum in range(start, end)
    if getline(lnum) !~ '^\s*' . cs_esc
      let all_commented = 0
      break
    endif
  endfor

  if all_commented
    execute start . ',' . end . 's/^\s*' . cs_esc . '\s\?//'
  else
    execute start . ',' . end . 's/^/' . cs . ' /'
  endif

  " Reselect previous visual area so you stay in visual mode
  call setpos("'<", [0, start, 1, 0])
  call setpos("'>", [0, end, 1, 0])
  normal! gv
endfunction
