# -*- coding: utf-8 -*-
"""카메라 무빙 레퍼런스 영상 수집 → moves.js 생성 (커머셜 필름 관점)"""
import sys, json, re, time, urllib.request, urllib.parse
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
}

# (key, 이름, 영문, 카테고리, 설명, 커머셜 활용 팁, 검색어)
MOVES = [
    ("basics", "무빙 총정리", "Camera Movements 101", "📚 기초",
     "팬부터 크레인까지 모든 카메라 무빙을 한 번에 훑는 개론 영상 모음.",
     "팀 온보딩·클라이언트 설득용 레퍼런스로 활용. 무빙 용어를 통일하면 콘티 커뮤니케이션이 빨라진다.",
     "all camera movements explained cinematography"),
    ("pan", "팬", "Pan", "🎬 기본 무빙",
     "카메라 위치는 고정, 수평으로 회전. 공간을 소개하거나 피사체를 따라가는 가장 기본 무빙.",
     "제품 라인업을 좌→우로 훑을 때, 두 인물의 시선 연결에. 속도가 곧 감정 — 느리면 우아, 빠르면 위트.",
     "pan shot examples film cinematography"),
    ("tilt", "틸트", "Tilt", "🎬 기본 무빙",
     "카메라 위치는 고정, 수직으로 회전. 인물 전신 소개(틸트 업)나 스케일 강조에 사용.",
     "빌딩·보틀 같은 세로 피사체의 위용 강조. 로우앵글 틸트 업 = 히어로 샷의 기본 문법.",
     "tilt shot examples film cinematography"),
    ("zoom", "줌 / 크래시 줌", "Zoom / Crash Zoom", "🎬 기본 무빙",
     "렌즈 화각 변화로 다가가거나 물러남. 급격한 크래시 줌은 코믹·임팩트 연출의 단골.",
     "유머 광고의 리액션 강조(크래시 줌 인), 레트로 무드 연출. 요즘은 '의도적으로 촌스럽게' 쓰는 게 힙하다.",
     "crash zoom examples film"),
    ("roll", "롤", "Camera Roll", "🎬 기본 무빙",
     "렌즈 축을 중심으로 카메라를 회전. 불안정·전환·초현실 무드를 만든다.",
     "음료 캔이 기울며 세계가 함께 도는 트랜지션, 더치앵글로 긴장감 주기. 과용 금지 — 포인트 컷에 한 번.",
     "camera roll shot examples film"),
    ("pushin", "푸시 인 / 풀 아웃", "Push In / Pull Out", "🚶 이동 무빙",
     "카메라 자체가 피사체로 다가가거나(푸시 인) 물러남(풀 아웃). 줌과 달리 공간감이 살아있다.",
     "감정 클로즈업 직전의 슬로우 푸시 인 = 몰입. 풀 아웃으로 제품→라이프스타일 전체 공개(리빌).",
     "push in shot examples film"),
    ("tracking", "트래킹 샷", "Tracking Shot", "🚶 이동 무빙",
     "이동하는 피사체를 나란히 따라가는 무빙. 인물의 에너지와 여정을 그대로 전달.",
     "러닝·워킹 캠페인의 기본기. 사이드 트래킹 + 배경 변화로 '하루의 흐름'을 한 컷에 압축할 수 있다.",
     "tracking shot examples commercial"),
    ("orbit", "아크 / 오빗", "Arc / Orbit", "🚶 이동 무빙",
     "피사체를 중심에 두고 원을 그리며 도는 무빙. 피사체를 '주인공'으로 만드는 힘이 있다.",
     "제품 히어로 샷의 정석. 인물 오빗 + 조명 변화 조합이면 비포/애프터 전환도 한 컷에 가능.",
     "orbit shot arc camera movement examples"),
    ("boom", "붐 업 / 다운", "Boom / Pedestal", "🚶 이동 무빙",
     "카메라가 수직으로 상승·하강. 장면의 스케일을 열거나 디테일로 내려앉는다.",
     "오프닝에서 붐 다운으로 세계→주인공 진입, 엔딩에서 붐 업으로 여운. 시작과 끝의 문법.",
     "boom up crane shot examples film"),
    ("steadicam", "스테디캠 / 짐벌", "Steadicam / Gimbal", "🛠 장비 기반",
     "흔들림 없이 유영하듯 따라가는 무빙. 긴 호흡의 몰입형 팔로우가 가능.",
     "매장·집·공장 투어를 원테이크로. 인물 뒤통수 팔로우 → 문 열림 → 공간 리빌 패턴은 언제나 통한다.",
     "steadicam one take commercial"),
    ("crane", "크레인 / 지미집", "Crane / Jib", "🛠 장비 기반",
     "크레인 암으로 크고 부드러운 궤적을 그리는 무빙. 웅장한 스케일 연출의 대명사.",
     "군중·건축·자동차 캠페인의 스케일 샷. 지미집 특유의 포물선 궤적은 TVC 엔딩 로고샷과 찰떡.",
     "crane shot commercial examples"),
    ("fpv", "드론 / FPV", "FPV Drone", "🛠 장비 기반",
     "레이싱 드론으로 좁은 틈을 통과하며 나는 초고속 몰입 무빙. 요즘 커머셜의 핫 트렌드.",
     "공장 라인·주방·매장을 관통하는 원테이크 브랜드 투어. 버거킹·아파트 광고처럼 '공간 전체가 무대'가 된다.",
     "fpv drone one take commercial"),
    ("bolt", "모션컨트롤 / 로봇암", "Motion Control / Bolt", "🛠 장비 기반",
     "로봇암(볼트)이 프로그래밍된 궤적을 초고속·초정밀 반복. 하이스피드 촬영과 결합된다.",
     "음료 스플래시·코스메틱 파우더 같은 텍스처 샷의 끝판왕. 같은 궤적 반복으로 합성 플레이트 확보 가능.",
     "bolt robot arm high speed commercial"),
    ("dolly", "슬라이더 / 달리", "Slider / Dolly", "🛠 장비 기반",
     "레일 위에서 짧고 정밀하게 미끄러지는 무빙. 제품 테이블탑 촬영의 기본 장비.",
     "제품 샷에 3~5cm의 미세 무빙만 넣어도 '살아있는 컷'이 된다. 정적인 스틸컷 대비 프리미엄 체감 상승.",
     "camera slider dolly product commercial shot"),
    ("dollyzoom", "달리 줌 (버티고)", "Dolly Zoom / Vertigo", "✨ 스페셜",
     "달리 인+줌 아웃(또는 반대)을 동시에 — 피사체는 그대로, 배경만 왜곡되며 현기증 나는 효과.",
     "심리적 반전 순간('이 가격이라고?'), 공간이 왜곡되는 판타지 연출. 한 편에 딱 한 번 쓸 때 가장 세다.",
     "dolly zoom vertigo effect examples"),
    ("whippan", "휩 팬", "Whip Pan", "✨ 스페셜",
     "잔상이 남을 만큼 빠른 팬. 주로 장면 전환(트랜지션)으로 사용.",
     "장소 A→B를 에너지 있게 연결. 비트 드랍에 맞춘 휩 팬 연쇄는 스포츠·패션 광고의 리듬 메이커.",
     "whip pan transition examples film"),
    ("speedramp", "스피드 램프", "Speed Ramp", "✨ 스페셜",
     "한 샷 안에서 슬로모션↔고속을 오가는 속도 변주. 무빙과 편집의 경계에 있는 기법.",
     "액션의 정점만 슬로모션으로 '보여주고' 나머지는 빠르게. 스니커즈·음료 광고 15초 안에 리듬감 만들기.",
     "speed ramp commercial edit examples"),
    ("bullettime", "불릿타임", "Bullet Time", "✨ 스페셜",
     "시간이 멈춘 듯 피사체 주위를 도는 매트릭스식 효과. 멀티캠 어레이나 3D로 구현.",
     "스플래시·점프의 '정지된 순간'을 360°로. 요즘은 AI·3D 스캔으로 저예산 구현도 가능해졌다.",
     "bullet time effect commercial"),
    ("snorricam", "스노리캠", "Snorricam", "✨ 스페셜",
     "카메라를 배우 몸에 고정 — 인물은 고정되고 세상이 흔들리는 1인칭 아닌 1인칭.",
     "혼란·취기·러시 상태 표현. '월요일의 나' 같은 공감형 유머 광고에서 강렬한 한 컷.",
     "snorricam shot examples"),
    ("probe", "프로브 렌즈", "Probe Lens", "✨ 스페셜",
     "가늘고 긴 잠망경형 매크로 렌즈. 피사체 '속으로' 들어가는 초근접 무빙이 가능.",
     "음식·화장품 텍스처의 내부 탐험. F&B 광고에서 소스 사이를 뚫고 지나가는 샷 = 프로브+모션컨트롤.",
     "probe lens macro food commercial"),
    ("oner", "원테이크 / 롱테이크", "Oner / Long Take", "✨ 스페셜",
     "컷 없이 하나의 샷으로 이어가는 연출. 모든 무빙 기법의 종합 예술.",
     "브랜드 세계관을 끊김 없이 체험시키는 최고의 포맷. 치밀한 리허설 필수 — 대신 임팩트는 보장된다.",
     "one take commercial long take ad"),
]

PER_QUERY = 6

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
    out = {"fetchedAt": date.today().isoformat(), "moves": []}
    seen = set()
    for key, name, en, cat, desc, tip, query in MOVES:
        try:
            results = fetch(query)
        except Exception as e:
            print(f"  ! {name} 실패: {e}")
            results = []
        vids = []
        for v in results:
            if v["id"] in seen:
                continue
            seen.add(v["id"])
            vids.append(v)
            if len(vids) >= PER_QUERY:
                break
        out["moves"].append({"key": key, "name": name, "en": en, "cat": cat,
                             "desc": desc, "tip": tip, "videos": vids})
        print(f"  {cat} {name} ({en}) {len(vids)}개")
        time.sleep(0.6)

    try:
        from yt_common import filter_embeddable
        for m in out["moves"]:
            m["videos"] = filter_embeddable(m["videos"])
    except Exception as e:
        print(f"  ! 임베드 검사 생략: {e}")

    dest = Path(__file__).parent / "moves.js"
    dest.write_text("window.TVC_MOVES = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    total = sum(len(m["videos"]) for m in out["moves"])
    print(f"\n완료: {len(out['moves'])}개 무빙, 총 {total}개 영상 → {dest}")

if __name__ == "__main__":
    main()
