---
allowed-tools: Write, Read
argument-hint: <content to capture>
description: Capture fleeting note to second-brain with auto-generated title
---

## Task

Capture this content as a fleeting note to my second-brain:

$ARGUMENTS

## Instructions

1. **Generate filename** (NO date prefix):
   - Extract 3-7 key concepts from the content
   - Format: `Key_Concepts_Title_Case.md`
   - Use underscores, no special characters (grep-friendly)
   - Example: `Databricks_Instance_Pools_Cluster_Startup.md`

2. **Extract metadata**:
   - `created`: Today's date (YYYY-MM-DD)
   - `Keywords`: 5-10 searchable terms as array
   - `Source`: Infer type (blog, reddit, documentation, conversation, article, tutorial)

3. **Create the file** at `~/second-brain/fleeting/<generated-filename>.md`:

```
---
created: YYYY-MM-DD
Source: <inferred source type>
Keywords: [keyword1, keyword2, keyword3, ...]
---

## Idea/Observation

<the captured content, lightly formatted for markdown readability>
```

4. **Output confirmation**:
   - Created: `<filename>`
   - Path: `~/second-brain/fleeting/<filename>`
   - Keywords: <list>

**Formatting**: Keep content mostly verbatim. Add code blocks or lists only where it clearly improves readability.
