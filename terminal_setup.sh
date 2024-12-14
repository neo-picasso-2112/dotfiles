#!/bin/bash

# Function to check if a command exists
command_exists() {
  command -v "$1" &>/dev/null
}

echo "Starting setup..."

# Install Homebrew if not already installed
if ! command_exists brew; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  echo "Homebrew is already installed."
fi

# Add Homebrew to PATH (macOS-specific)
if [[ "$OSTYPE" == "darwin"* ]]; then
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >>~/.zprofile
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

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

# Install Nerd Fonts
echo "Installing Nerd Fonts..."
brew tap homebrew/cask-fonts
brew install font-meslo-lg-nerd-font
# brew install --cask font-hack-nerd-font
brew install $(cat brew-packages.txt)


echo "Setup complete!"

