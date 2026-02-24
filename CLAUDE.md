# Job Application Agent — CLAUDE.md

You are building an autonomous job application agent that runs using Claude Code on a Max subscription. Follow these instructions step by step.

## Project Goal

Build a fully autonomous system that:

1. Searches job boards for matching roles
1. Scores and ranks jobs against my profile
1. Tailors my resume and generates cover letters per job
1. Fills out and submits applications via browser automation
1. Logs everything to a tracker

## Step 1: Project Setup

```
mkdir -p ~/job-hunter/.claude/agents
cd ~/job-hunter
git init
npm init -y
npm install playwright @playwright/mcp
npx playwright install chromium
pip install beautifulsoup4 requests --break-system-packages
```

Create this folder structure:

```
~/job-hunter/
├── CLAUDE.md              (this file)
├── .claude/
│   ├── settings.json      (MCP config)
│   └── agents/
│       └── job-applier.md (custom agent definition)
├── profile/
│   ├── resume.md          (my full resume in markdown)
│   ├── resume.pdf         (my current PDF resume)
│   ├── preferences.md     (job search preferences)
│   └── cover-letter-template.md
├── output/
│   ├── tailored-resumes/  (generated per job)
│   ├── cover-letters/     (generated per job)
│   └── screenshots/       (proof of submission)
├── data/
│   └── applications.json  (application tracker)
├── scripts/
│   ├── search.py          (job board scraper)
│   ├── score.py           (job matching scorer)
│   ├── tailor.py          (resume tailor)
│   ├── apply.py           (browser automation apply)
│   └── run.sh             (orchestrator script)
└── logs/
    └── agent.log
```

## Step 2: MCP Configuration

See `.claude/settings.json` for Playwright MCP server configuration.

## Step 3: Custom Agent Definition

See `.claude/agents/job-applier.md` for the autonomous agent workflow.

## Step 4: Profile Files

Before running, fill in your actual details:

1. `profile/preferences.md` — Replace all `[FILL IN]` placeholders with your actual details
2. `profile/resume.md` — Replace the entire template with your actual resume in markdown
3. `profile/resume.pdf` — Add your current PDF resume
4. `profile/cover-letter-template.md` — Customize the template structure

## Step 5: Scripts

- `scripts/search.py` — Scrapes Indeed NL, ICTerGezocht, Werkenbij; generates URLs for LinkedIn/Glassdoor/StepStone (Playwright MCP needed)
- `scripts/score.py` — Scores jobs 1-10 using keyword matching against your profile; filters to 7+ by default
- `scripts/tailor.py` — Generates tailored resumes and cover letters via `claude -p` CLI
- `scripts/apply.py` — Automates form filling via Playwright browser automation
- `scripts/run.sh` — Orchestrates the full pipeline (or individual phases)

## Step 6: Running Modes

### Interactive (watch it work)

```bash
cd ~/job-hunter
claude
# Then say: "Run the full job application pipeline. Search, score, tailor, and apply."
```

### Headless one-shot

```bash
cd ~/job-hunter
claude -p "Run the full job hunt cycle: search for .NET developer roles in Eindhoven, score them, tailor my resume for the top 5, and apply to them. Log everything."
```

### Background with subagent

From within Claude Code, press Ctrl+B to send a running task to background while you keep working.

### Scheduled (cron)

```bash
# Add to crontab: run every weekday at 9 AM
0 9 * * 1-5 cd ~/job-hunter && claude -p "Run daily job search and apply cycle. Search all configured boards, apply to top 5 new matches." >> ~/job-hunter/logs/agent.log 2>&1
```

### Continuous loop with tmux

```bash
tmux new -s jobhunter
cd ~/job-hunter
while true; do
  claude -p "Run one job hunt cycle. Search, score, tailor, apply to top 5 new jobs."
  echo "Sleeping 4 hours..."
  sleep 14400
done
```

### Run individual phases

```bash
bash scripts/run.sh search   # Search only
bash scripts/run.sh score    # Score only
bash scripts/run.sh tailor   # Tailor only
bash scripts/run.sh apply    # Apply only
bash scripts/run.sh          # All phases
```

## Step 7: Application Tracker

`data/applications.json` tracks all applications with fields:
- id, company, role, url, date_applied, score, status, resume_file, cover_letter_file, screenshot, notes, response

## Important Notes

- This project uses Claude Max subscription via Claude Code — no API keys needed
- All browser automation goes through the Playwright MCP server
- Never store passwords in plain text — use environment variables or a .env file
- For LinkedIn: log in manually first, save cookies, then reuse the session
- Test each phase independently before running the full pipeline
- Start with 2-3 applications to verify everything works before scaling up
- Run `npx playwright install chromium` before first use to download browser binaries
