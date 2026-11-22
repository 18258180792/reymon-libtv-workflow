#!/usr/bin/env python3
"""
Cross-agent bootstrap, skill linker, dependency installer, and health-check tool
for the reymon-libtv-workflow repository (V3.0 Dual-Mode).

Uses Python 3.9+ standard library only. Never runs paid generation nodes (--run).
"""

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_SRC_DIR = REPO_ROOT / ".agents" / "skills"

REQUIRED_RULES = [
    "AGENTS.md",
    "GEMINI.md",
    "CLAUDE.md",
    ".cursor/rules/reymon-workflow.mdc",
]

REQUIRED_SKILLS: Dict[str, List[str]] = {
    "reymon-ad-reverse-workflow": [
        "SKILL.md",
        "references/canvas_blueprint_schema.md",
        "references/delivery_markdown_standard.md",
        "references/reymon_cat_litter_playbook.md",
        "scripts/build_libtv_canvas.py",
        "scripts/check_env_and_libtv.sh",
        "scripts/fetch_reference_video.py",
    ],
    "commercial-image-prompt-pro": [
        "SKILL.md",
        "references/optical_lighting_material_lexicon.md",
    ],
    "cinematic-storyboard-director": [
        "SKILL.md",
        "references/camera_motion_and_beat_sheet.md",
    ],
}

REQUIRED_ASSETS = [
    "products/_sku_template/product_brief_template.md",
    "products/reymon-cat-litter/product_brief.md",
    "products/reymon-cat-litter/assets/packshots/pack_front.png",
    "products/reymon-cat-litter/assets/inner_granules/granules_macro.png",
    "products/reymon-cat-litter/assets/inner_granules/detail_5in1_formula.png",
    "products/reymon-cat-litter/assets/inner_granules/detail_granules_raw.png",
]

PLACEHOLDER_KEY = "在此填入你的_LIBTV_ACCESS_KEY"
SUPPORTED_AGENTS = ["antigravity", "claude", "cursor", "codex", "gemini", "opencode"]
LIBTV_INSTALL_URL = "https://liblibai-web-static.liblib.cloud/cli/1.1.1/install-libtv-cli.sh"


def parse_frontmatter(skill_md: Path) -> Tuple[Optional[str], Optional[str]]:
    """Verify minimal YAML frontmatter containing `name:` and `description:`."""
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if not m:
        return None, None
    block = m.group(1)
    name_m = re.search(r"^name:\s*(.+)$", block, flags=re.MULTILINE)
    desc_m = re.search(r"^description:\s*(.+)$", block, flags=re.MULTILINE)
    name_val = name_m.group(1).strip().strip("\"'") if name_m else None
    desc_val = desc_m.group(1).strip() if desc_m else None
    return name_val, desc_val


def find_libtv_bin() -> Optional[str]:
    env_bin = os.environ.get("LIBTV_BIN")
    if env_bin and os.access(env_bin, os.X_OK):
        return env_bin
    which_bin = shutil.which("libtv")
    if which_bin:
        return which_bin
    home_bin = Path.home() / ".libtv" / "libtv"
    if home_bin.exists() and os.access(str(home_bin), os.X_OK):
        return str(home_bin)
    return None


def inspect_env_file(env_path: Path) -> str:
    """Inspect .env without ever echoing or printing secret values."""
    if not env_path.exists():
        return "missing"
    content = env_path.read_text(encoding="utf-8", errors="ignore")
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == "LIBTV_ACCESS_KEY":
            val = v.strip().strip("\"'")
            if not val or val == PLACEHOLDER_KEY:
                return "placeholder"
            return "configured"
    return "missing_key"


def init_env() -> None:
    env_example = REPO_ROOT / ".env.example"
    env_file = REPO_ROOT / ".env"
    if env_file.exists():
        print("[OK] .env already exists (preserved, not overwritten).")
        return
    if not env_example.exists():
        print("[WARN] .env.example not found; skipping .env initialization.")
        return
    shutil.copy2(env_example, env_file)
    print(f"[OK] Created {env_file.relative_to(REPO_ROOT)} from .env.example (fill in LIBTV_ACCESS_KEY if using CLI).")


