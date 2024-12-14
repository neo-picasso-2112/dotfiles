return {
  "folke/tokyonight.nvim",
  priority = 1000,
  config = function()
    -- local bg, bg_dark, bg_highlight, bg_search, bg_visual, fg, fg_dark, fg_gutter, border
    require("tokyonight").setup({
      style = "night", -- check repo for many styles 
    })

    vim.cmd("colorscheme tokyonight")
  end
}
