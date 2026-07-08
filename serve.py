# -*- coding: utf-8 -*-
"""TVC Reference Hub 로컬 서버
- 정적 파일 서빙 (유튜브/비메오 임베드는 file://에서 재생 불가 → http 필수)
- POST /api/update?mode=quick|full : 데이터 갱신 실행 (백그라운드)
- GET  /api/status : 갱신 진행 상황(JSON)
"""
import sys, json, threading, subprocess, webbrowser, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).parent
PORT = 8777

STATE = {"running": False, "mode": "", "log": [], "done": False, "startedAt": 0}
LOCK = threading.Lock()

# (라벨, 스크립트/인자)  quick=신작 피드만, full=전체
STEPS = {
    "quick": [
        ("큐레이션 채널 최신 피드", ["update_feeds.py"]),
        ("모션 스튜디오 Vimeo 신작", ["update_vimeo.py"]),
        ("힙 스튜디오 100 신작", ["update_hip.py"]),
        ("웹 배포 (GitHub Pages)", ["publish.py"]),
    ],
    "full": [
        ("국가별 TVC 재수집", ["update_data.py"]),
        ("카메라 무빙", ["update_moves.py"]),
        ("5초 컷 (길이 검증 — 오래 걸림)", ["update_shorts.py"]),
        ("프로덕션/디렉터", ["update_legends.py"]),
        ("모션 스튜디오 Vimeo", ["update_vimeo.py"]),
        ("힙 스튜디오 100", ["update_hip.py"]),
        ("큐레이션 채널 피드", ["update_feeds.py"]),
        ("패싯 기본 태그", ["tag_tools.py", "fallback"]),
        ("웹 배포 (GitHub Pages)", ["publish.py"]),
    ],
}


def log(msg):
    with LOCK:
        STATE["log"].append(msg)
        if len(STATE["log"]) > 300:
            STATE["log"] = STATE["log"][-300:]
    print(msg, flush=True)


def run_update(mode):
    steps = STEPS.get(mode, STEPS["quick"])
    log(f"=== {'전체' if mode == 'full' else '신작'} 갱신 시작 ({len(steps)}단계) ===")
    for i, (label, args) in enumerate(steps, 1):
        log(f"[{i}/{len(steps)}] {label}...")
        try:
            p = subprocess.Popen([sys.executable] + [str(HERE / args[0])] + args[1:],
                                 cwd=str(HERE), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 text=True, encoding="utf-8", errors="replace")
            for line in p.stdout:
                line = line.rstrip()
                if line:
                    log("   " + line)
            p.wait()
            if p.returncode != 0:
                log(f"   ! 종료코드 {p.returncode}")
        except Exception as e:
            log(f"   ! 실패: {e}")
    log("=== 갱신 완료! 페이지를 새로고침하면 반영됩니다 ===")
    with LOCK:
        STATE["running"] = False
        STATE["done"] = True


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(HERE), **kw)

    def log_message(self, *a):  # 조용히
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/ping":
            return self._json({"ok": True})
        if parsed.path == "/api/status":
            with LOCK:
                return self._json({"running": STATE["running"], "mode": STATE["mode"],
                                   "done": STATE["done"], "log": STATE["log"][-40:]})
        # 데이터 js 파일은 캐시 금지
        if parsed.path.endswith(".js") or parsed.path.endswith(".html") or parsed.path == "/":
            self.protocol_version = "HTTP/1.1"
        return super().do_GET()

    def end_headers(self):
        if self.path.endswith((".js", ".html")) or self.path == "/":
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/update":
            mode = parse_qs(parsed.query).get("mode", ["quick"])[0]
            with LOCK:
                if STATE["running"]:
                    return self._json({"ok": False, "error": "이미 갱신이 진행 중입니다"}, 409)
                STATE.update(running=True, mode=mode, log=[], done=False, startedAt=time.time())
            threading.Thread(target=run_update, args=(mode,), daemon=True).start()
            return self._json({"ok": True, "mode": mode})
        return self._json({"ok": False, "error": "unknown"}, 404)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/index.html"
    print(f"TVC Reference Hub 서버 실행 중: {url}")
    print("이 창을 닫으면 사이트가 꺼집니다.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
