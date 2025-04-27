# Map of Contents Topic

This guide will cover what MOCs are, how they relate to tags and links, where to store them, how to structure them, and how to build and maintain them effectively.

---

## Guide: Connecting Your Knowledge with Maps of Content (MOCs)

### The Goal: Beyond Isolated Notes

Your `scribe` tool helps create well-structured notes (Tutorials, How-Tos, Explanations, References). However, the true power of a knowledge base emerges when these individual notes are connected, allowing you to see the bigger picture, discover related concepts, and synthesize new insights. While tags help categorize and filter, they don't explicitly show the relationships *between* ideas. Direct linking (`[[Note Title]]` or Markdown links) creates the granular connections, but navigating this web can become difficult without higher-level signposts.

This is where **Maps of Content (MOCs)** come in.

### What is a Map of Content (MOC)?

Think of an MOC as a **curated index note** or a **hub note**. Its primary purpose is **not** to contain detailed knowledge itself, but rather to **gather, structure, and provide context for links to *other* notes** related to a specific topic, project, or area of interest.

It's like a table of contents, an index, or a mind map created *within* your note system, using links as the building blocks.

### MOCs vs. Tags vs. Folders vs. Direct Links

*   **Tags (`#python`, `#api`):** Good for broad categorization and filtering. Tells you *what* a note is about. Doesn't show relationships *between* notes with the same tag.
*   **Folders (`docs/python/`):** Provide rigid, hierarchical organization. A note can only live in one folder. Doesn't easily represent notes relevant to multiple topics. We're minimizing folders in your system.
*   **Direct Links (`[[Some Note]]`):** The micro-connections *between* individual ideas. Essential for the Zettelkasten-like web of thought. Shows a direct relationship.
*   **MOCs:** Provide **meso-level structure**. They curate direct links, grouping related notes (regardless of folder location) and adding context/narrative around those links. They help navigate the web created by direct links and tags.

**Answering your question:** Do you organize links by tag? **Not directly.** You use tags (and search) to *find* relevant notes, but you then *manually curate* links to those notes within an MOC based on their **conceptual relationship** to the MOC's topic, not just because they share a tag. An MOC provides *structure* that tags alone cannot.

### Where to Store MOCs?

Keep it simple and discoverable:

1.  **Within Your Knowledge Base:** MOCs are just notes, so they live alongside your other notes.
2.  **Option A (Simple Tagging):** Store them directly in `~/repos/second_brain/knowledge_base/explanation/` or `~/repos/second_brain/knowledge_base/` itself, and rely on a specific tag.
    *   **Tag:** Consistently use a tag like `#Type/MOC` or `#Index`.
    *   **Findability:** Use `scribe find --tag Type/MOC` or `grep '#Type/MOC'` to find all MOCs.
3.  **Option B (Dedicated Folder - Use Sparingly):** If you prefer, create a dedicated folder: `~/repos/second_brain/knowledge_base/moc/`.
    *   **Benefit:** Easy to browse MOCs via the file system.
    *   **Downside:** Adds a bit more folder structure. Still tag them (`#Type/MOC`) for consistency.

**Recommendation:** Start with **Option A (Simple Tagging)**. It aligns best with the goal of minimizing folder reliance. You can always create the `moc/` folder later if tagging alone feels insufficient.

### How to Structure an MOC

An MOC is just a Markdown note. Its value comes from the curated links and structure *you* impose. Here's a flexible template:

```markdown
---
title: "[Topic Name] MOC" # e.g., "Python Async Programming MOC"
date_created: {{DATE}}
last_updated: {{DATE}}
tags: [Type/MOC, Topic/TopicName] # e.g., Topic/Python, Topic/Async
status: evergreen # MOCs are usually actively maintained
related_notes:
  - maybe_parent_moc.md # If it's part of a larger topic
---

# {{title}}

*Last Updated: {{DATE}}*

**Scope:** [Briefly describe what this MOC covers. What kind of notes does it link to? What's its purpose? e.g., "This MOC gathers key concepts, tutorials, and reference points for understanding and using asynchronous programming in Python."]

---

## Core Concepts & Explanations

*   [[Explanation - What is Async IO]] - The fundamental idea.
*   [[Explanation - Coroutines vs Threads]] - Key differentiator.
*   [[Explanation - Event Loop Fundamentals]] - How it works under the hood.
*   *See also:* [[Python Concurrency MOC]] for broader context.

## Getting Started & Tutorials

*   [[Tutorial - Basic Asyncio Usage]] - First steps.
*   [[Tutorial - Async Await Syntax]] - How to write it.

## Practical Usage & How-Tos

*   [[How-To - Async HTTP Requests with aiohttp]]
*   [[How-To - Async File IO]]
*   [[How-To - Debugging Async Code]] - Common pitfalls.

## Key Libraries & Reference

*   **`asyncio` (stdlib):**
    *   [[Reference - asyncio Event Loop API]]
    *   [[Reference - asyncio Tasks and Futures]]
*   **`aiohttp`:**
    *   [[Reference - aiohttp ClientSession]]
*   **Other libs:** [[Reference - Anyio Library]], [[Reference - Trio Library]]

## Patterns & Best Practices

*   [[Explanation - Async Context Managers]]
*   [[Explanation - Handling Async Exceptions]]
*   [[Snippet - Basic Async Function Template]]

## Open Questions / Areas to Explore Further

*   How does framework X integrate with asyncio? [[Fleeting Note - Async Framework X Question]]
*   Performance implications of deep async calls?

## Related MOCs

*   [[Python Concurrency MOC]]
*   [[Web Development MOC]]

---
```