def resolve_agent_targets(agent: str, scope: str) -> Dict[str, Optional[Path]]:
    """Return mapping of agent -> target skills root directory (None means native .agents/skills/)."""
    home = Path.home()
    if scope == "project":
        mapping: Dict[str, Optional[Path]] = {
            "antigravity": None,
            "codex": None,
            "gemini": None,
            "opencode": None,
            "claude": REPO_ROOT / ".claude" / "skills",
            "cursor": REPO_ROOT / ".cursor" / "skills",
        }
    else:
        mapping = {
            "antigravity": home / ".gemini" / "antigravity" / "skills",
            "claude": home / ".claude" / "skills",
            "cursor": home / ".cursor" / "skills",
            "codex": home / ".codex" / "skills",
            "gemini": home / ".agents" / "skills",
            "opencode": home / ".agents" / "skills",
        }
    if agent == "all":
        return mapping
    return {agent: mapping[agent]}


def sync_skills(agent: str, scope: str, mode: str, force: bool) -> int:
    targets = resolve_agent_targets(agent, scope)
    seen_dirs: Dict[Path, List[str]] = {}
    for ag, tdir in targets.items():
        if tdir is None:
            print(f"[OK] {ag} ({scope}): discovers skills natively from .agents/skills/")
        else:
            seen_dirs.setdefault(tdir, []).append(ag)

    for target_root, agents in seen_dirs.items():
        target_root.mkdir(parents=True, exist_ok=True)
        ag_label = ", ".join(agents)
        for skill_name in REQUIRED_SKILLS:
            src = SKILLS_SRC_DIR / skill_name
            dst = target_root / skill_name
            if not src.exists():
                print(f"[FAIL] Missing source skill directory: {src}", file=sys.stderr)
                return 1

            if dst.is_symlink():
                if dst.resolve() == src.resolve():
                    print(f"[OK] {ag_label} ({scope}): {dst} already linked -> {skill_name}")
                    continue
                dst.unlink()
            elif dst.exists():
                if not force:
                    print(
                        f"[SKIP] {ag_label} ({scope}): {dst} already exists as a real directory. "
                        "Pass --force to replace."
                    )
                    continue
                shutil.rmtree(dst)

            effective_mode = mode
            if effective_mode == "symlink":
                link_target = (
                    os.path.relpath(src, dst.parent) if scope == "project" else str(src.resolve())
                )
                try:
                    os.symlink(link_target, dst, target_is_directory=True)
                    print(f"[OK] {ag_label} ({scope}): symlinked {dst} -> {link_target}")
                    continue
                except OSError as exc:
                    print(f"[WARN] Symlink failed ({exc}); falling back to copy for {dst}.")
                    effective_mode = "copy"

            if effective_mode == "copy":
                shutil.copytree(src, dst)
                print(f"[OK] {ag_label} ({scope}): copied {skill_name} -> {dst}")
    return 0


