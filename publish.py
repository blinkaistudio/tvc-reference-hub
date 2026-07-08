# -*- coding: utf-8 -*-
"""갱신된 데이터를 GitHub Pages로 배포 (git commit + push).

로컬 갱신(데이터갱신.bat / serve.py 웹 버튼) 마지막 단계에서 호출.
git 원격이 없거나 실패해도 사이트 로컬 사용에는 지장 없도록 조용히 종료.
"""
import sys, subprocess, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent


def run(*args):
    return subprocess.run(["git"] + list(args), cwd=HERE, capture_output=True, text=True)


def main():
    if not (HERE / ".git").exists():
        print("git 저장소가 아님 — 배포 생략")
        return 0
    run("add", "-A")
    diff = run("diff", "--cached", "--quiet")
    if diff.returncode == 0:
        print("변경사항 없음 — 배포 생략")
        return 0
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    run("commit", "-m", f"data-update {stamp}")
    # 원격(Actions 봇)과 충돌 방지: 내 쪽(방금 수집) 우선 머지
    run("fetch", "origin", "main")
    run("merge", "-s", "ours", "origin/main", "-m", "merge remote")
    p = run("push")
    if p.returncode == 0:
        print("✓ 웹 배포 완료 → https://blinkaistudio.github.io/tvc-reference-hub/")
    else:
        print(f"푸시 실패(로컬 사용은 정상): {p.stderr.strip()[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
