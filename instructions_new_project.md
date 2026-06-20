# Starting a New Project with Gald3r

These instructions are for developers beginning a **brand-new project** and want gald3r
set up from the start.

For adding gald3r to an **existing project**, see [instructions_existing_project.md](./instructions_existing_project.md).

---

## Step 1 - Pick Your AI Coding Tool

Find your tool in the list below and note the folder name:

| Tool | Folder | Tier |
|---|---|---|
| Cursor | cursor/ | Tier 1 |
| Claude Code | claude/ | Tier 1 |
| GitHub Copilot | copilot/ | Tier 1 |
| OpenCode | opencode/ | Tier 1 |
| Windsurf | windsurf/ | Tier 1 |
| Cline | cline/ | Tier 1 |
| Roo Code | roo/ | Tier 1 |
| Codex CLI | codex/ | Tier 1 |
| CodeBuddy (Tencent) | codebuddy/ | Tier 1 |
| Amp Code (Sourcegraph) | amp/ | Tier 1 |
| Continue | continue/ | Tier 1 |
| Kimi Code (Moonshot AI) | kimi/ | Tier 1 |
| TRAE (ByteDance) | trae/ | Tier 1 |
| Aider | aider/ | Tier 2 |
| Augment | augment/ | Tier 2 |
| Goose | goose/ | Tier 2 |
| Warp | warp/ | Tier 2 |
| OpenHands | openhands/ | Tier 2 |
| Kiro | kiro/ | Tier 2 |
| Kiro CLI | kiro-cli/ | Tier 2 |
| Junie | junie/ | Tier 2 |
| Replit | replit/ | Tier 2 |
| Gemini CLI | gemini/ | Tier 2 |
| Mistral | mistral/ | Tier 3 |
| Antigravity | antigravity/ | Tier 3 |
| OpenClaw | openclaw/ | Tier 3 |
| Qwen | qwen/ | Tier 3 |
| SubQ | subq/ | Tier 3 |
| Kilo Code | kilo-code/ | Tier 2 |
| Qoder (Alibaba) | qoder/ | Tier 2 |
| Deep Code (DeepSeek) | deepcode/ | Tier 3 |
| Hermes (Nous Research) | hermes/ | Tier 3 |
| AstrBot | astrbot/ | Tier 3 |
| Void Editor | void/ | Tier 3 |

---

## Step 2 - Get the Template

**Option A - Clone and copy:**
```bash
git clone https://github.com/wrm3/gald3r.git
cp -r gald3r/<your-tool>/ my-new-project/
cd my-new-project
```

**Option B - Download zip:**
1. Click **Code → Download ZIP** on GitHub
2. Unzip and copy just the <your-tool>/ folder to your new project location

---

## Step 3 - Open in Your IDE

Open the folder in your AI coding tool. gald3r will auto-load on first launch.

---

## Step 4 - Verify Setup

In your AI assistant, type:

`
@g-status
`

You should see a gald3r session context block. If not, check that your IDE
recognizes the rules/config files in the project root.

---

## Tier Definitions

| Tier | Meaning |
|---|---|
| **Tier 1 - Fully Supported** | Tested by gald3r maintainers on every release |
| **Tier 2 - Community Supported** | Tested by the community; contributions welcome |
| **Tier 3 - Experimental** | Scaffold available; may have structural gaps |

---

*Full documentation: [README.md](./README.md) | [CHANGELOG.md](./CHANGELOG.md)*