**Key Structural Elements:**

*   **Clear Title:** Identifies the topic.
*   **Scope:** Briefly explains the MOC's purpose.
*   **Sections:** Group links logically (Concepts, How-Tos, Reference, etc.). **This is where you add value!** The sections you choose depend on the topic.
*   **Links:** Use wiki-links `[[Note Title]]` or standard Markdown links `[Note Title](path/to/note.md)`. Consistent naming via `scribe edit-name` is helpful here.
*   **Annotations (Optional but Recommended):** Add a short comment after a link explaining *why* it's relevant or what its key takeaway is (like in the example: "The fundamental idea."). This adds context beyond the note's title.
*   **Related MOCs:** Link to higher-level or related MOCs to build a hierarchy.
*   **Open Questions/Fleeting Notes:** Make it a living document by linking questions or related raw ideas.

### How and When to Create/Update MOCs

MOCs should grow **organically**. Don't feel pressured to create them for everything immediately.

**Creation:**

1.  **Bottom-Up (Emergent):** You notice several notes clustering around a specific topic (e.g., you have multiple notes tagged `#api-design`). Create an "API Design MOC" and gather links to those existing notes. This is often the most natural way.
2.  **Top-Down (Intentional):** You decide to learn about a new, broad topic (e.g., "Kubernetes"). Create a "Kubernetes MOC" early on and add links to tutorials, concepts, and references as you create or find them. This acts as your learning dashboard.
3.  **Project-Based:** Create an MOC for a specific project (`Project X MOC`) linking to requirements, design decisions, relevant technical notes, meeting summaries, etc.

**Updating:**

MOCs are like **gardens, not filing cabinets**. Tend to them periodically, not necessarily daily.

*   **When Adding Notes:** When you create a significant new note (Explanation, Tutorial, etc.), think: "Which MOC(s) should this be linked from?" Go to that MOC and add the link in the relevant section.
*   **When Linking *To* an MOC:** When writing a regular note, if it relates to a broader topic covered by an MOC, link *to* the MOC (e.g., "For more on this, see the [[Python Async Programming MOC]]."). This makes the MOC discoverable.
*   **During Review:** When you revisit a topic or feel your understanding has evolved, review the corresponding MOC. Reorganize sections, add annotations, remove irrelevant links, or identify gaps where new notes are needed.
*   **Don't Over-Organize:** Resist the urge to constantly refactor MOCs. Let them evolve naturally. Perfection is not the goal; utility is.

### Finding and Using MOCs

*   **Search:** Use `scribe find` (or `grep`) for `#Type/MOC` or specific topic tags associated with the MOC.
*   **Direct Links:** Follow links *to* MOCs from your regular notes.
*   **Entry Points:** MOCs serve as excellent starting points when you want to explore or refresh your knowledge on a specific topic. Navigate *from* the MOC into the detailed notes.

### Advanced Usage

*   **Nested MOCs:** A high-level MOC (e.g., "Software Development MOC") can link to more specific MOCs ("Web Development MOC", "Database MOC", "Cloud Computing MOC").
*   **Linking MOCs:** Connect related MOCs directly (e.g., link from "Python Async Programming MOC" to "Networking MOC").
*   **MOCs as Thinking Tools:** Use an MOC to structure your thoughts while working on a complex problem or project. Add links to notes, questions, and resources as you gather them.
*   **Temporal MOCs:** Create "Logs of Logs" – a weekly or monthly MOC linking to the Daily Logs from that period, perhaps highlighting key events or achievements.

### Integration with `scribe`

*   **`scribe new`:** Could have a specific template for creating MOC notes, pre-filled with the structure.
*   **`scribe link` (Proposed Feature):** This would be invaluable for maintaining MOCs. You could run `scribe link`, choose your MOC file as the *source note*, and then use `fzf` to find the *target note* you want to add, automatically inserting the link into the MOC file.

### Conclusion

Maps of Content are a powerful technique to add structure and navigability to your linked notes. They bridge the gap between individual ideas and broad topics. By creating MOCs organically, structuring them thoughtfully with curated links and annotations, and using them as entry points for exploration, you significantly enhance the value and usability of your `scribe`-managed knowledge base, making it a true "second brain."
