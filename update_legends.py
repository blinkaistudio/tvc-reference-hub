# -*- coding: utf-8 -*-
"""유명 프로덕션 / 디렉터 / 큐레이션 채널 레퍼런스 수집 → legends.js (임베드 가능 영상만)"""
import sys, json, time
from datetime import date
from pathlib import Path
from yt_common import search_videos, filter_embeddable

sys.stdout.reconfigure(encoding="utf-8")

PER = 5

# 검수에서 걸러낸 정크 영상 (재수집 시 자동 제외)
BLOCKED_IDS = ['2Kji_xZlCgw', '5osZk9Mw94w', '8lo9YIAWzGM', '8xk3AzcLZBM', 'EezwSH_mQ_0', 'Kdi0I6YnbUI', 'OzUnqQk4eOg', 'YyXn7pNDcL4', 'fYeqlml_SVs', 'gFTYNp0HWTg', 'iyQIlVuqxCQ', 'n0wYovVRoE4', 'npoFNsmk2RY', 'oWeFw5ZZpcg', 'rCYMJ5cMdfg', 'uXZd_W5B7N0', 'vwmQ3_pRbZk', 'xLXx71a-1Wk', 'xXRwPjynMwA', 'yfcy0TXpJhU']

# (섹션, 이름, 부제, 설명, 링크[(라벨,URL)], 검색어 목록 — 대표작을 직접 검색해 잡음 차단)
ENTRIES = [
    # ---------- 글로벌 프로덕션 ----------
    ("🏭 글로벌 프로덕션", "Hungry Man", "코미디 커머셜의 명가 (US/UK)",
     "'웃기는데 완성도 높은' 광고의 대명사. Bryan Buckley(역대 슈퍼볼 최다 연출) 등 코미디 거장 디렉터 군단.",
     [("공식 사이트", "https://hungryman.com")],
     ["ESPN This is SportsCenter funny commercial",
      "Bryan Buckley Super Bowl commercial director"]),
    ("🏭 글로벌 프로덕션", "MJZ", "블록버스터급 스케일 (US)",
     "슈퍼볼 대작과 시네마틱 캠페인의 산실. Old Spice, Sony Bravia 등 광고사(史)급 캠페인 다수.",
     [("공식 사이트", "https://www.mjz.com")],
     ["Old Spice The Man Your Man Could Smell Like",
      "Sony Bravia Balls commercial San Francisco",
      "Nike Take It To The Next Level commercial"]),
    ("🏭 글로벌 프로덕션", "Smuggler", "스토리텔링 강자 (US/UK)",
     "감정을 건드리는 내러티브 광고의 최전선. 칸 라이언즈 '올해의 프로덕션' 다수 수상.",
     [("공식 사이트", "https://smugglersite.com")],
     ["Apple Underdogs The Whole Working From Home Thing",
      "Mark Molloy commercial director"]),
    ("🏭 글로벌 프로덕션", "Biscuit Filmworks", "휴먼 코미디 & 크래프트 (US)",
     "Noam Murro가 이끄는 프로덕션. 절제된 유머와 정교한 미장센 — 카피 없이 상황으로 웃기는 광고들.",
     [("공식 사이트", "https://www.biscuitfilmworks.com")],
     ["Southern Comfort Beach Whatever's Comfortable commercial",
      "Noam Murro commercial director"]),
    ("🏭 글로벌 프로덕션", "Somesuch", "컬처를 만드는 프로덕션 (UK/US)",
     "Nike 'Dream Crazier', Libresse 'Viva La Vulva' 등 사회적 임팩트와 크래프트를 동시에. Kim Gehrig의 홈.",
     [("공식 사이트", "https://somesuch.co")],
     ["Nike Dream Crazier commercial",
      "Viva La Vulva Libresse commercial",
      "This Girl Can campaign film"]),
    ("🏭 글로벌 프로덕션", "Iconoclast", "뮤직비디오 DNA의 하이패션 필름 (FR)",
     "Romain Gavras 등 프랑스 비주얼리스트 군단. 압도적 스케일과 에너지의 브랜드 필름 — 패션·스포츠 캠페인 강자.",
     [("공식 사이트", "https://iconoclast.tv")],
     ["adidas Your Future Is Not Mine commercial",
      "Jacquemus Guirlande campaign film",
      "Kenzo World film"]),
    ("🏭 글로벌 프로덕션", "Megaforce", "프랑스식 아이디어 폭발 (FR)",
     "4인조 디렉터 콜렉티브. Burberry 'Open Spaces' 등 — 중력을 무시하는 상상력과 원테이크 연출.",
     [("공식 사이트", "https://www.megaforce.fr")],
     ["Burberry Open Spaces film",
      "Megaforce directed music video commercial"]),
    ("🏭 글로벌 프로덕션", "Park Pictures", "시네마 크래프트 (US)",
     "Lance Acord(『Lost in Translation』 촬영) 공동설립. VW 'The Force' 같은 필름 룩과 절제된 감성의 정점.",
     [("공식 사이트", "https://parkpictures.com")],
     ["Volkswagen The Force commercial",
      "Lance Acord commercial director"]),
    # ---------- 국내 프로덕션 ----------
    ("🇰🇷 국내 프로덕션", "돌고래유괴단", "B급과 시네마틱을 오가는 국내 최강 화제성",
     "신우석 감독의 프로덕션. NewJeans 'Ditto' MV부터 바이럴 광고까지 — '광고 같지 않은 광고'로 매번 화제의 중심.",
     [("공식 사이트", "https://www.dolphiners.com")],
     ["돌고래유괴단 광고",
      "돌고래유괴단 신우석 광고",
      "NewJeans Ditto MV"]),
    ("🇰🇷 국내 프로덕션", "스튜디오좋", "세계관 광고의 개척자",
     "빙그레 '빙그레우스' 세계관 캠페인의 주인공. 브랜드에 서사와 캐릭터를 심는 국내 대표 크리에이티브 스튜디오.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=스튜디오좋+광고")],
     ["스튜디오좋 광고",
      "빙그레우스 빙그레 광고"]),
    # ---------- 레전드 디렉터 ----------
    ("🎬 레전드 디렉터", "Romain Gavras", "폭발하는 에너지 (FR)",
     "군중·화염·슬로모션의 마스터. adidas 'Your Future Is Not Mine', M.I.A 'Bad Girls' — 스케일로 압도하는 연출.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Romain+Gavras+commercial")],
     ["Romain Gavras commercial",
      "MIA Bad Girls official video"]),
    ("🎬 레전드 디렉터", "Jonathan Glazer", "광고를 예술로 (UK)",
     "Guinness 'Surfer'(역대 최고 광고 단골 1위) — 이후 『Under the Skin』 등 영화 거장으로.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Jonathan+Glazer+commercial")],
     ["Guinness Surfer commercial 1999",
      "Jonathan Glazer commercial"]),
    ("🎬 레전드 디렉터", "Spike Jonze", "기발함의 대명사 (US)",
     "IKEA 'Lamp', Kenzo World, Apple 'Welcome Home' — 춤·감정·유머를 자유자재로 섞는 연출.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Spike+Jonze+commercial")],
     ["IKEA Lamp commercial Spike Jonze",
      "Kenzo World film Spike Jonze",
      "Apple HomePod Welcome Home Spike Jonze"]),
    ("🎬 레전드 디렉터", "Michel Gondry", "수공예 이미지네이션 (FR)",
     "Levi's 'Drugstore', Smirnoff 'Smarienberg' — CG 대신 아이디어와 인카메라 트릭으로 마법을 만드는 감독.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Michel+Gondry+commercial")],
     ["Levis Drugstore commercial Michel Gondry",
      "Michel Gondry commercial"]),
    ("🎬 레전드 디렉터", "Tom Kuntz", "데드팬 코미디의 왕 (US)",
     "Old Spice 'The Man Your Man Could Smell Like', Skittles 다수 — 무표정한 얼굴로 세상에서 제일 웃긴 광고를 만든다.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Tom+Kuntz+commercial")],
     ["Old Spice The Man Your Man Could Smell Like",
      "Skittles funny commercial Tom Kuntz"]),
    ("🎬 레전드 디렉터", "Dougal Wilson", "감동 스토리텔링 (UK)",
     "John Lewis 'Monty the Penguin', 'The Long Wait' — 크리스마스마다 영국을 울리는 그 광고들의 감독.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Dougal+Wilson+advert")],
     ["John Lewis Monty the Penguin advert",
      "John Lewis The Long Wait advert",
      "Three pony advert dancing"]),
    ("🎬 레전드 디렉터", "Andreas Nilsson", "기묘한 유머 (SE)",
     "Volvo Trucks 'Epic Split'(반담 다리찢기) — 조회수 신화. 진지한 얼굴의 초현실 코미디.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Andreas+Nilsson+commercial")],
     ["Volvo Trucks Epic Split Van Damme",
      "Andreas Nilsson commercial director"]),
    ("🎬 레전드 디렉터", "Nicolai Fuglsig", "한 컷의 장관 (DK)",
     "Sony Bravia 'Balls'(샌프란시스코 언덕의 25만 개 슈퍼볼) — 리얼 스펙터클 연출의 교과서.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Nicolai+Fuglsig+commercial")],
     ["Sony Bravia Balls commercial",
      "Nicolai Fuglsig commercial"]),
    ("🎬 레전드 디렉터", "Ian Pons Jewell", "초현실 비주얼 트립 (UK)",
     "Nike 'Nothing Beats a Londoner' — 장면이 꼬리를 무는 체이닝 연출의 대가.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Ian+Pons+Jewell+commercial")],
     ["Nike Nothing Beats a Londoner",
      "Ian Pons Jewell commercial"]),
    ("🎬 레전드 디렉터", "Kim Gehrig", "대담한 컬처 캠페인 (UK)",
     "Nike 'Dream Crazier', Apple 'The Greatest' — 시대의 메시지를 크래프트에 담는 연출.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Kim+Gehrig+commercial")],
     ["Nike Dream Crazier commercial",
      "Apple The Greatest accessibility film",
      "Kim Gehrig commercial"]),
    # ---------- 큐레이션 채널 ---------- (모션그래픽 스튜디오는 update_vimeo.py가 담당)
    ("📺 큐레이션 채널", "Amazing Ads", "칸 수상작 케이스 스터디",
     "칸 라이언즈 그랑프리 수상작들의 케이스 필름을 꾸준히 올리는 채널 — 수상작 훑기에 최적.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Amazing+Ads+Cannes+Grand+Prix")],
     ["Amazing Ads Cannes Lions Grand Prix case study"]),
    ("📺 큐레이션 채널", "The Hall of Advertising", "역대 명작 광고 아카이브",
     "연도·국가별 클래식 광고를 원본 화질로 보존하는 아카이브 채널. 레트로 레퍼런스 보물창고.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=The+Hall+of+Advertising")],
     ["The Hall of Advertising classic commercial"]),
    ("📺 큐레이션 채널", "JP Ad Play", "일본 최신 CM 큐레이션",
     "일본 온에어 CM을 셀럽·브랜드별로 빠르게 모아주는 채널 — 일본 트렌드 파악용.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=JP+Ad+Play+CM")],
     ["JP Ad Play 最新CM"]),
    ("📺 큐레이션 채널", "Commercial Archivist", "미국 온에어 광고 기록",
     "지금 미국 TV에서 나오는 광고를 브랜드별로 아카이빙 — 실전 온에어 트렌드 체크.",
     [("유튜브 검색", "https://www.youtube.com/results?search_query=Commercial+Archivist")],
     ["Commercial Archivist commercial 2026"]),
]


