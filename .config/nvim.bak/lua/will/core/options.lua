-- netrw is a built-in nvim file tree explorer
vim.cmd("let g:netrw_liststyle = 3")


local opt = vim.opt
opt.relativenumber = true
opt.number = true

-- tabs & identation
opt.tabstop = 4 -- 4 spaces for tabs (pep8 default)
opt.shiftwidth = 2 -- 2 spaces for indent width
opt.expandtab = true -- expand tabs to spaces
opt.autoindent = true -- copy indent from current line when starting new one.

opt.wrap = false -- disable line wrapping

-- search settings
opt.ignorecase = true -- ignore case when searching
opt.smartcase = true -- if you include mixed case in your search, assumes you want case-sensitive

opt.cursorline = true

-- turn on termguicolors for colour schemes to show up proper
-- (have to use iterm2 or any other true color terminal!)
opt.termguicolors = true
opt.background = "dark" -- colorschemes that can be light or dark will be made dark
opt.signcolumn = "yes" -- show sign column so text doesn't shift

-- backspace
opt.backspace = "indent,eol,start" -- allow backspace on indent, end of line or insert mode start position

-- clipboard to allow paste to anywhere on computer
opt.clipboard:append("unnamedplus") -- use system clipboard as default register

-- split windows
opt.splitright = true -- split vertical window to the right
opt.splitbelow = true -- split horizontal video to the bottom


