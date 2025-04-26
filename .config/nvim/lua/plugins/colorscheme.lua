return {
  -- Define the gruvbox theme plugin
  {
    "ellisonleao/gruvbox.nvim",
    lazy = false,    -- We want the theme loaded immediately on startup
    priority = 1000, -- Ensure it loads before other plugins that depend on highlighting
    config = function()
      -- Load the colorscheme here. Usually this is done in Vim VScode theme format
      -- vim.cmd([[colorscheme gruvbox]])

      -- Optional: Configure gruvbox settings if needed
      require('gruvbox').setup({
        terminal_colors = true, -- add neovim terminal colors
        undercurl = true,
        underline = true,
        bold = true,
        italic = {
          strings = true,
          emphasis = true,
          comments = true,
          operators = false,
          folds = true,
        },
        strikethrough = true,
        invert_selection = false,
        invert_signs = false,
        invert_tabline = false,
        invert_intend_guides = false,
        inverse = true, -- invert background for search, diffs, statuslines and errors
        contrast = "hard", -- Available values: 'hard', 'medium', 'soft'
        palette_overrides = {},
        overrides = {},
        dim_inactive = false,
        transparent_mode = false,
      })

      -- Set the colorscheme using the setup function's return or vim.cmd
      -- The setup function might implicitly set the colorscheme,
      -- or you might need vim.cmd depending on the plugin's design.
      -- Check gruvbox.nvim docs if the setup call alone doesn't apply it.
      vim.cmd.colorscheme "gruvbox" -- Make sure this line runs to apply the theme
    end,
  }
}
