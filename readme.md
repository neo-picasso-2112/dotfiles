# My Dotfiles

Contains configurations for my system.

## Terminal Setup

These instructions are meant to be used on Mac. Instructions for terminal setup on windows TBA.

1. Install Homebrew
2. A transparent terminal such as iterm2.
3. Install neovim
4. Nerdfonts so that icons in neovim can show up properly.
5. Once nerdfonts has been installed, we need to open iterm2 preferences > Profile > Text: update the font.


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



## Setup & Installation

First install GNU Stow using any package manager i.e. Brew.

Once installed, navigate to your dotfiles directory (e.g. ~/dotfiles) and running `stow .`

