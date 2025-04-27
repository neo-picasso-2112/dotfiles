# Roadmap

Here are 4 potential high-impact feature areas, keeping the target developer audience (Python, Terraform, Bash) and the tool's philosophy in mind:

1. Feature Area: Seamless Capture & Processing Workflow

Problem: Fleeting ideas or clipboard content need a frictionless way into the system and a clear path to refinement.

High-Impact Feature: scribe capture command & scribe process command.

scribe capture "Quick thought about XYZ" or pbpaste | scribe capture:

Functionality: Instantly creates a new note in the fleeting/ directory.

Details: Takes text directly from the command line argument or standard input (stdin). Uses a timestamp + optional keyword/first few words for the filename. Automatically assigns a #Status/Inbox or #Type/FleetingNote tag in the frontmatter. No prompts, just instant capture. Optionally opens the new note in $EDITOR if a flag like -e or --edit is passed, otherwise just confirms creation.

UI/UX: Maximum speed, minimum friction. Designed to be bound to a global keyboard shortcut or shell alias. Confirmation message uses rich for clarity ([green]Success:[/green] Created fleeting note: ...).

scribe process:

Functionality: Helps process notes marked for review (e.g., those in fleeting/ or tagged #Status/Inbox).

Details: Scans the relevant directory/tags. Opens an fzf window listing these notes, sorted by oldest first (or newest). Uses fzf's preview window (glow/cat) to show content. Selecting a note in fzf opens it directly in $EDITOR. Optionally, after closing the editor, it could prompt "Mark as processed? (y/N/d)" where 'y' removes the #Status/Inbox tag (or moves the file), 'N' does nothing, 'd' deletes the file.

UI/UX: Streamlines the Zettelkasten-like processing step. fzf provides efficient browsing and preview. The post-edit prompt helps manage the workflow state.

Why it's impactful: Directly addresses the capture friction and the crucial refinement step needed to turn raw notes into usable knowledge. Integrates well with a CLI workflow.

2. Feature Area: Powerful Note Retrieval & Exploration

Problem: Finding the right note quickly as the knowledge base grows is essential. Directory structure and basic grep have limits.

High-Impact Feature: scribe find (or scribe search) command.

Functionality: A unified interface for finding notes by filename, title (from frontmatter), tags, and content.

Details:

Opens an fzf interface.

By default, it lists all notes (maybe excluding fleeting/ unless specified), perhaps formatted like path/relative/filename.md | Title from Frontmatter | #tag1 #tag2.

fzf naturally searches across this combined line.

Uses fzf's preview window (glow/cat) showing the note content.

Content Search Integration: Add a keybinding within fzf (e.g., Ctrl-F) that switches the fzf input source to use rg (ripgrep) to search inside the note contents across the knowledge base. The results would show filename + matching line + context. Selecting a result opens the file in $EDITOR, ideally jumping to the matching line (requires editor integration or specific open command).

Tag Filtering: Potentially add flags like scribe find --tag python --tag api to pre-filter the list sent to fzf.

UI/UX: Leverages the power and familiarity of fzf and ripgrep. Provides instant preview. Combines multiple search methods (filename, title, content, tags) into one interface. The Ctrl-F toggle for content search within fzf is a common and effective pattern.

Why it's impactful: Transforms note retrieval from manual searching or basic grep into a fast, interactive, context-rich experience, crucial for leveraging the knowledge base.

3. Feature Area: Connecting Ideas (Low-Friction Linking)

Problem: While initially avoided, linking is the core of a connected knowledge base and essential for RAG. Manually finding and typing links is tedious.

High-Impact Feature: scribe link command.

Functionality: Interactively create a Markdown link between two notes.

Details:

scribe link: First, prompts the user to select the source note (the note where the link will be inserted) using the fzf-based interface developed for scribe find.

After selecting the source note, it immediately opens fzf again, prompting the user to select the target note (the note being linked to).

Once the target note is selected, scribe automatically:

Determines a suitable link text (e.g., the target note's title from frontmatter, or its filename).

Determines the link destination (e.g., the relative path from the source to the target, or just the target filename/title if using wiki-style links [[Target Title]]).

Parses the source note file.

Inserts the Markdown link (e.g., [Link Text](relative/path/target.md) or [[Target Title]]) at the current cursor position (ideal, but hard for a CLI tool) or, more practically, at the end of the source note file.

Saves the source note file.

Optionally confirms [green]Success:[/green] Linked [Target Title] in [Source File].

UI/UX: Uses the fast fzf interface twice. Automates the tedious parts of finding paths/titles and inserting the Markdown syntax. Inserting at the end is a pragmatic choice for a CLI tool, allowing the user to easily cut/paste it later in their editor if needed. Wiki-links ([[...]]) might be simpler to insert if path calculation is too complex.

Why it's impactful: Drastically lowers the barrier to creating connections between notes, transforming the collection into a true graph of knowledge. This is vital for discoverability and future RAG applications.

4. Feature Area: Knowledge Base Overview & Maintenance

Problem: Understanding the overall structure, finding disconnected parts, or managing metadata can become difficult.

High-Impact Feature: scribe stats (or scribe info) and enhanced tag management.

Functionality: Provides overview statistics and helps manage tags.

Details:

scribe stats:

Prints a summary using rich tables/panels: Total notes, notes per type (directory), number of tags, maybe notes without tags, notes older than X days without modification.

Could potentially list "Orphan" notes (notes with no incoming links - requires parsing links, more advanced).

scribe list-tags: Lists all unique tags found across all notes (parsing frontmatter) with counts of how many notes use each tag.

scribe rename-tag <old_tag> <new_tag>: Finds all notes with old_tag and replaces it with new_tag in their frontmatter. Requires confirmation.

scribe remove-tag <tag_name>: Removes a specific tag from all notes that use it. Requires confirmation.

UI/UX: Uses rich for clear, readable output of statistics. Tag management commands provide essential maintenance capabilities with confirmation prompts for safety.

Why it's impactful: Gives the user insight into their knowledge base's health and structure. Provides tools to keep metadata (tags) consistent and useful over time, which is crucial for organization and retrieval.

These four areas focus on improving the speed and effectiveness of capturing, finding, connecting, and managing notes within the established scribe framework, leveraging familiar and powerful CLI tools for a good UX. They build directly upon the core value proposition of the tool.
