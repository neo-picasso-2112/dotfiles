## `scribe` Enhancement User Stories & Analysis

Here's a collection of user stories based on your ideas, marked as `#todo` for tracking, followed by analysis for each:

**User Stories:**

1.  `#todo` **As a scribe user, I want to add tags to existing notes using a fuzzy finder sorted by recent edits so that I can categorize and retrieve my notes more easily.** (Covers Feature 1)
2.  `#todo` **As a scribe user, I want to rename a note file and automatically update its internal title metadata so that the filename and title stay consistent.** (Covers Feature 2)
3.  `#todo` **As a scribe user, I want to browse available note templates with a live preview of their content so that I can easily choose the right template structure.** (Covers Feature 3)
4.  `#todo` **As a scribe user browsing templates, I want to select a template from the previewer and immediately open it for editing in Neovim so that I can modify the base template structure.** (Covers Feature 6)
5.  `#todo` **As a scribe user, I want enhanced help messages and intelligent suggestions for mistyped commands so that the tool is easier to learn and use.** (Covers Feature 4)
6.  `#todo` **As a Neovim user working on my second brain, I want a way to see a live rendered preview of my Markdown notes side-by-side with the source so that I can visualize the final output while writing.** (Covers Feature 5)
7.  `#todo` **As a scribe user, I want the tool to consistently open files in Neovim (`nvim`) instead of potentially defaulting to Vim (`vim`) so that I get my preferred editor experience.** (Covers Feature 7)

---

### Analysis & Implementation Details

**1. `scribe add-tags`**

