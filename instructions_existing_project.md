# Adding Gald3r to an Existing Project

These instructions are for developers who want to add gald3r to a project
that **already exists**.

For starting a **brand-new project**, see [instructions_new_project.md](./instructions_new_project.md).

---

## Step 1 - Pick Your AI Coding Tool

See the tool/folder table in [instructions_new_project.md](./instructions_new_project.md#step-1--pick-your-ai-coding-tool).

---

## Step 2 - Download Just Your Platform Folder

You only need one folder - not the whole repo.

**Option A - GitHub Download (no git required):**
1. Browse to https://github.com/wrm3/gald3r/tree/main/<your-tool>/
2. Click **Code → Download ZIP** (downloads the full repo)
3. Unzip and find <your-tool>/ inside

**Option B - Sparse checkout (advanced):**
```bash
git clone --no-checkout --depth=1 https://github.com/wrm3/gald3r.git gald3r-temp
cd gald3r-temp
git sparse-checkout init --cone
git sparse-checkout set <your-tool>
git checkout
cp -r <your-tool>/ /path/to/your/existing/project/
cd .. && rm -rf gald3r-temp
```

---

## Step 3 - Copy Into Your Project Root

Copy the **contents** of <your-tool>/ into the root of your existing project.

> **Important:** Do not overwrite files that already exist with the same name unless
> you intend to. Gald3r config files (.cursor/rules/, .claude/skills/, etc.) are
> additive - they extend your setup, they do not replace your code.

---

## Step 4 - Open in Your IDE

Reload your AI coding tool. gald3r auto-loads from the config files.

---

## Step 5 - Verify

`
@g-status
`

---

*Full documentation: [README.md](./README.md) | [CHANGELOG.md](./CHANGELOG.md)*
