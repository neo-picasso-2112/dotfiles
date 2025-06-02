# My Dotfiles

Contains configurations for my system.

## Terminal Setup

These instructions are meant to be used on Mac. Instructions for terminal setup on windows TBA.

1. Install Homebrew
2. A transparent terminal such as iterm2.
3. Install neovim
4. Nerdfonts so that icons in neovim can show up properly.
5. Once nerdfonts has been installed, we need to open iterm2 preferences > Profile > Text: update the font.

As of 2025, we are using `gruvbox` which is a retro Vim theme with [font fantasque-sans](https://github.com/belluzj/fantasque-sans).
This is configured by installing `gruvbox` within the `.vimrc` file. Fonts and background can be edited in Iterm2 settings.

## MCP Servers for Claude Code

To enhance Claude Code with additional capabilities, you can install MCP (Model Context Protocol) servers:

```bash
claude mcp add context7 -s user -- npx -y @upstash/context7-mcp
```

This command installs the Context7 MCP server which provides additional context management features for Claude Code.

## Some notes

Your home directory needs to exactly match the folder structure on ~/dotfiles directory.

For example, if you have an alacritty config in your user directory like this:

~/.config/alacritty.txt

Then you will need to setup your dotfiles to match this structure:
~/dotfiles/.config/alacritty.txt.

________________________________


If you run `stow .` and you run into conflicts due to existing configs where stow is trying to create symbolic links. 

In this scenario, you can rename your existing directory. Or, do `stow --adopt .` which would move conflicting files into dotfiles directory
allowing to create symbolic links. Doing this however would overwrite the files in the dotfiles directory with the conflicted files.
 

## Pre-requisites

Ensure Git is installed on your machine to begin cloning this dotfiles repository.

### Git


### Stow

For mac users:
- brew install stow

### Fonts

My preference for fonts when working in nvim is Fantasque Mono, but Jetsbrain Mono font looks beautiful on the terminal configured (Iterm)

## Setup & Installation

1. Run following commands:

```bash
chmod u+x ~/dotfiles/terminal_setup.sh
./terminal_setup.sh
```

2. Install requirements: GNU Stow using any package manager i.e. Brew. GNU Stow is a symlink farm manager which takes distinct packages of software located in separate directories on file system, and makes them appear to be installed in the same place.

```bash
brew install stow
```

Once installed, navigate to your dotfiles directory (e.g. ~/dotfiles) and running `stow .`

3. We need to install `vim-plug` so that our `.vimrc` configuration works.

You may notice even when you run `stow .` to create symlinks for `.vim` directory into your home directory that when you open files in VIM,
there will still be errors. That is because you need to manually delete `.vim/autoload/plug.vim` and install it again in order for `vim-plug`
to be recognised as installed. You can check if `vim-plug` manager is installed by running `:scriptnames` in Vim mode to see if `vim-plug` 
manager is installed.

So how do you install `.vimrc` config?
- Run `stow .` in your dotfiles directory
- Remove .vim/autoload/plug.vim
- Run `curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim`
- In Vim mode, run `:PlugInstall`

This step will provide a basic editor to work with files in Vim.