*   **Goal:** Efficiently add existing or new tags to notes.
*   **Implementation Steps:**
    1.  **File Selection:**
        *   Scan the `knowledge_base` directory recursively for `.md` files.
        *   Get the last modified time for each file (`os.stat(path).st_mtime` or `pathlib.Path.stat().st_mtime`).
        *   Sort the file paths list in descending order by modification time.
        *   **Use `fzf`:** Pipe the sorted list of file paths into an `fzf` process (`subprocess.run` or a library like `pyfzf`). `fzf` provides excellent fuzzy finding out-of-the-box. Capture the selected file path(s) from `fzf`'s output.
    2.  **Tag Database:**
        *   **Storage:** A simple JSON file (e.g., `~/.config/scribe/tags.json` or within the dotfiles script dir) is likely sufficient to store the list of known tags. Load this list at the start of the command.
        *   **`Tag` Class:** Not strictly necessary initially. Store tags as simple strings. Only create a class if tags need more attributes later (e.g., color, description, hierarchy).
    3.  **Tag Selection UI:**
        *   **Library:** `inquirerpy` is excellent for this.
        *   **Existing Tags:** Use an `inquirerpy` `checkbox` prompt. Populate `choices` with tags loaded from the database. Its built-in fuzzy searching works well as you type.
        *   **New Tag:** After the checkbox, add an option like `[ Create New Tag ]`. If selected, use an `inquirerpy` `input` prompt to ask for the new tag name. Validate it (e.g., no spaces, maybe lowercase). Add the new tag to the selected list *and* save it back to the tag database file.
    4.  **File Modification:**
        *   **Parsing:** Use a library like `python-frontmatter` to parse the YAML frontmatter of the selected Markdown file.
        *   **Updating:** Get the existing `tags:` list (or create it if it doesn't exist). Add the newly selected tags (avoiding duplicates).
        *   **Writing:** Serialize the updated frontmatter and original content back to the file.
*   **UX Improvements:**
    *   **Colored Tags:** `inquirerpy` doesn't easily support coloring individual checkbox items differently. You *could* potentially use `rich` to print the list *before* the prompt for visual reference, but it complicates the interaction. I'd skip dynamic colors in the selection list initially for simplicity.
*   **Tradeoffs:** Adds file I/O for tag database, dependency on `python-frontmatter`, and likely requires `fzf` to be installed system-wide for the best file-finding experience.

**2. `scribe edit-name`**

*   **Goal:** Rename a note file and keep its internal `title:` frontmatter synchronized.
*   **Implementation Steps:**
    1.  **File Selection:** Same as `add-tags` (scan, sort by mtime, use `fzf` to select a single file).
    2.  **New Name Prompt:** Use `inquirerpy` `input` prompt to get the desired *base* name (without `.md`). Validate it (e.g., no invalid characters).
    3.  **Confirmation:** Use `inquirerpy` `confirm` prompt showing the old and new proposed filename.
    4.  **Rename File:** Use `os.rename` or `pathlib.Path.rename`. Handle potential errors (file not found, permissions).
    5.  **Update Frontmatter Title:**
        *   **Parse:** Use `python-frontmatter` to load the *renamed* file.
        *   **Generate Title:** Create a user-friendly title from the new base name (e.g., replace underscores/hyphens with spaces, title-case words).
        *   **Update:** Modify the `title:` key in the loaded frontmatter metadata. If the `title:` key doesn't exist, add it.
        *   **Write:** Save the modified content (metadata + original markdown) back to the file.
*   **`title: {{title}}` Placeholder Discussion:**
    *   **Problem:** As mentioned before, the `{{title}}` placeholder is processed *only once* during the *initial creation* of the note by `scribe new`. Once the file is created, the placeholder text is gone, replaced by the actual title. It **cannot** be used for automatic updates later.
    *   **Best Option:** The robust approach is to **parse the frontmatter and explicitly update the `title:` field** based on the new filename whenever `scribe edit-name` is run. This requires the `python-frontmatter` library but ensures consistency regardless of the file's history.
    *   **Recommendation:** **Do not rely on placeholders for updates.** Implement the frontmatter parsing/updating logic. Ensure all templates (except maybe `daily_log.md`, where the title is usually the date) *do* include a `title: {{title}}` line during creation so the field exists from the start.

**3. `scribe templates` (Preview)**

*   **Goal:** Allow users to browse templates and preview their structure/content before creating a note.
*   **Implementation Steps:**
    1.  **Template Discovery:** Reuse the `scan_templates` logic from `templates.py` to get the list of available template paths and names.
    2.  **Use `fzf` with Preview:** This is the ideal tool.
        *   Construct the input for `fzf`: A list of strings, perhaps formatted like `"Type / Template Name\tFullPath"` (using a tab allows `fzf` to potentially hide the full path while still using it later).
        *   Execute `fzf` using `subprocess.run`.
        *   Crucially, set the `fzf` `--preview` option. The preview command needs to take the selected line's relevant part (the full path) as input.
        *   **Preview Command:** This command should render the Markdown file. Good options:
            *   `glow {2}`: If the full path is the second field (index {2}) after the tab. Needs `glow` installed. Renders nicely in the terminal.
            *   `cat {2}`: Simple, shows raw Markdown content. Works anywhere.
            *   `mdcat {2}`: Another Markdown renderer. Needs `mdcat` installed.
        *   Example `fzf` call within Python (conceptual):
            ```python
            # input_lines = ["How-To / Standard Task\t/path/to/standard_task.md", ...]
            # input_str = "\n".join(input_lines)
            # preview_cmd = "glow {2}" # or cat {2}
            # fzf_cmd = ["fzf", "--preview", preview_cmd, "--preview-window=right:60%:wrap", "--with-nth=1"] # Show only name, use path for preview
            # result = subprocess.run(fzf_cmd, input=input_str, text=True, capture_output=True)
            # selected_line = result.stdout.strip()
            # selected_path = selected_line.split('\t')[1] # Extract path if needed later
            ```
*   **Tradeoffs:** Requires `fzf` installed on the system. Requires a Markdown previewer (`glow`, `mdcat`) for the best experience, otherwise falls back to `cat`.

**4. `scribe help` / Error Handling**

*   **Goal:** Improve built-in help and provide suggestions for incorrect commands.
*   **Implementation Steps:**
    1.  **Enhance Typer Help:**
        *   Add detailed `help="..."` arguments to `@app.command(...)` decorators in `main.py`.
        *   Add docstrings to the command functions – Typer often includes these in the help output.
        *   Structure commands logically using Typer subcommands if the tool grows significantly.
        *   `Typer` uses `Rich` by default, so the basic help output (`scribe --help`, `scribe new --help`) should already look quite good.
    2.  **Mistyped Command Suggestions:**
        *   **Logic:** In the main entry point (or where Typer handles unknown commands, if possible), if a command isn't recognized:
            *   Get a list of all valid command names registered with Typer.
            *   Use a string distance algorithm (like Levenshtein distance) to compare the mistyped command with all valid commands. Libraries: `python-Levenshtein`, `fuzzywuzzy`, `RapidFuzz`.
            *   Find the valid command(s) with the smallest distance (below a certain threshold).
            *   If a close match is found, print a suggestion using `rich`: `rprint(f"[bold red]Error:[/bold red] Unknown command '[mistyped_command]'. Did you mean '[suggestion]'?")`
        *   **Implementation:** This requires adding logic around how Typer processes commands or potentially catching exceptions raised for unknown commands.

**5. Live Markdown Preview (in Neovim)**

*   **Goal:** Side-by-side view of Markdown source and rendered HTML/terminal output within Neovim during editing.
*   **Analysis:**
    *   **Not `fzf`:** `fzf` is for selection, not live editing preview.
    *   **Not Core Vim/Nvim:** No built-in feature for this.
    *   **Plugin Options:**
        1.  **`markdown-preview.nvim`**: Very popular. Uses either Node.js or Python backend. Opens preview in your default web browser or can use `curl` to render in a floating terminal window. Gives high-fidelity HTML preview. Requires setup (backend choice, potentially Node installation).
        2.  **`glow.nvim`**: Integrates the `glow` CLI tool. Renders Markdown directly in a Neovim split/floating window using terminal formatting. Simpler setup (just need `glow` CLI installed), stays entirely within the terminal. Rendering might be less accurate for complex HTML/CSS than a browser.
        3.  **Other Smaller Plugins:** Might exist, but these two are the most common.
*   **Recommendation:**
    *   **`glow.nvim`:** Choose this if you prefer staying entirely within the terminal and want the simplest setup. The rendering is usually good enough for standard Markdown. Requires `glow` CLI.
    *   **`markdown-preview.nvim`:** Choose this if you want the most accurate HTML preview (in a browser) and don't mind the context switch or the potential Node.js dependency.
    *   For a terminal-focused developer using `scribe`, **`glow.nvim` often feels more natural and integrated.**
*   **Setup (Example for `glow.nvim`):**
    1.  Install `glow` CLI: `brew install glow` / `apt install glow` / etc.
    2.  Add plugin spec to a file in `lua/plugins/` (e.g., `markdown-tools.lua`):
        ```lua
        -- lua/plugins/markdown-tools.lua
        return {
          {
            "ellisonleao/glow.nvim",
            config = true, -- Runs default setup
            cmd = "Glow",  -- Lazy load on command
            -- Optional: Set custom width, border etc.
            -- opts = { width = 80, border = "shadow" }
          }
        }
        ```
    3.  Restart Nvim.
    4.  Open a Markdown file and run `:Glow` to open the preview in a vertical split. Run it again to close.

**6. `scribe templates` (Edit)**

*   **Goal:** Select a template from the `fzf` previewer and open it directly in Neovim.
*   **Implementation Steps:**
    1.  **Modify `scribe templates` Command (Feature 3):** Ensure the `fzf` subprocess call is configured so that when the user presses `Enter`, `fzf` prints the *selected line* (which contains the template path) to standard output and exits.
    2.  **Capture Output:** Capture the standard output from the `fzf` subprocess result in your Python script.
    3.  **Extract Path:** Parse the output line to get the full path to the selected template file.
    4.  **Open in Editor:** Call the existing `file_utils.open_in_editor(selected_path)` function.

**7. Neovim (`nvim`) vs Vim (`vim`) Invocation**

*   **Goal:** Ensure `scribe` prefers `nvim` when opening files.
*   **Location of Change:** `~/dotfiles/custom_scripts/python/scribe/scribe/file_utils.py`, within the `open_in_editor` function.
*   **Current Logic:** Checks `os.environ.get('EDITOR')` first. If unset, it tries a list of fallbacks (potentially including `vim` before `nvim`).
*   **Recommendation:**
    1.  **Best Practice (User Environment):** The *ideal* solution is for the *user* to set their default editor correctly in their shell environment: `export EDITOR=nvim` in `.bashrc`/`.zshrc`. `scribe` will then automatically respect this. Add this instruction to the `README.md`.
    2.  **Code Adjustment (Fallback Order):** If you want the script itself to be more opinionated when `$EDITOR` is *not* set, modify the fallback logic within `open_in_editor`. Change the list of potential editors to try `nvim` *before* `vim`:
        ```python
        # Inside open_in_editor function in file_utils.py
        editor = os.environ.get('EDITOR')
        if not editor:
            # Fallback logic if EDITOR is not set
            # *** PRIORITIZE NVIM ***
            for potential_editor in ['nvim', 'vim', 'nano', 'code', 'emacs']: # Try nvim first
                 # Use shutil.which() for a more robust check than os.system
                 import shutil
                 if shutil.which(potential_editor):
                      editor = potential_editor
                      break
        # ... rest of the function using the determined 'editor' ...
        ```
        This makes the script prefer `nvim` as a fallback but still respects the user's `$EDITOR` if it's set.