def install_deps() -> None:
    print("=== Installing optional CLI dependencies (libtv CLI, yt-dlp) ===")
    libtv_bin = find_libtv_bin()
    if libtv_bin:
        print(f"[OK] libtv CLI already installed: {libtv_bin}")
    else:
        curl_bin = shutil.which("curl")
        bash_bin = shutil.which("bash")
        if not curl_bin or not bash_bin:
            print(
                "[WARN] curl or bash not found; install libtv CLI manually:\n"
                f"  curl -fsSL {LIBTV_INSTALL_URL} | bash"
            )
        else:
            print("[INFO] Installing official libtv CLI...")
            cmd = f"curl -fsSL {LIBTV_INSTALL_URL} | bash"
            res = subprocess.run([bash_bin, "-lc", cmd], check=False)
            if res.returncode == 0:
                print("[OK] libtv CLI installation finished.")
            else:
                print(
                    "[WARN] libtv CLI installation failed (network/offline or permissions). "
                    "If your host agent uses LibTV MCP, CLI is not required.\n"
                    f"  Manual command: curl -fsSL {LIBTV_INSTALL_URL} | bash"
                )

    yt_dlp = shutil.which("yt-dlp")
    if yt_dlp:
        print(f"[OK] yt-dlp already installed: {yt_dlp}")
    else:
        installed = False
        brew_bin = shutil.which("brew")
        if platform.system() == "Darwin" and brew_bin:
            print("[INFO] Installing yt-dlp via Homebrew...")
            res = subprocess.run([brew_bin, "install", "yt-dlp"], check=False)
            installed = res.returncode == 0
        if not installed:
            print("[INFO] Trying pip install --user yt-dlp...")
            res = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--user", "yt-dlp"],
                check=False,
            )
            installed = res.returncode == 0
        if installed:
            print("[OK] yt-dlp installation finished.")
        else:
            print(
                "[WARN] yt-dlp could not be installed automatically (only needed for video URLs; "
                "local .mp4 files work natively without yt-dlp)."
            )


