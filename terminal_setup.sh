#!/bin/bash

# Function to check if a command exists
command_exists() {
  command -v "$1" &>/dev/null
}

echo "Starting setup ..."

# Install Homebrew if not already installed
if ! command_exists brew; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "Homebrew is already installed."
fi

# Install GNU stow
brew install stow

# Install iTerm2
if ! command_exists iterm2; then
  echo "Installing iTerm2..."
  brew install --cask iterm2
else
  echo "iTerm2 is already installed."
fi

# Install Neovim
if ! command_exists nvim; then
  echo "Installing Neovim..."
  brew install neovim
else
  echo "Neovim is already installed."
fi

# Install Oh-My-Zsh
if [-d "$HOME/.oh-my-zsh" ]; then
  echo "Oh My Zsh is already installed."
else
  echo "Oh My Zsh is not installed. Installing now ..."
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

# Install Nerd Fonts & PowerLevel10K theme
echo "Installing Nerd Fonts..."
brew tap homebrew/cask-fonts
echo "Install Powerlevel10k theme..."
brew install powerlevel10k
echo "source $(brew --prefix)/share/powerlevel10k/powerlevel10k.zsh-theme" >> ~/.zshrc

# Update OhMyZsh Theme
NEW_THEME="powerlevel10k/powerlevel10k"
# Check if ZSH Theme is already set
if grep -q '^ZSH_THEME=' ~/.zshrc; then
  # replace existing theme
  sed -i '' 's/^ZSH_THEME=.*/ZSH_THEME="'"$NEW_THEME"'"/' ~/.zshrc
else
  # if not found, add it to end.
  echo 'ZSH_THEME="'"$NEW_THEME"'"' >> ~/.zshrc
fi
echo "Updated ~/.zshrc to use Powerlevel10K. Restart your terminal or run 'source ~/.zshrc'."

brew install font-meslo-lg-nerd-font
# brew install --cask font-hack-nerd-font
echo "Installed font-meslo-lg-nerd font!"
brew install --cask font-fantasque-sans-mono
echo "Installed font-fantasque-sans-mono to be suitable with gruvbox theme!"
brew install $(cat brew-packages.txt)
echo "Installed brew-packages.txt!"
brew install fzf
[[ -f $HOME/.fzf.zsh ]] && source $HOME/.fzf.zsh
echo "Installed fzf!"
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
echo "Installed vim plug!"


