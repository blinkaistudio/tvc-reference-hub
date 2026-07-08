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

    def _bytes(self, data, ctype, code=200):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        try:
            return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            return {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

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
        # 웹 배포판(GitHub Pages)에서도 로컬 헬퍼를 부를 수 있게 CORS 허용
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
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
        if parsed.path == "/api/download":
            body = self._read_body()
            url = body.get("url", "")
            if not url.startswith("http"):
                return self._json({"ok": False, "error": "잘못된 URL"}, 400)
            threading.Thread(target=do_download, args=(url,), daemon=True).start()
            return self._json({"ok": True, "dest": str(DL_DIR)})
        if parsed.path == "/api/frame":
            body = self._read_body()
            url, t = body.get("url", ""), float(body.get("t") or 0)
            if not url.startswith("http"):
                return self._json({"ok": False, "error": "잘못된 URL"}, 400)
            try:
                jpg, path = do_frame(url, t)
                import base64
                return self._json({"ok": True, "path": path,
                                   "jpg_b64": base64.b64encode(jpg).decode()})
            except Exception as e:
                return self._json({"ok": False, "error": str(e)[:300]}, 500)
        return self._json({"ok": False, "error": "unknown"}, 404)


# ---------------- 다운로드 / 프레임 캡처 (yt-dlp + ffmpeg) ----------------
DL_DIR = Path.home() / "Downloads" / "TVC레퍼런스"


def find_ffmpeg():
    import shutil, glob
    p = shutil.which("ffmpeg")
    if p:
        return p
    hits = glob.glob(str(Path.home() / "AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*"
                         "/ffmpeg-*/bin/ffmpeg.exe"))
    return hits[0] if hits else "ffmpeg"


def do_download(url):
    """원본 최고화질(1080p 상한)로 Downloads/TVC레퍼런스에 저장 후 폴더 열기."""
    DL_DIR.mkdir(parents=True, exist_ok=True)
    log(f"⬇ 다운로드 시작: {url}")
    cmd = [sys.executable, "-m", "yt_dlp",
           "-f", "bv*[height<=1080]+ba/b[height<=1080]/b",
           "--ffmpeg-location", find_ffmpeg(),
           "-o", "%(title).80s [%(id)s].%(ext)s", "-P", str(DL_DIR), url]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode == 0:
        log("⬇ 다운로드 완료")
        try:
            import os
            os.startfile(DL_DIR)
        except OSError:
            pass
    else:
        log(f"⬇ 다운로드 실패: {(p.stderr or '')[-200:]}")


def do_frame(url, t):
    """영상의 t초 지점 프레임을 JPG로 추출 → (bytes, 저장경로)."""
    DL_DIR.mkdir(parents=True, exist_ok=True)
    # 1) yt-dlp로 직접 스트림 URL 획득 (mp4 우선 — ffmpeg 시킹 안정성)
    # progressive(https) 스트림 우선 — DASH mpd는 ffmpeg에서 403 나는 경우가 많음(비메오)
    g = subprocess.run([sys.executable, "-m", "yt_dlp", "--no-update", "-g",
                        "-f", ("b[protocol=https][height<=1080]/bv*[protocol=https][height<=1080]"
                               "/bv*[ext=mp4][height<=1080]/b"), url],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    stream = (g.stdout or "").strip().splitlines()
    out = DL_DIR / f"캡처_{int(time.time())}_{int(t)}s.jpg"
    UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    if stream:
        # 1차: 스트림 URL에서 바로 추출 (브라우저 헤더 필요 — 비메오 CDN 403 방지)
        f = subprocess.run([find_ffmpeg(), "-y", "-user_agent", UA,
                            "-referer", "https://vimeo.com/" if "vimeo" in url else "https://www.youtube.com/",
                            "-ss", f"{t:.2f}", "-i", stream[0],
                            "-frames:v", "1", "-q:v", "2", str(out)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90)
        if f.returncode == 0 and out.exists():
            return out.read_bytes(), str(out)
    # 2차 폴백: 해당 구간만 임시 다운로드(yt-dlp가 인증 헤더 처리) 후 추출
    import tempfile, glob as _glob
    with tempfile.TemporaryDirectory() as td:
        dl = subprocess.run([sys.executable, "-m", "yt_dlp", "--no-update",
                             "--download-sections", f"*{max(t-0.5,0):.1f}-{t+1.5:.1f}",
                             "-f", "bv*[height<=1080]/b", "--ffmpeg-location", find_ffmpeg(),
                             "-o", "clip.%(ext)s", "-P", td, url],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        clips = _glob.glob(str(Path(td) / "clip.*"))
        if not clips:
            raise RuntimeError("구간 다운로드 실패: " + (dl.stderr or "")[-150:])
        f2 = subprocess.run([find_ffmpeg(), "-y", "-ss", "0.5", "-i", clips[0],
                             "-frames:v", "1", "-q:v", "2", str(out)],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        if f2.returncode != 0 or not out.exists():
            # 구간 맨 앞 프레임이라도
            f3 = subprocess.run([find_ffmpeg(), "-y", "-i", clips[0],
                                 "-frames:v", "1", "-q:v", "2", str(out)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            if f3.returncode != 0 or not out.exists():
                raise RuntimeError("프레임 추출 실패: " + (f2.stderr or "")[-150:])
    return out.read_bytes(), str(out)


def main():
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}/index.html"
    print(f"TVC Reference Hub 서버 실행 중: {url}")
    print("이 창을 닫으면 사이트가 꺼집니다.")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
