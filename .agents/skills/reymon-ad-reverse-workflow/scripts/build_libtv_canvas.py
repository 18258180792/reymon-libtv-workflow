#!/usr/bin/env python3
"""
Build and validate a V3 Dual-Mode LibTV Infinite Canvas blueprint (canvas_blueprint.json).

V3 HIGHLIGHTS:
  1. Supports Dual Production Modes:
     - `full_ai` (Mode A): Full-AI Unified pipeline (locks visuals + TTS voice/speed +
       1 Global BGM node, and enforces NO per-shot BGM in shot video prompts).
     - `hook_hybrid` (Mode B): Lightweight AI Hook (first 3-6s, single or A/B hooks) +
       Real-Shoot Handoff schedule (zero redundant back-half AI nodes).
  2. Default 480p Draft-Ready Video Preset:
     - Defaults to `Seedance 2.5 Flash` (`480p`) for low-cost card testing, and
       `Lib Image 2.6 Pro` for static frames.
  3. SAFETY INVARIANT:
     - NEVER passes `--run` to any `libtv` command. Zero auto-spend guaranteed.
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# V3 Infinite Canvas Column Coordinates
COL0_GUIDE_X = -700
COL1_ASSETS_X = 80
COL2_ANCHORS_X = 760
COL2B_AUDIO_X = 1380
COL3_KEYFRAMES_X = 2040
COL3B_TAIL_KEYFRAMES_X = 2520
COL4_VIDEOS_X = 3040

START_Y = 120
ASSET_STEP_Y = 360
ANCHOR_STEP_Y = 400
AUDIO_STEP_Y = 300
SHOT_STEP_Y = 480

SLOT_INDEX_RE = re.compile(r"\{\{(?:Image|Mixed)\s+(\d+)\}\}")
NODE_REF_RE = re.compile(r"\{\{Node\s+([^}]+)\}\}")
CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]")


def find_libtv_bin() -> str:
    env_bin = os.environ.get("LIBTV_BIN")
    if env_bin and os.access(env_bin, os.X_OK):
        return env_bin
    which_bin = shutil.which("libtv")
    if which_bin:
        return which_bin
    home_bin = Path.home() / ".libtv" / "libtv"
    if home_bin.exists() and os.access(str(home_bin), os.X_OK):
        return str(home_bin)
    return "libtv"


def assert_no_auto_run(cmd: List[str]) -> None:
    """Hard safety lock: block any accidental `--run` execution."""
    for token in cmd:
        if token == "--run" or token.startswith("--run="):
            raise RuntimeError(
                f"[SAFETY_LOCK] 检测到禁止参数 '{token}'！本工作流严禁自动运行生图/生音/生视频节点。"
            )


def validate_slot_placeholders(node_name: str, prompt: str, left_inputs: List[str]) -> List[str]:
    """Verify {{Image/Mixed 1..N}} or {{Node <id>}} placeholders match `left_inputs`."""
    warnings: List[str] = []
    node_refs = [m.group(1).strip() for m in NODE_REF_RE.finditer(prompt)]
    found_nums = sorted({int(m.group(1)) for m in SLOT_INDEX_RE.finditer(prompt)})

    if not left_inputs and (found_nums or node_refs):
        raise ValueError(
            f"节点 [{node_name}] 未配置 left_inputs 连线，但提示词中出现了槽位引用: {found_nums or node_refs}"
        )

    if left_inputs:
        if node_refs:
            missing = [u for u in left_inputs if u not in node_refs]
            if missing:
                warnings.append(
                    f"节点 [{node_name}] 使用了 {{{{Node ...}}}} 语法，但以下上游未在提示词中显式点名: {missing}"
                )
        else:
            expected_nums = list(range(1, len(left_inputs) + 1))
            if found_nums != expected_nums:
                raise ValueError(
                    f"节点 [{node_name}] 连线槽位不匹配：left_inputs 共 {len(left_inputs)} 个 "
                    f"(期望提示词依次包含槽位 1..{len(left_inputs)})，实际检测到编号: {found_nums}"
                )
    return warnings


def audit_v3_audio_and_pacing(bp: Dict[str, Any]) -> List[str]:
    """Audit V3 speech-rate consistency (4.0-4.2 cps) and No-per-shot-BGM rule."""
    notes: List[str] = []
    mode = bp.get("production_mode", "full_ai")

    for shot in bp.get("shots", []):
        sid = shot.get("shot_id", "Shot")
        vo = (shot.get("voiceover") or "").strip()
        vid = shot.get("video_node", {})
        dur = float(vid.get("duration", 5))
        v_prompt = vid.get("prompt", "")

        # 1. Check speech rate consistency when voiceover is present
        if vo and not vo.startswith("（"):
            char_count = len(CJK_CHAR_RE.findall(vo))
            if char_count > 0 and dur > 0:
                cps = char_count / dur
                if cps > 4.6 or cps < 2.6:
                    notes.append(
                        f"【语速预警】{sid} 台词共 {char_count} 字 / 视频时长 {dur:g}s (折合 {cps:.1f} 字/秒)，"
                        f"偏离 V3 恒定字速区间 (3.5~4.4 字/秒)，建议调整字数或节点时长以防倍速/拖腔。"
                    )

        # 2. Check No-per-shot-BGM rule when sound is enabled
        if str(vid.get("enable_sound", "")).lower() == "on":
            if ("严禁生成任何背景音乐" not in v_prompt) and ("No BGM" not in v_prompt):
                notes.append(
                    f"【BGM冲突预警】{sid} 视频节点开启了有声生成 (enable_sound=on)，"
                    f"建议在提示词中显式加入『【禁配乐红线（No BGM）】严禁生成任何背景音乐』，防止切镜换曲！"
                )

    if mode == "full_ai" and not bp.get("audio_nodes"):
        notes.append(
            "【统合提醒】当前为模式 A (full_ai)，建议在 audio_nodes 中配置角色专属 Minimax 音色母本与全局唯一 ElevenMusic BGM 节点。"
        )
    return notes


def validate_and_plan_commands(
    bp: Dict[str, Any], workspace_root: Path, libtv_bin: str, existing_project_uuid: str = ""
) -> Tuple[List[Tuple[str, List[str]]], List[str]]:
    """Validate V3 blueprint topology and construct ordered libtv CLI commands without `--run`."""
    known_nodes: Set[str] = set()
    planned: List[Tuple[str, List[str]]] = []
    notes: List[str] = audit_v3_audio_and_pacing(bp)

    project_name = bp["project_name"]
    mode = bp.get("production_mode", "full_ai")
    default_ratio = bp.get("aspect_ratio", "9:16")
    image_model = bp.get("image_model", "Lib Image 2.6 Pro")
    image_res = bp.get("image_resolution", "2K")
    video_model = bp.get("video_model", "Seedance 2.5 Flash")
    video_res = bp.get("video_resolution", "480p")

    if existing_project_uuid:
        planned.append(
            ("绑定指定 LibTV 画布项目", [libtv_bin, "project", "use", existing_project_uuid])
        )
    else:
        planned.append(
            ("创建并进入新 LibTV 无限画布项目", [libtv_bin, "project", "create", project_name])
        )

    # Column 0: Overview & Step-by-Step Anti-Empty-URL Guide
    guide_lines = [
        f"【V3 工作流模式】: {'模式A 全AI统合全片' if mode == 'full_ai' else '模式B 轻量AI钩子+实拍混剪'}",
        f"【默认抽卡档位】: 视频预设 {video_model} ({video_res}) | 图像预设 {image_model} (零自动扣费)",
        "【第1步必先运行】: 左侧音色/全局BGM节点 + 环境/角色底座图（严禁音频未出先点视频！）",
        "【第2步运行】: 各行分镜首尾静帧（核对包装字与上下18%+右侧12%安全区）",
        "【第3步运行】: 最右侧 480p 视频抽卡节点",
    ] + bp.get("script_summary", [])
    guide_payload = json.dumps(guide_lines, ensure_ascii=False)
    guide_cmd = [
        libtv_bin,
        "node",
        "--x",
        str(COL0_GUIDE_X),
        "--y",
        str(START_Y),
        "create",
        "00_总剧本与防翻车点跑指南",
        "-t",
        "text",
        "-u",
        f"content={guide_payload}",
    ]
    assert_no_auto_run(guide_cmd)
    planned.append(("导览列: 创建总剧本与分级点跑指南节点", guide_cmd))
    known_nodes.add("00_总剧本与防翻车点跑指南")

    # Column 1: Uploaded SKU Packaging / Inner-Granule / Prop Real Assets
    cur_asset_y = START_Y
    for asset in bp.get("uploaded_assets", []):
        n_name = asset["node_name"]
        m_type = asset.get("media_type", "image")
        rel_path = asset["file_path"]
        abs_path = (workspace_root / rel_path).resolve()
        is_req = asset.get("required", True)

        if abs_path.exists():
            cmd = [
                libtv_bin,
                "upload",
                n_name,
                "-t",
                m_type,
                "--resource",
                str(abs_path),
                "--x",
                str(COL1_ASSETS_X),
                "--y",
                str(cur_asset_y),
            ]
            assert_no_auto_run(cmd)
            planned.append((f"资产列: 上传真实素材 [{n_name}]", cmd))
        else:
            status_tag = "【必补传】" if is_req else "【可选补传】"
            notes.append(
                f"{status_tag} 本地暂未检测到 `{rel_path}`，已创建同名占位节点 `{n_name}`，进画布后可直接替换为实拍图。"
            )
            placeholder_text = json.dumps(
                [f"请在此位置上传替换真实素材: {n_name}", f"说明: {asset.get('description', '')}"],
                ensure_ascii=False,
            )
            cmd = [
                libtv_bin,
                "node",
                "--x",
                str(COL1_ASSETS_X),
                "--y",
                str(cur_asset_y),
                "create",
                n_name,
                "-t",
                "text",
                "-u",
                f"content={placeholder_text}",
            ]
            assert_no_auto_run(cmd)
            planned.append((f"资产列: 创建待上传素材占位节点 [{n_name}]", cmd))

        known_nodes.add(n_name)
        cur_asset_y += ASSET_STEP_Y

    # Column 2: Environment / Character Turnaround / Prop Static Image Nodes
    cur_anchor_y = START_Y
    for anchor in bp.get("anchor_image_nodes", []):
        n_name = anchor["node_name"]
        lefts = anchor.get("left_inputs", [])
        prompt = anchor["prompt"]
        ratio = anchor.get("ratio", default_ratio)

        for up in lefts:
            if up not in known_nodes:
                raise ValueError(f"视觉底座节点 [{n_name}] 引用了未定义的上游节点: [{up}]")
        notes.extend(validate_slot_placeholders(n_name, prompt, lefts))

        cmd = [
            libtv_bin,
            "node",
            "--x",
            str(COL2_ANCHORS_X),
            "--y",
            str(cur_anchor_y),
            "create",
            n_name,
            "-t",
            "image",
            "--prompt",
            prompt,
        ]
        for up in lefts:
            cmd.extend(["--left", up])
        cmd.extend(["-s", f"model={image_model}", "-s", f"ratio={ratio}"])
        if image_res:
            cmd.extend(["-s", f"resolution={image_res}"])

        assert_no_auto_run(cmd)
        planned.append((f"底座列: 创建视觉定妆节点(第1步先跑) [{n_name}]", cmd))
        known_nodes.add(n_name)
        cur_anchor_y += ANCHOR_STEP_Y

    # Column 2B: TTS Voice Locks & Global BGM Audio Nodes (MUST RUN FIRST!)
    cur_audio_y = START_Y
    for aud in bp.get("audio_nodes", []):
        a_name = aud["node_name"]
        a_model = aud.get("model", "Minimax-speech-2.8-hd")
        a_prompt = aud["prompt"]
        cmd = [
            libtv_bin,
            "node",
            "--x",
            str(COL2B_AUDIO_X),
            "--y",
            str(cur_audio_y),
            "create",
            a_name,
            "-t",
            "audio",
            "--prompt",
            a_prompt,
            "-s",
            f"model={a_model}",
        ]
        assert_no_auto_run(cmd)
        planned.append((f"音色与配乐列: 创建音频节点(第1步必先运行!) [{a_name}]", cmd))
        known_nodes.add(a_name)
        cur_audio_y += AUDIO_STEP_Y

    # Column 3 (Keyframes) & Column 4 (480p Draft Video Nodes) — Horizontally Aligned per Shot
    cur_shot_y = START_Y
    for shot in bp.get("shots", []):
        shot_id = shot["shot_id"]
        kf = shot["keyframe_node"]
        kf_name = kf["node_name"]
        kf_lefts = kf.get("left_inputs", [])
        kf_prompt = kf["prompt"]
        kf_ratio = kf.get("ratio", default_ratio)

        for up in kf_lefts:
            if up not in known_nodes:
                raise ValueError(f"分镜首帧 [{kf_name}] 引用了未定义的上游节点: [{up}]")
        notes.extend(validate_slot_placeholders(kf_name, kf_prompt, kf_lefts))

        kf_cmd = [
            libtv_bin,
            "node",
            "--x",
            str(COL3_KEYFRAMES_X),
            "--y",
            str(cur_shot_y),
            "create",
            kf_name,
            "-t",
            "image",
            "--prompt",
            kf_prompt,
        ]
        for up in kf_lefts:
            kf_cmd.extend(["--left", up])
        kf_cmd.extend(["-s", f"model={image_model}", "-s", f"ratio={kf_ratio}"])
        if image_res:
            kf_cmd.extend(["-s", f"resolution={image_res}"])

        assert_no_auto_run(kf_cmd)
        planned.append((f"分镜 [{shot_id}]: 创建首帧静帧(第2步点生图) [{kf_name}]", kf_cmd))
        known_nodes.add(kf_name)

        tkf = shot.get("tail_keyframe_node")
        if tkf:
            tkf_name = tkf["node_name"]
            tkf_lefts = tkf.get("left_inputs", [])
            tkf_prompt = tkf["prompt"]
            tkf_ratio = tkf.get("ratio", default_ratio)

            for up in tkf_lefts:
                if up not in known_nodes:
                    raise ValueError(f"分镜尾帧 [{tkf_name}] 引用了未定义的上游节点: [{up}]")
            notes.extend(validate_slot_placeholders(tkf_name, tkf_prompt, tkf_lefts))

            tkf_cmd = [
                libtv_bin,
                "node",
                "--x",
                str(COL3B_TAIL_KEYFRAMES_X),
                "--y",
                str(cur_shot_y),
                "create",
                tkf_name,
                "-t",
                "image",
                "--prompt",
                tkf_prompt,
            ]
            for up in tkf_lefts:
                tkf_cmd.extend(["--left", up])
            tkf_cmd.extend(["-s", f"model={image_model}", "-s", f"ratio={tkf_ratio}"])
            if image_res:
                tkf_cmd.extend(["-s", f"resolution={image_res}"])

            assert_no_auto_run(tkf_cmd)
            planned.append((f"分镜 [{shot_id}]: 创建尾帧静帧(第2步点生图) [{tkf_name}]", tkf_cmd))
            known_nodes.add(tkf_name)

        vid = shot["video_node"]
        vid_name = vid["node_name"]
        vid_lefts = vid.get("left_inputs", [])
        vid_prompt = vid["prompt"]
        vid_ratio = vid.get("ratio", default_ratio)
        vid_dur = vid.get("duration", 5)
        vid_sound = vid.get("enable_sound", "on")
        shot_video_model = vid.get("model", video_model)
        shot_video_res = vid.get("resolution", video_res)

        for up in vid_lefts:
            if up not in known_nodes:
                raise ValueError(f"分镜视频 [{vid_name}] 引用了未定义的上游节点: [{up}]")
        notes.extend(validate_slot_placeholders(vid_name, vid_prompt, vid_lefts))

        vid_cmd = [
            libtv_bin,
            "node",
            "--x",
            str(COL4_VIDEOS_X),
            "--y",
            str(cur_shot_y),
            "create",
            vid_name,
            "-t",
            "video",
            "--prompt",
            vid_prompt,
        ]
        for up in vid_lefts:
            vid_cmd.extend(["--left", up])
        vid_cmd.extend(
            [
                "-s",
                f"model={shot_video_model}",
                "-s",
                f"ratio={vid_ratio}",
                "-s",
                f"duration={vid_dur}",
                "-s",
                f"resolution={shot_video_res}",
            ]
        )
        if vid_sound:
            vid_cmd.extend(["-s", f"enableSound={vid_sound}"])

        assert_no_auto_run(vid_cmd)
        planned.append(
            (f"分镜 [{shot_id}]: 创建 {shot_video_res} 视频抽卡节点(第3步点生视频) [{vid_name}]", vid_cmd)
        )
        known_nodes.add(vid_name)
        cur_shot_y += SHOT_STEP_Y

    return planned, notes


def render_markdown_manual(bp: Dict[str, Any], notes: List[str]) -> str:
    """Render V3 Dual-Mode prompt & node-wiring specification with Mermaid graph."""
    mode = bp.get("production_mode", "full_ai")
    mode_label = (
        "模式 A：全 AI 统合全片（画面+音色语速+全局BGM 100%统一）"
        if mode == "full_ai"
        else "模式 B：轻量 AI 钩子 + 实拍混剪"
    )
    video_model = bp.get("video_model", "Seedance 2.5 Flash")
    video_res = bp.get("video_resolution", "480p")

    lines: List[str] = []
    lines.append(f"# {bp['project_name']} — V3 提示词与 LibTV 画布预连线总表\n")
    lines.append(
        f"- **制作模式**：`{mode_label}`\n"
        f"- **默认抽卡档位**：视频 `{video_model}` (`{video_res}`) | 零自动扣费（未附加 `--run`）\n"
        f"- **必遵点跑顺序**：**① 先跑左侧音色/BGM与视觉底座（防空 URL 变声） → ② 跑各行首尾静帧 → ③ 跑右侧 480p 视频抽卡**\n"
    )

    if notes:
        lines.append("## 校验与统合预检提醒")
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")

    # Mermaid Topology Diagram
    lines.append("## 一、 LibTV 无限画布节点连线拓扑图\n")
    lines.append("```mermaid")
    lines.append("flowchart LR")

    node_ids: Dict[str, str] = {}
    counter = 1

    def get_id(name: str) -> str:
        nonlocal counter
        if name not in node_ids:
            node_ids[name] = f"N{counter}"
            counter += 1
        return node_ids[name]

    if bp.get("uploaded_assets"):
        lines.append('    subgraph C1["01/02组: 真实包装与内料实拍图"]')
        for a in bp.get("uploaded_assets", []):
            nid = get_id(a["node_name"])
            lines.append(f'        {nid}["{a["node_name"].replace(chr(34), chr(39))}"]')
        lines.append("    end")

    if bp.get("anchor_image_nodes"):
        lines.append('    subgraph C2["03/04组: 环境道具与角色三视图 (第1步生图)"]')
        for anc in bp.get("anchor_image_nodes", []):
            nid = get_id(anc["node_name"])
            lines.append(f'        {nid}["{anc["node_name"].replace(chr(34), chr(39))}"]')
        lines.append("    end")

    if bp.get("audio_nodes"):
        lines.append('    subgraph CA["05组: 同源TTS音色锁与全局唯一BGM (第1步最先运行!)"]')
        for aud in bp.get("audio_nodes", []):
            nid = get_id(aud["node_name"])
            lines.append(f'        {nid}["{aud["node_name"].replace(chr(34), chr(39))}"]')
        lines.append("    end")

    lines.append('    subgraph C3["分镜首尾关键静帧 (第2步生图)"]')
    for s in bp.get("shots", []):
        kname = s["keyframe_node"]["node_name"]
        lines.append(f'        {get_id(kname)}["{kname.replace(chr(34), chr(39))}"]')
        if s.get("tail_keyframe_node"):
            tkname = s["tail_keyframe_node"]["node_name"]
            lines.append(f'        {get_id(tkname)}["{tkname.replace(chr(34), chr(39))}"]')
    lines.append("    end")

    lines.append(f'    subgraph C4["{video_res} 视频抽卡节点 (第3步生视频 · 单镜禁BGM)"]')
    for s in bp.get("shots", []):
        vname = s["video_node"]["node_name"]
        lines.append(f'        {get_id(vname)}["{vname.replace(chr(34), chr(39))}"]')
    lines.append("    end")

    for anc in bp.get("anchor_image_nodes", []):
        dst = get_id(anc["node_name"])
        for idx, up in enumerate(anc.get("left_inputs", []), start=1):
            lines.append(f'    {get_id(up)} -- "Ref {idx}" --> {dst}')

    for s in bp.get("shots", []):
        kf = s["keyframe_node"]
        k_dst = get_id(kf["node_name"])
        for idx, up in enumerate(kf.get("left_inputs", []), start=1):
            lines.append(f'    {get_id(up)} -- "Ref {idx}" --> {k_dst}')

        if s.get("tail_keyframe_node"):
            tkf = s["tail_keyframe_node"]
            tk_dst = get_id(tkf["node_name"])
            for idx, up in enumerate(tkf.get("left_inputs", []), start=1):
                lines.append(f'    {get_id(up)} -- "Ref {idx}" --> {tk_dst}')

        vid = s["video_node"]
        v_dst = get_id(vid["node_name"])
        for idx, up in enumerate(vid.get("left_inputs", []), start=1):
            lines.append(f'    {get_id(up)} -- "Ref {idx}" --> {v_dst}')

    lines.append("```\n")

    if bp.get("audio_nodes"):
        lines.append("## 二、 音色同源锁与全局唯一 BGM 配置（第 1 步必先运行）\n")
        for aud in bp.get("audio_nodes", []):
            role = aud.get("audio_role", "audio")
            extra = ""
            if aud.get("voice_id"):
                extra = f" | `voiceId={aud['voice_id']}` | 固定语速 `speed={aud.get('speed', 1.0)}`"
            lines.append(
                f"- **`{aud['node_name']}`**（`{role}` | 模型：`{aud.get('model', 'Minimax-speech-2.8-hd')}`{extra}）\n"
                f"  > {aud['prompt']}\n"
            )

    lines.append("## 三、 逐分镜静帧与 `480p` 视频提示词明细\n")
    for s in bp.get("shots", []):
        lines.append(
            f"### {s['shot_id']}：{s['title']}（`{s.get('time_range', '')}` | 路由：`{s.get('shot_routing', '')}`）"
        )
        lines.append(f"- **口播台词**：{s.get('voiceover', '（纯画面/物理音效）')}")
        kf = s["keyframe_node"]
        kf_map = "，".join(
            [f"`Ref {i}` ← `{u}`" for i, u in enumerate(kf.get("left_inputs", []), 1)]
        )
        lines.append(f"- **首帧静帧节点**：`{kf['node_name']}`（连线：{kf_map or '无'}）")
        lines.append(f"  > {kf['prompt']}")

        if s.get("tail_keyframe_node"):
            tkf = s["tail_keyframe_node"]
            tkf_map = "，".join(
                [f"`Ref {i}` ← `{u}`" for i, u in enumerate(tkf.get("left_inputs", []), 1)]
            )
            lines.append(f"- **尾帧静帧节点**：`{tkf['node_name']}`（连线：{tkf_map or '无'}）")
            lines.append(f"  > {tkf['prompt']}")

        vid = s["video_node"]
        vid_map = "，".join(
            [f"`Ref {i}` ← `{u}`" for i, u in enumerate(vid.get("left_inputs", []), 1)]
        )
        lines.append(
            f"- **视频抽卡节点**：`{vid['node_name']}`（`{vid.get('duration', 5)}s` | `{vid.get('resolution', video_res)}` | 连线：{vid_map or '无'}）"
        )
        lines.append(f"  > {vid['prompt']}\n")

    if bp.get("real_shoot_handoff"):
        lines.append("## 四、 模式 B：后半段手机实拍混剪无缝对接表\n")
        lines.append("| 时间段 | 镜头定位 | 建议实拍画面 | 衔接切入点 | 同源旁白台词 |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for item in bp["real_shoot_handoff"]:
            lines.append(
                f"| `{item.get('time_range', '')}` | {item.get('role', '')} | {item.get('shoot_guide', '')} | {item.get('cut_in', '')} | {item.get('voiceover', '')} |"
            )
        lines.append("")

    return "\n".join(lines)


def write_shell_script(planned: List[Tuple[str, List[str]]], out_sh: Path) -> None:
    lines = [
        "#!/usr/bin/env bash",
        "# 自动生成的 LibTV V3 无限画布预连线脚本（严格不含 --run，零自动扣费）",
        "set -euo pipefail",
        "",
    ]
    for desc, cmd in planned:
        assert_no_auto_run(cmd)
        quoted = " ".join(shlex.quote(c) for c in cmd)
        lines.append(f"# {desc}")
        lines.append(quoted)
        lines.append("")
    out_sh.write_text("\n".join(lines), encoding="utf-8")
    os.chmod(out_sh, 0o755)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and build V3 Dual-Mode LibTV pre-wired canvas.")
    parser.add_argument("--blueprint", required=True, help="Path to canvas_blueprint.json")
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Workspace root used to resolve relative uploaded asset paths",
    )
    parser.add_argument(
        "--project-uuid",
        default="",
        help="Optional existing LibTV projectUuid (skips creating a new project)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute libtv CLI commands to build nodes on cloud canvas (still NO --run)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate blueprint topology and audio/pacing rules without writing output files",
    )
    args = parser.parse_args()

    bp_path = Path(args.blueprint).expanduser().resolve()
    ws_root = Path(args.workspace_root).expanduser().resolve()
    out_dir = bp_path.parent

    bp = json.loads(bp_path.read_text(encoding="utf-8"))
    libtv_bin = find_libtv_bin()

    planned, notes = validate_and_plan_commands(
        bp=bp,
        workspace_root=ws_root,
        libtv_bin=libtv_bin,
        existing_project_uuid=args.project_uuid.strip(),
    )

    if args.check_only:
        print(f"[CHECK-ONLY] V3 蓝图拓扑与音画统合校验通过！共规划 {len(planned)} 条无扣费预连线指令。")
        for n in notes:
            print(f"  - {n}")
        return 0

    md_out = out_dir / "03_canvas_wiring_and_prompts.md"
    sh_out = out_dir / "04_deploy_canvas_commands.sh"

    md_out.write_text(render_markdown_manual(bp, notes), encoding="utf-8")
    write_shell_script(planned, sh_out)

    print(f"[OK] V3 蓝图拓扑与音画统合校验通过！共规划 {len(planned)} 条无扣费预连线指令。")
    for n in notes:
        print(f"  - {n}")
    print(f"[OK] 已输出提示词与连线总表: {md_out}")
    print(f"[OK] 已输出可审计 CLI 脚本: {sh_out}")

    if not args.apply:
        print("[DRY-RUN] 当前为校验与脚本生成模式（未连接云端执行）。")
        return 0

    if not shutil.which(libtv_bin) and not os.path.exists(libtv_bin):
        print(
            f"[ERROR] 未找到可执行的 libtv CLI ({libtv_bin})。优先使用 LibTV MCP 云端直连，或先运行 check_env_and_libtv.sh。",
            file=sys.stderr,
        )
        return 1

    uuid_re = re.compile(r"([0-9a-fA-F]{32}|[0-9a-fA-F-]{36})")
    detected_uuid = args.project_uuid.strip()

    for idx, (desc, cmd) in enumerate(planned, start=1):
        assert_no_auto_run(cmd)
        print(f"[{idx}/{len(planned)}] {desc} ...")
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        if proc.stdout:
            print(proc.stdout.strip())
        if proc.returncode != 0:
            print(f"[ERROR] 指令执行失败 (exit={proc.returncode}): {' '.join(cmd)}", file=sys.stderr)
            if proc.stderr:
                print(proc.stderr.strip(), file=sys.stderr)
            return proc.returncode

        if idx == 1 and not detected_uuid and proc.stdout:
            m = uuid_re.search(proc.stdout)
            if m:
                detected_uuid = m.group(1)
                subprocess.run([libtv_bin, "project", "use", detected_uuid], check=False)

    print("\n=== LibTV V3 无限画布预连线搭建完成（0 算力消耗，未执行任何 --run）===")
    if detected_uuid:
        print(f"画布网页端入口: https://www.liblib.tv/canvas?projectId={detected_uuid}")
    print("必遵人工点跑顺序：① 先跑左侧音色/全局BGM与视觉底座 -> ② 跑各分镜首尾静帧 -> ③ 跑右侧 480p 视频抽卡")
    return 0


if __name__ == "__main__":
    sys.exit(main())
