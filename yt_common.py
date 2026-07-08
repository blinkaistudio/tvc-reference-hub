# -*- coding: utf-8 -*-
"""유튜브 수집 공용 헬퍼: 검색 파싱 + 임베드 가능 여부 검사"""
import json, re, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def search_videos(query):
    """검색 결과의 videoRenderer 목록 [{id,title,ch,len}]"""
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
                channel = "".join(r.get("text", "") for r in v.get("ownerText", {}).get("runs", []))
                length = v.get("lengthText", {}).get("simpleText", "")
                if vid and title:
                    items.append({"id": vid, "title": title, "ch": channel, "len": length})
            for val in node.values():
                walk(val)
        elif isinstance(node, list):
            for val in node:
                walk(val)

    walk(data)
    return items


def is_embeddable(vid):
    """oEmbed 200 = 존재하고 임베드 허용"""
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception:
        return False


def filter_embeddable(videos, key="id", workers=16):
    """임베드 불가/삭제 영상 제거"""
    ids = [v[key] for v in videos]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        ok = dict(zip(ids, ex.map(is_embeddable, ids)))
    return [v for v in videos if ok.get(v[key])]
