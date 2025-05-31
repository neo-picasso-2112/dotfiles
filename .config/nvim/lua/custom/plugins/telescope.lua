return {
  'nvim-telescope/telescope.nvim',
  dependencies = { 'nvim-lua/plenary.nvim' },
  config = function()
    require('telescope').setup {}
    local map = vim.keymap.set
    local opts = { noremap = true, silent = true }

    map('n', '<C-f>', '<cmd>Telescope find_files<CR>', vim.tbl_extend('force', opts, { desc = 'Telescope: File Files' }))
    map('n', '<C-g>', '<cmd>Telescope live_grep<CR>', vim.tbl_extend('force', opts, { desc = 'Telescope: Grep Files' }))
  end,
}
