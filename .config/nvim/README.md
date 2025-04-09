# 💤 LazyVim

A starter template for [LazyVim](https://github.com/LazyVim/LazyVim).
Refer to the [documentation](https://lazyvim.github.io/installation) to get started.

## TL;DR

An initial configuration in you `.config/nvim/lua` folder
  - A config folder with:
    - A `lazy.lua` file that boostraps LazyVim
    - A `keymaps.lua` file where you can add you custom key mappings
    - An `autocmd.lua` file where you can add your custom auto commands
    - An `options.lua` file where you can setup your custom neovim options
  - A plugins folder where you can add new plugins or configure the built-in ones. Any file that you add under this directory will be loaded when you open Neovim. A suggestion is to create a file per plugin you want to add and configure. The folder starts with a single file example.lua which contains a number of example configurations you can use.

A bare `.config/local/init.lua` file that loads the config folder

A number of plugins that get installed in you neovim data directory (referred in neovim’s documentation as `$XDG_DATA_HOME`) which on unix systems is under `~/local/shared/nvim`.
