# -*- coding: utf-8 -*-
"""유튜브 검색 결과에서 TVC 레퍼런스 영상 데이터를 수집해 data.js 생성"""
import sys, json, re, time, urllib.request, urllib.parse
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8,ja;q=0.7",
}

COUNTRIES = {
    "kr": {
        "label": "🇰🇷 한국",
        "cats": [
            ("최신 광고", "한국 TV 광고 2026"),
            ("뷰티", "화장품 광고 2026 CF"),
            ("자동차", "현대자동차 기아 광고 2026"),
            ("테크/가전", "삼성 갤럭시 LG 광고 2026"),
            ("금융", "금융 보험 광고 2026 CF"),
            ("F&B", "식품 음료 광고 2026 CF"),
            ("통신", "SKT KT LG유플러스 광고 2026"),
            ("명작", "한국 레전드 광고 모음"),
        ],
    },
    "jp": {
        "label": "🇯🇵 일본",
        "cats": [
            ("최신 CM", "日本 CM 2026 最新"),
            ("뷰티", "資生堂 コスメ CM 2026"),
            ("자동차", "トヨタ ホンダ 日産 CM 2026"),
            ("테크/가전", "ソニー パナソニック CM"),
            ("F&B", "サントリー 明治 CM 2026"),
            ("통신", "au ソフトバンク docomo CM 2026"),
            ("철도/여행", "JR CM 京都"),
            ("명작", "日本 CM 名作 傑作選"),
        ],
    },
    "us": {
        "label": "🇺🇸 미국",
        "cats": [
            ("최신 광고", "best US TV commercials 2026"),
            ("슈퍼볼", "Super Bowl commercials 2026"),
            ("뷰티", "beauty commercial 2026"),
            ("자동차", "car commercial 2026 USA"),
            ("테크", "Apple Google Samsung commercial 2026"),
            ("금융", "insurance bank commercial USA 2026"),
            ("F&B", "food beverage commercial 2026 USA"),
            ("명작", "best commercials of all time"),
        ],
    },
    "uk": {
        "label": "🇬🇧 영국",
        "cats": [
            ("최신 광고", "best UK adverts 2026"),
            ("크리스마스", "John Lewis Christmas advert"),
            ("뷰티/패션", "UK fashion beauty advert"),
            ("자동차", "UK car advert 2026"),
            ("금융", "UK bank advert"),
            ("F&B", "UK food advert 2026"),
            ("통신", "EE Vodafone Three advert"),
            ("명작", "best british adverts of all time"),
        ],
    },
    "global": {
        "label": "🌍 글로벌",
        "cats": [
            ("칸 수상작", "Cannes Lions Grand Prix film 2025"),
            ("럭셔리/패션", "luxury fashion film commercial"),
            ("시네마틱", "cinematic commercial film ad"),
            ("유럽", "best european commercials"),
            ("태국", "thai commercial emotional"),
            ("AI 광고", "AI generated commercial 2026"),
        ],
    },
}

PER_QUERY = 12

def fetch(query: str):
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        html = r.read().decode("utf-8", errors="ignore")
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

def main():
    out = {"fetchedAt": date.today().isoformat(), "countries": {}}
    for cid, c in COUNTRIES.items():
        vids, seen = [], set()
        for cat, q in c["cats"]:
            try:
                results = fetch(q)
            except Exception as e:
                print(f"  ! {cid}/{cat} 실패: {e}")
                results = []
            n = 0
            for v in results:
                if v["id"] in seen:
                    continue
                seen.add(v["id"])
                v["cat"] = cat
                vids.append(v)
                n += 1
                if n >= PER_QUERY:
                    break
            print(f"  {c['label']} [{cat}] {n}개")
            time.sleep(0.6)
        out["countries"][cid] = {"label": c["label"], "cats": [cat for cat, _ in c["cats"]], "videos": vids}
        print(f"{c['label']} 합계 {len(vids)}개")

    # 임베드 불가/삭제 영상 제거
    try:
        from yt_common import filter_embeddable
        for c in out["countries"].values():
            before = len(c["videos"])
            c["videos"] = filter_embeddable(c["videos"])
            if before != len(c["videos"]):
                print(f"  {c['label']} 임베드 불가 {before - len(c['videos'])}개 제거")
    except Exception as e:
        print(f"  ! 임베드 검사 생략: {e}")

    dest = Path(__file__).parent / "data.js"
    dest.write_text("window.TVC_DATA = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    total = sum(len(v["videos"]) for v in out["countries"].values())
    print(f"\n완료: 총 {total}개 영상 → {dest}")

if __name__ == "__main__":
    main()