def main():
    out = {"fetchedAt": date.today().isoformat(), "entries": []}
    for sec, name, sub, desc, links, queries in ENTRIES:
        # 대표작 쿼리별 상위 2개씩 → 잡음 최소화
        uniq, seen = [], set()
        for q in queries:
            try:
                results = search_videos(q)
            except Exception as e:
                print(f"  ! {name} / {q} 검색 실패: {e}")
                continue
            n = 0
            for v in results:
                if v["id"] in seen:
                    continue
                seen.add(v["id"])
                uniq.append(v)
                n += 1
                if n >= 3:
                    break
            time.sleep(0.3)
        uniq = [v for v in uniq if v['id'] not in BLOCKED_IDS]
        ok = filter_embeddable(uniq)[:PER]
        out["entries"].append({"section": sec, "name": name, "sub": sub, "desc": desc,
                               "links": [{"label": l, "url": u} for l, u in links],
                               "videos": ok})
        print(f"  {sec} {name}: {len(ok)}개 (후보 {len(uniq[:PER*3])}개 중 임베드 가능만)")
        time.sleep(0.4)

    dest = Path(__file__).parent / "legends.js"
    dest.write_text("window.TVC_LEGENDS = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    total = sum(len(e["videos"]) for e in out["entries"])
    print(f"\n완료: {len(out['entries'])}개 항목, 총 {total}개 영상 → {dest}")


if __name__ == "__main__":
    main()
