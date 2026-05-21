# Compact System — How to use

> **Goal:** never lose context between sessions. Every `/compact` produces a durable MD snapshot that any future Claude can resume from cleanly.

---

## The two prompts

### 1. **PRE-COMPACT-PROMPT.md** — paste this BEFORE running `/compact`

Tells Claude to:
- Update `MEMORY.md` with anything new learned this session
- Update `STATE.md` with what shipped / what's in progress
- Create a snapshot at `compact/SNAPSHOT-<YYYY-MM-DD-HHMM>.md`
- Git status check + uncommitted-work warning
- Confirm "snapshot saved" before you `/compact`

### 2. **POST-COMPACT-PROMPT.md** — paste this AFTER `/compact`

Tells the new Claude to:
- Find the latest `compact/SNAPSHOT-*.md`
- Read it + MEMORY.md + STATE.md + CLAUDE.md
- Ack with a 3-bullet "where we are / what's next / blockers" summary
- Wait for Dhruv's go-ahead before doing anything

---

## Folder structure

```
compact/
├── README.md                              ← you are here
├── PRE-COMPACT-PROMPT.md                  ← copy-paste from this before /compact
├── POST-COMPACT-PROMPT.md                 ← copy-paste from this after /compact
├── SNAPSHOT-2026-05-22-1500.md            ← first snapshot (V3 lock)
├── SNAPSHOT-2026-05-23-XXXX.md            ← next session
└── ...                                    ← every compact adds one
```

**Cumulative archive** — never delete old snapshots. They become the history of how the product evolved.

---

## Flow (every session boundary)

```
1. [You're working in current session, context fills up]
2. [Paste PRE-COMPACT-PROMPT.md]
3. Claude writes SNAPSHOT-<timestamp>.md + updates MEMORY.md + STATE.md
4. Claude confirms "snapshot saved at <path>"
5. [You run /compact]
6. [Compaction happens — Claude's context resets to compact summary]
7. [Paste POST-COMPACT-PROMPT.md]
8. Claude reads latest snapshot + memory + state + acks with 3-bullet summary
9. [Continue working]
```

---

## Rules for snapshots

1. **One snapshot per session boundary.** Don't overwrite an existing one — append a new file.
2. **Filename = ISO timestamp** for natural sort order. Latest = last alphabetically.
3. **Every snapshot is self-contained.** A future Claude reading ONLY that snapshot + the V3 doc set should be able to resume.
4. **Snapshots reference, don't duplicate.** Don't restate the architecture — point at ARCHITECTURE-V3.md.
5. **Never delete snapshots.** Cumulative history.

---

## What if I forget to pre-compact?

If `/compact` runs without a pre-compact prompt, paste the post-compact prompt anyway — Claude reads MEMORY.md + STATE.md and reconstructs as best it can. The snapshot is a safety net, not a hard requirement. But always pre-compact when you've done meaningful work.

---

## Quick links

- [PRE-COMPACT-PROMPT.md](./PRE-COMPACT-PROMPT.md)
- [POST-COMPACT-PROMPT.md](./POST-COMPACT-PROMPT.md)
- Latest snapshot: see `ls -t compact/SNAPSHOT-*.md | head -1`
