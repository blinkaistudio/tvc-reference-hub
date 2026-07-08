# -*- coding: utf-8 -*-
"""광고 큐레이션 채널들의 최신 업로드 수집 (YouTube 채널 RSS) → feeds.js"""
import sys, json, re, time, html, urllib.request, urllib.parse
from datetime import date
from pathlib import Path
from yt_common import get, filter_embeddable

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
ID_CACHE = HERE / "channel_id_cache.json"
PER = 8

# (표시명, 설명, channelId 탐색용 검색어)
CHANNELS = [
    ("Amazing Ads", "칸 라이언즈 수상작 케이스 스터디", "Amazing Ads Cannes Grand Prix case study"),
    ("The Hall of Advertising", "역대 명작 광고 아카이브", "The Hall of Advertising"),
    ("JP Ad Play", "일본 최신 CM 큐레이션", "JP Ad Play 最新CM"),
    ("Commercial Archivist", "미국 온에어 광고 기록", "Commercial Archivist commercial"),
    ("Dose of Good Ads", "글로벌 웰메이드 광고 큐레이션", "Dose of Good Ads"),
    ("WORLD CLASS ADVERTISING", "세계 광고 명작 모음", "WORLD CLASS ADVERTISING ads"),
    ("Campaigns of the world", "글로벌 캠페인 큐레이션", "Campaigns of the world"),
    ("돌고래유괴단", "국내 최강 화제성 프로덕션 (신작 피드)", "돌고래유괴단"),
    ("스튜디오좋", "세계관 광고 스튜디오 (신작 피드)", "스튜디오좋 광고"),
]


def resolve_channel_id(query):
    body = get("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    m = re.search(r"var ytInitialData = (\{.*?\});</script>", body, re.DOTALL)
    if not m:
        return None
    data = json.loads(m.group(1))
    found = []

    def walk(node):
        if isinstance(node, dict):
            if "channelRenderer" in node:
                c = node["channelRenderer"]
                cid = c.get("channelId")
                name = c.get("title", {}).get("simpleText", "")
                if cid:
                    found.append((cid, name))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(data)
    return found[0] if found else None


def rss_latest(channel_id):
    body = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", body, re.DOTALL):
        vid = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", entry)
        title = re.search(r"<title>([^<]*)</title>", entry)
        pub = re.search(r"<published>([^<]+)</published>", entry)
        if vid and title:
            out.append({"id": vid.group(1),
                        "title": html.unescape(title.group(1)),
                        "date": (pub.group(1)[:10] if pub else "")})
    return out


def main():
    cache = json.loads(ID_CACHE.read_text(encoding="utf-8")) if ID_CACHE.exists() else {}
    out = {"fetchedAt": date.today().isoformat(), "channels": []}
    for name, desc, query in CHANNELS:
        cid = cache.get(name)
        cname = name
        if not cid:
            r = resolve_channel_id(query)
            if not r:
                print(f"  ! {name}: 채널 ID 못 찾음")
                continue
            cid, cname = r
            cache[name] = cid
            print(f"  {name} → {cname} ({cid})")
        try:
            vids = rss_latest(cid)[:PER]
        except Exception as e:
            print(f"  ! {name} RSS 실패: {e}")
            continue
        vids = filter_embeddable(vids)
        out["channels"].append({"name": name, "desc": desc, "channelId": cid,
                                "url": f"https://www.youtube.com/channel/{cid}", "videos": vids})
        print(f"  {name}: 최신 {len(vids)}개")
        time.sleep(0.3)

    ID_CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    (HERE / "feeds.js").write_text("window.TVC_FEEDS = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    total = sum(len(c["videos"]) for c in out["channels"])
    print(f"\n완료: {len(out['channels'])}개 채널, 최신 영상 {total}개 → feeds.js")


if __name__ == "__main__":
    main()
