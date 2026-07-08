# -*- coding: utf-8 -*-
"""5초 이내 초단편 트랜지션/무빙 레퍼런스 수집 → shorts.js 생성
검색 결과(일반+쇼츠)에서 후보를 모은 뒤, 시청 페이지의 lengthSeconds로 정확히 필터링"""
import sys, json, re, time, urllib.request, urllib.parse
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
LEN_CACHE = HERE / "shorts_len_cache.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

MAX_SEC = 5      # 메인: 5초 이내
EXT_SEC = 10     # 보조: 6~10초
PER_QUERY = 25   # 쿼리당 후보 상한

QUERIES = [
    ("트랜지션", "seamless transition #shorts"),
    ("트랜지션", "whip pan transition #shorts"),
    ("트랜지션", "match cut transition #shorts"),
    ("트랜지션", "zoom transition #shorts"),
    ("트랜지션", "spin transition #shorts"),
    ("트랜지션", "invisible cut #shorts"),
    ("트랜지션", "impact transition edit #shorts"),
    ("트랜지션", "creative transition #shorts"),
    ("트랜지션", "smooth transition camera #shorts"),
    ("트랜지션", "transition in 5 seconds"),
    ("무빙", "fpv fly through #shorts"),
    ("무빙", "dolly zoom #shorts"),
    ("무빙", "bolt cam high speed #shorts"),
    ("무빙", "probe lens shot #shorts"),
    ("무빙", "camera whoosh #shorts"),
    ("무빙", "orbit shot #shorts"),
    ("무빙", "hyperlapse #shorts"),
    ("무빙", "speed ramp #shorts"),
    ("무빙", "cinematic camera movement #shorts"),
    ("무빙", "crash zoom #shorts"),
    ("B롤", "product b roll #shorts"),
    ("B롤", "cinematic b roll #shorts"),
    ("B롤", "commercial b roll #shorts"),
    ("B롤", "food b roll #shorts"),
    ("B롤", "perfume b roll #shorts"),
    ("B롤", "cosmetic commercial shot #shorts"),
]


def get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse_sec(t):
    try:
        parts = [int(p) for p in t.split(":")]
    except ValueError:
        return None
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def clean_reel_title(txt):
    # "제목, 10 million views - play Short" → "제목"
    return re.sub(r",\s*[\d.,]+\s*(thousand|million|billion)?\s*views?\s*-\s*play Short\s*$", "", txt, flags=re.I).strip()


def search(query):
    """일반 videoRenderer + 쇼츠(reelWatchEndpoint) 후보 수집"""
    html = get("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", html, re.DOTALL)
    if not m:
        return []
    data = json.loads(m.group(1))
    items = []

    def walk(node):
        if isinstance(node, dict):
            if "videoRenderer" in node:
                v = node["videoRenderer"]
                vid = v.get("videoId")
                title = "".join(r.get("text", "") for r in v.get("title", {}).get("runs", []))
                length = v.get("lengthText", {}).get("simpleText", "")
                if vid and title:
                    items.append({"id": vid, "title": title, "sec": parse_sec(length) if length else None})
            if "reelWatchEndpoint" in node:
                vid = node["reelWatchEndpoint"].get("videoId")
                if vid:
                    items.append({"id": vid, "title": "", "sec": None})
            if "accessibilityText" in node and "entityId" in node and str(node.get("entityId", "")).startswith("shorts-shelf-item-"):
                vid = node["entityId"].replace("shorts-shelf-item-", "")
                for it in items:
                    if it["id"] == vid and not it["title"]:
                        it["title"] = clean_reel_title(node["accessibilityText"])
            for val in node.values():
                walk(val)
        elif isinstance(node, list):
            for val in node:
                walk(val)

    walk(data)
    # entityId 매칭이 순서 문제로 빠질 수 있어 한 번 더
    def walk2(node):
        if isinstance(node, dict):
            if str(node.get("entityId", "")).startswith("shorts-shelf-item-") and "accessibilityText" in node:
                vid = node["entityId"].replace("shorts-shelf-item-", "")
                for it in items:
                    if it["id"] == vid and not it["title"]:
                        it["title"] = clean_reel_title(node["accessibilityText"])
            for val in node.values():
                walk2(val)
        elif isinstance(node, list):
            for val in node:
                walk2(val)
    walk2(data)
    return items[:PER_QUERY * 3]


def fetch_length(vid):
    """시청 페이지에서 정확한 길이(초) 파싱"""
    try:
        html = get("https://www.youtube.com/watch?v=" + vid)
        m = re.search(r'"lengthSeconds":"(\d+)"', html)
        if m:
            return vid, int(m.group(1))
        m = re.search(r'"approxDurationMs":"(\d+)"', html)
        if m:
            return vid, round(int(m.group(1)) / 1000)
    except Exception:
        pass
    return vid, None


def main():
    cache = json.loads(LEN_CACHE.read_text(encoding="utf-8")) if LEN_CACHE.exists() else {}
    candidates = {}  # id -> {title, group, sec(None=미상)}
    for group, q in QUERIES:
        try:
            results = search(q)
        except Exception as e:
            print(f"  ! {q} 실패: {e}")
            continue
        n = 0
        for v in results:
            if v["id"] in candidates:
                continue
            if v["sec"] is not None and v["sec"] > EXT_SEC:
                continue  # 이미 길이를 알고 10초 초과면 제외
            candidates[v["id"]] = {"title": v["title"], "group": group, "sec": v["sec"]}
            n += 1
            if n >= PER_QUERY:
                break
        print(f"  [{group}] {q} → 후보 {n}개")
        time.sleep(0.4)

    unknown = [vid for vid, c in candidates.items() if c["sec"] is None and vid not in cache]
    print(f"\n후보 총 {len(candidates)}개, 길이 조회 필요 {len(unknown)}개 (캐시 {len(candidates) - len(unknown)}개)")

    done = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        for vid, sec in ex.map(fetch_length, unknown):
            cache[vid] = sec
            done += 1
            if done % 50 == 0:
                print(f"  길이 조회 {done}/{len(unknown)}")
                LEN_CACHE.write_text(json.dumps(cache), encoding="utf-8")
    LEN_CACHE.write_text(json.dumps(cache), encoding="utf-8")

    core, ext = [], []
    for vid, c in candidates.items():
        sec = c["sec"] if c["sec"] is not None else cache.get(vid)
        if sec is None:
            continue
        item = {"id": vid, "title": c["title"] or "(제목 없음)", "sec": sec, "group": c["group"]}
        if sec <= MAX_SEC:
            core.append(item)
        elif sec <= EXT_SEC:
            ext.append(item)

    try:
        from yt_common import filter_embeddable
        core = filter_embeddable(core)
        ext = filter_embeddable(ext)
    except Exception as e:
        print(f"  ! 임베드 검사 생략: {e}")

    core.sort(key=lambda x: x["sec"])
    ext.sort(key=lambda x: x["sec"])
    out = {"fetchedAt": date.today().isoformat(), "core": core, "ext": ext,
           "groups": ["트랜지션", "무빙", "B롤"]}
    (HERE / "shorts.js").write_text("window.TVC_SHORTS = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    print(f"\n완료: ≤{MAX_SEC}초 {len(core)}개, {MAX_SEC+1}~{EXT_SEC}초 {len(ext)}개 → shorts.js")


if __name__ == "__main__":
    main()
