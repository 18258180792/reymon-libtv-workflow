# Claude Code Workspace Instructions

@AGENTS.md

## Claude Code Skill Discovery & LibTV Execution Notes

- **Skills Location (Single Source of Truth)**:
  - `.agents/skills/reymon-ad-reverse-workflow/SKILL.md`
  - `.agents/skills/commercial-image-prompt-pro/SKILL.md`
  - `.agents/skills/cinematic-storyboard-director/SKILL.md`
- **Enable Native Claude Code Slash-Skill Discovery (Optional)**:
  - Project-local link/copy: `python3 scripts/setup.py --agent claude --scope project` (creates `.claude/skills/*`)
  - Global install: `python3 scripts/setup.py --agent claude --scope global` (installs to `~/.claude/skills/*`)
- **Environment & Asset Verification**:
  - Run `python3 scripts/setup.py --check` to verify all 3 skills, bundled `products/reymon-cat-litter/assets/`, and blueprint validation.
- **LibTV Connectivity**:
  - If a LibTV MCP server is connected in Claude Code, use MCP directly (`doctor` -> `create_project`/`target_project` -> `create_node` with `run=false`).
  - Otherwise use the `libtv` CLI fallback (`./setup.sh --install-deps` then `bash .agents/skills/reymon-ad-reverse-workflow/scripts/check_env_and_libtv.sh`), strictly without `--run`.
