-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Sets core Neovim options (equivalent to Vim's set option=value).
-- Common Use: Setting number and relativenumber, configuring tabs vs. spaces (expandtab, shiftwidth, tabstop),
-- text wrapping (wrap), mouse support (mouse).

-- ~/.config/nvim/lua/config/options.lua
--
-- Sets Neovim options (equivalent to :set command).
-- See :help option-list for available options.

-- Access vim options api
local opt = vim.opt

-- ----------------------------------------------------------------------------
-- ## Basic Setup & File Handling ##
-- ----------------------------------------------------------------------------

-- Set utf-8 encoding
opt.encoding = 'utf-8'
opt.fileencoding = 'utf-8'

-- Enable true color support
opt.termguicolors = true

-- Enable mouse support in all modes
opt.mouse = 'a'

-- Sync with system clipboard
-- Requires 'xclip'/'xsel' (Linux X11), 'wl-copy' (Linux Wayland), 'pbcopy' (macOS), 'clip.exe' (Windows/WSL)
opt.clipboard = 'unnamedplus' -- Use system clipboard for copy/paste

-- Enable hidden buffers - ESSENTIAL for buffer switching
opt.hidden = true -- Allows switching buffers without saving

-- Reduce update time - Improves responsiveness for plugins like GitSigns
opt.updatetime = 250 -- Lower value (e.g., 250ms) is more responsive
opt.timeoutlen = 500 -- Time to wait for mapped sequence (shorter than default 1000ms)

-- Better editor UI behavior
opt.cmdheight = 1 -- Height of the command area
opt.showmode = false -- Don't show mode indicator (usually handled by statusline)
opt.pumheight = 10 -- Max number of items to show in popup menu

-- ----------------------------------------------------------------------------
-- ## Appearance & UI ##
-- ----------------------------------------------------------------------------

opt.guifont = { 'FantasqueSansM Nerd Font', ':h14' }

-- Line Numbers
opt.number = true -- Show line numbers
opt.relativenumber = true -- Show relative line numbers (useful for vertical motion)

-- Sign Column (for diagnostics, git signs, etc.)
opt.signcolumn = 'yes' -- Always show the sign column, prevents UI shifting

-- Text Wrapping
opt.wrap = false -- Do not wrap lines (personal preference, common for code)
opt.linebreak = true -- Wrap lines at convenient points if wrap is enabled

-- Cursor Appearance
opt.cursorline = true -- Highlight the current line
-- opt.cursorcolumn = true -- Highlight the current column (can be distracting)

-- Scrolling Behavior
opt.scrolloff = 8 -- Keep 8 lines visible above/below cursor when scrolling
opt.sidescrolloff = 8 -- Keep 8 columns visible left/right when scrolling horizontally

-- Indentation Guides (Requires a plugin like 'lukas-reineke/indent-blankline.nvim')
-- This option enables the built-in feature that plugins can use
opt.list = true
opt.listchars = { tab = '» ', trail = '·', nbsp = '␣' } -- Customize visual characters

-- ----------------------------------------------------------------------------
-- ## Indentation & Formatting ##
-- ----------------------------------------------------------------------------

-- Use spaces instead of tabs
opt.expandtab = true

-- Auto-indentation
opt.smartindent = true -- Be smart about indentation
opt.autoindent = true -- Always auto-indent new lines

-- Tab and shift widths
opt.tabstop = 2 -- Number of visual spaces per TAB
opt.softtabstop = 2 -- Number of spaces for TAB key press/backspace
opt.shiftwidth = 2 -- Number of spaces for indentation commands (>>, <<)

-- ----------------------------------------------------------------------------
-- ## Search & Completion ##
-- ----------------------------------------------------------------------------

-- Search Behavior
opt.ignorecase = true -- Ignore case when searching...
opt.smartcase = true -- ...unless the search pattern contains uppercase letters

opt.hlsearch = true -- Highlight search results
opt.incsearch = true -- Show matches incrementally as you type

-- Completion Options
opt.completeopt = 'menu,menuone,noselect' -- Configure completion menu behavior

-- Wild Menu/Command Completion
opt.wildmode = 'longest:full,full' -- Command-line completion mode
opt.wildmenu = true -- Enable visual wildmenu

-- ----------------------------------------------------------------------------
-- ## Editing Behavior ##
-- ----------------------------------------------------------------------------

-- Backspace Behavior
opt.backspace = 'indent,eol,start' -- Allow backspace over everything in Insert mode

-- Persistent Undo
opt.undofile = true -- Save undo history to file
-- You might need to configure opt.undodir if you don't want undo files
-- cluttering your project directories. LazyVim often sets this up for you
-- under ~/.local/state/nvim/undo/ or similar. Check :h undodir.

-- Swap/Backup Files (Often disabled with modern workflows/VCS)
opt.swapfile = false
opt.backup = false
opt.writebackup = false -- Critical setting for some plugins if backup is enabled

-- ----------------------------------------------------------------------------
-- ## Other Settings ##
-- ----------------------------------------------------------------------------

opt.sessionoptions = 'buffers,curdir,folds,help,tabpages,winsize' -- What to save in sessions
opt.splitbelow = true -- New horizontal splits go below current
opt.splitright = true -- New vertical splits go right of current

-- Make sure filetype detection and plugins are enabled
-- These are usually default in Neovim but explicit doesn't hurt
vim.cmd 'filetype plugin indent on'

print 'Base options set!' -- Optional confirmation message

