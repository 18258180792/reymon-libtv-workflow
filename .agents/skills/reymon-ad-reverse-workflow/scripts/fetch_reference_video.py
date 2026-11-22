#!/usr/bin/env python3
"""Prepare reference video input from a local file path or URL for native multimodal analysis."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare reference video in run input folder.")
    parser.add_argument("--source", required=True, help="Local video file path or video URL")
    parser.add_argument("--output-dir", required=True, help="Target input directory (e.g. runs/batch01/input)")
    args = parser.parse_args()

    out_dir = Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    src = args.source.strip()

    if src.startswith(("http://", "https://")):
        yt_dlp = shutil.which("yt-dlp")
        if not yt_dlp:
            print(
                "[MANUAL_VIDEO_REQUIRED] 当前环境未安装 yt-dlp，无法直接从防盗链短视频网址拉取原片。\n"
                f"请将参考视频无水印 MP4 下载后放入目录：{out_dir}\n"
                "放入后我可直接用当前对话模型的原生音视频读取能力逐帧拆解节奏与逻辑。",
                file=sys.stderr,
            )
            return 2

        output_tpl = str(out_dir / "reference_video.%(ext)s")
        cmd = [yt_dlp, "--no-playlist", "-f", "mp4/best", "-o", output_tpl, src]
        print(f"[INFO] 正在拉取参考视频: {' '.join(cmd)}")
        res = subprocess.run(cmd, check=False)
        if res.returncode != 0:
            print(
                f"[MANUAL_VIDEO_REQUIRED] 链接受平台登录墙或反爬限制无法直接下载，请将视频保存至：{out_dir}",
                file=sys.stderr,
            )
            return 2
        print(f"[OK] 视频已下载至目录: {out_dir}")
        return 0

    src_path = Path(src).expanduser().resolve()
    if not src_path.exists():
        print(f"[ERROR] 找不到本地视频文件: {src_path}", file=sys.stderr)
        return 1

    dest_path = out_dir / src_path.name
    if src_path != dest_path:
        shutil.copy2(src_path, dest_path)
    size_mb = os.path.getsize(dest_path) / (1024 * 1024)
    print(f"[OK] 参考视频已就绪: {dest_path} ({size_mb:.2f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