def run_check() -> int:
    print(f"=== Reymon LibTV Workflow Health Check ({REPO_ROOT}) ===")
    failures = 0

    # 1. Python version
    py_ver = sys.version_info
    if (py_ver.major, py_ver.minor) >= (3, 9):
        print(f"[OK] Python version: {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
    else:
        print(f"[FAIL] Python >= 3.9 required, found {py_ver.major}.{py_ver.minor}.{py_ver.micro}")
        failures += 1

    # 2. Cross-agent rule entry points
    for rel in REQUIRED_RULES:
        p = REPO_ROOT / rel
        if p.is_file() and p.stat().st_size > 0:
            print(f"[OK] Rule file present: {rel}")
        else:
            print(f"[FAIL] Missing or empty rule file: {rel}")
            failures += 1

    # 3. Skills & frontmatter
    for skill_name, req_files in REQUIRED_SKILLS.items():
        sdir = SKILLS_SRC_DIR / skill_name
        skill_md = sdir / "SKILL.md"
        if not skill_md.is_file():
            print(f"[FAIL] Missing skill SKILL.md: .agents/skills/{skill_name}/SKILL.md")
            failures += 1
            continue
        fm_name, fm_desc = parse_frontmatter(skill_md)
        if fm_name == skill_name and fm_desc:
            print(f"[OK] Skill frontmatter valid: {skill_name}")
        else:
            print(
                f"[FAIL] Invalid YAML frontmatter in {skill_md} "
                f"(expected name={skill_name!r}, got name={fm_name!r})"
            )
            failures += 1
        for sub in req_files:
            sub_p = sdir / sub
            if not sub_p.is_file() or sub_p.stat().st_size == 0:
                print(f"[FAIL] Missing skill asset: .agents/skills/{skill_name}/{sub}")
                failures += 1

    # 4. Bundled product assets
    for rel in REQUIRED_ASSETS:
        p = REPO_ROOT / rel
        if p.is_file() and p.stat().st_size > 0:
            size_kb = p.stat().st_size / 1024
            print(f"[OK] Product asset ready: {rel} ({size_kb:.1f} KB)")
        else:
            print(f"[FAIL] Missing or empty product asset: {rel}")
            failures += 1

    # 5. Non-destructive blueprint validation check
    builder = SKILLS_SRC_DIR / "reymon-ad-reverse-workflow" / "scripts" / "build_libtv_canvas.py"
    demo_bp = REPO_ROOT / "runs" / "demo_reymon_sample" / "canvas_blueprint.json"
    if builder.is_file() and demo_bp.is_file():
        res = subprocess.run(
            [
                sys.executable,
                str(builder),
                "--blueprint",
                str(demo_bp),
                "--workspace-root",
                str(REPO_ROOT),
                "--check-only",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if res.returncode == 0:
            first_line = res.stdout.strip().splitlines()[0] if res.stdout.strip() else "passed"
            print(f"[OK] Blueprint validator (--check-only): {first_line}")
        else:
            print(f"[FAIL] Blueprint validator failed (exit={res.returncode}):\n{res.stderr.strip()}")
            failures += 1
    else:
        print("[FAIL] Missing build_libtv_canvas.py or runs/demo_reymon_sample/canvas_blueprint.json")
        failures += 1

    # 6. .env status (never print secret values)
    env_status = inspect_env_file(REPO_ROOT / ".env")
    if env_status == "configured":
        print("[OK] .env present and LIBTV_ACCESS_KEY appears configured.")
    elif env_status == "placeholder":
        print(
            "[WARN/OPTIONAL] .env exists with placeholder LIBTV_ACCESS_KEY "
            "(only needed for libtv CLI if LibTV MCP is not connected)."
        )
    else:
        print(
            "[WARN/OPTIONAL] .env not initialized (run `python3 scripts/setup.py --init-env` "
            "if using libtv CLI with access key; not required when using LibTV MCP)."
        )

    # 7. libtv CLI status (optional if MCP is available)
    libtv_bin = find_libtv_bin()
    if libtv_bin:
        print(f"[OK] libtv CLI detected: {libtv_bin}")
    else:
        print(
            "[WARN/OPTIONAL] libtv CLI not found. Prefer LibTV MCP in your host agent, "
            "or run `./setup.sh --install-deps` to install the CLI fallback."
        )

    # 8. yt-dlp status (optional for URL fetching)
    yt_dlp = shutil.which("yt-dlp")
    if yt_dlp:
        print(f"[OK] yt-dlp detected: {yt_dlp}")
    else:
        print(
            "[WARN/OPTIONAL] yt-dlp not found (optional: only needed to download video URLs; "
            "local .mp4/.mov files work without it)."
        )

    print("")
    if failures == 0:
        print("[PASS] All required rules, skills, product assets, and blueprint checks passed.")
        return 0
    print(f"[FAIL] {failures} required check(s) failed.", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-agent bootstrap & diagnostics for reymon-libtv-workflow."
    )
    parser.add_argument(
        "--check",
        "--doctor",
        dest="check",
        action="store_true",
        help="Run read-only environment, skills, assets, and blueprint checks",
    )
    parser.add_argument(
        "--init-env",
        action="store_true",
        help="Copy .env.example to .env if .env does not already exist",
    )
    parser.add_argument(
        "--agent",
        choices=SUPPORTED_AGENTS + ["all"],
        help="Link or copy .agents/skills/ into target agent skill directory",
    )
    parser.add_argument(
        "--scope",
        choices=["project", "global"],
        default="project",
        help="Install skill links/copies at project scope (default) or user global scope",
    )
    parser.add_argument(
        "--mode",
        choices=["symlink", "copy"],
        default="symlink",
        help="Use symlink (default, auto-falls back to copy on failure) or copy",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing non-symlink target skill directories",
    )
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install optional CLI dependencies (libtv CLI and yt-dlp) if missing",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run --init-env, --install-deps, --agent all --scope project, and --check",
    )

    args = parser.parse_args()

    if not any([args.check, args.init_env, args.agent, args.install_deps, args.all]):
        parser.print_help()
        return 0

    if args.all:
        init_env()
        install_deps()
        rc = sync_skills("all", args.scope, args.mode, args.force)
        if rc != 0:
            return rc
        return run_check()

    if args.init_env:
        init_env()
    if args.install_deps:
        install_deps()
    if args.agent:
        rc = sync_skills(args.agent, args.scope, args.mode, args.force)
        if rc != 0:
            return rc
    if args.check:
        return run_check()
    return 0


if __name__ == "__main__":
    sys.exit(main())
