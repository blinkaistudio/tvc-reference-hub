# -*- coding: utf-8 -*-
"""글로벌 탑티어 모션/디자인 스튜디오의 공식 Vimeo 최신작 수집 → motionv.js
Vimeo RSS(vimeo.com/{user}/videos/rss) + oEmbed(썸네일/길이/임베드 검증)"""
import sys, json, re, time, html, urllib.request
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
PER = 5
SECTION = "🌀 모션그래픽 스튜디오"

# (이름, vimeo유저명(없으면 None), 부제, 설명, 공식사이트, 유튜브 고정핀 [(id,title,len)])
STUDIOS = [
    ("BUCK", "buck", "세계 1위 모션 디자인 스튜디오 (US)",
     "구글·애플·스포티파이의 단골. 2D/3D를 넘나드는 압도적 크래프트 — 'Good Books: Metamorphosis'는 모션계의 전설.",
     "https://buck.co",
     [("IrzNx1nMqxU", "Good Books – Metamorphosis (전설의 레퍼런스)", "3:03")]),
    ("ManvsMachine", "mvsm", "3D 추상 비주얼의 정점 (UK/US)",
     "나이키·애플 캠페인의 미니멀하고 촉각적인 3D 모션. 제품을 추상 조형으로 승화시키는 대표 스튜디오.",
     "https://mvsm.com", []),
    ("Tendril", "tendril", "디자인 드리븐 CG (CA)",
     "토론토 기반. 빛·재질·유기적 형태 탐구의 끝판왕 — 하이엔드 CG 모션의 무드보드 단골.",
     "https://tendril.ca", []),
    ("The Mill", "millchannel", "VFX·모션의 전설 (UK/US)",
     "광고 VFX의 역사 그 자체(2025년 운영 종료, 아카이브는 영원한 교과서). PlayStation, Nike 등 수천 편의 명작.",
     "https://www.themill.com", []),
    ("Aggressive", "aggressive", "뮤직비디오 DNA의 하이엔드 CG (US)",
     "NY 기반. 대담한 카메라와 CG가 결합된 에너지 — 테크·엔터테인먼트 론칭 필름 전문.",
     "https://aggressive.tv", []),
    ("Oddfellows", "oddfellows", "위트 있는 2D 브랜드 모션 (US)",
     "SF/포틀랜드 기반. 명확한 스토리와 사랑스러운 일러스트 모션 — 테크 브랜드 설명 영상의 정석.",
     "https://oddfellows.tv", []),
    ("Giant Ant", "giantant", "따뜻한 스토리 애니메이션 (CA)",
     "밴쿠버 기반. 손맛 나는 일러스트 모션과 서정적 스토리텔링 — 브랜드 필름의 감성 레퍼런스.",
     "https://giantant.ca", []),
    ("Ordinary Folk", "ordinaryfolk", "감각적인 모션 크래프트 (CA)",
     "JR Canest가 이끄는 스튜디오. 부드러운 이징과 리듬감 — 모션 디자이너들이 프레임 단위로 뜯어보는 작업들.",
     "https://ordinaryfolk.co", []),
    ("Golden Wolf", "goldenwolf", "하이에너지 2D 애니메이션 (UK/US)",
     "스포츠·게임·스트리트 컬처 감성의 폭발적인 2D — ESPN, 나이키, 라이엇게임즈 작업 다수.",
     "https://goldenwolf.tv", []),
    ("Cub Studio", "cubstudio", "유머러스 캐릭터 애니메이션 (UK)",
     "런던 기반. 동글동글한 캐릭터와 능청스러운 유머 — 가볍고 친근한 톤의 브랜드 애니메이션.",
     "https://cubstudio.com", []),
    ("Art&Graft", "artandgraft", "브랜드 애니메이션 크래프트 (UK)",
     "런던 기반. 그래픽 디자인 기반의 정갈한 모션 브랜딩 — BBC, Google 작업.",
     "https://www.artandgraft.com", []),
    ("Nexus Studios", "nexusstudios", "애니메이션+인터랙티브 명가 (UK/US)",
     "아카데미 후보급 애니메이션부터 AR까지 — 스토리텔링 애니메이션의 세계 최정상.",
     "https://nexusstudios.com", []),
    ("Vucko", "vucko", "실험적 모션 디자인 (CA)",
     "Andrew Vucko의 스튜디오. 타이포·리듬·컨셉추얼 모션 실험 — 모던한 브랜드 모션의 트렌드세터.",
     "https://www.vucko.tv", []),
    ("Serial Cut", "serialcut", "아트디렉션 CG (ES)",
     "마드리드 기반. 팝하고 조형적인 CG 아트디렉션 — 키비주얼과 모션을 오가는 이미지 메이킹.",
     "https://www.serialcut.com", []),
    ("Polyester", "polyester", "팝 컬러 2D/3D (CA)",
     "토론토 기반. 비비드한 컬러와 탄력 있는 애니메이션 — 유쾌한 브랜드 캠페인 모션.",
     "https://polyesterstudio.com", []),
    ("Elastic", None, "타이틀 시퀀스의 제왕 (US)",
     "『왕좌의 게임』 오프닝 타이틀의 주인공. 시리즈·영화 메인타이틀 디자인의 최정상.",
     "https://www.elastic.tv",
     [("s7L2PVdrb_8", "Game of Thrones — Main Title (HBO)", "1:46"),
      ("TZE9gVF1QbA", "Game of Thrones S8 — Opening Credits", "2:03")]),
    ("Imaginary Forces", "imaginaryforces", "모션 브랜딩의 원조 (US)",
     "『기묘한 이야기』『매드맨』 타이틀 — 타이포그래피와 내러티브를 결합한 모션 브랜딩의 교과서.",
     "https://www.imaginaryforces.com",
     [("-RcPZdihrp4", "Stranger Things — Title Sequence", "0:48")]),
    ("Territory Studio", "territory", "영화 속 스크린 UI(FUI) 명가 (UK)",
     "『블레이드 러너 2049』『마션』의 홀로그램·인터페이스 그래픽 — 테크 광고 UI 연출 레퍼런스.",
     "https://territorystudio.com",
     [("H07HumKRQKE", "Blade Runner 2049 — UI Reel", "2:11")]),
    ("자이언트스텝", None, "리얼타임 콘텐츠 강자 (KR)",
     "국내 대표 크리에이티브 테크 스튜디오. 리얼타임 엔진 기반 버추얼 프로덕션·XR — SM·삼성 작업 다수.",
     "https://www.giantstep.co.kr",
     [("lsXPCVm0ZXs", "2019 GIANTSTEP VFX REEL", "2:00"),
      ("6X28U3L-93Y", "2020 GIANTSTEP NEW MEDIA REEL", "1:44"),
      ("ZdZLI_au74I", "GIANTSTEP AI PROJECT: SPACE GREEN", "1:30")]),
    ("디스트릭트 (d'strict)", None, "아나몰픽 미디어아트 (KR)",
     "코엑스 'WAVE'로 세계를 놀라게 한 퍼블릭 미디어아트 스튜디오. 초대형 아나몰픽 착시 콘텐츠의 개척자.",
     "https://www.dstrict.com",
     [("CZxKdgiisAU", "Public Media Art \"WAVE\" Full ver.", "1:00"),
      ("OB5NxwEBoIA", "ARTE MUSEUM — WAVE", "2:00"),
      ("ZzxuftgFuoE", "WAVE Short ver.", "0:30")]),
]


def get(url, timeout=20):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def rss_videos(user):
    """공식 계정 최신 영상 [(id, title)]"""
    body = get(f"https://vimeo.com/{user}/videos/rss")
    out = []
    for item in re.findall(r"<item>(.*?)</item>", body, re.DOTALL):
        t = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
        l = re.search(r"<link>https://vimeo\.com/(\d+)</link>", item)
        if t and l:
            title = html.unescape(re.sub(r"\s+", " ", t.group(1)).strip())
            out.append((l.group(1), title))
    return out


def oembed(vid):
    """임베드 검증 + 썸네일/길이"""
    try:
        data = json.loads(get(f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{vid}&width=640", timeout=15))
        dur = data.get("duration") or 0
        length = f"{dur // 60}:{dur % 60:02d}" if dur else ""
        return {"thumb": data.get("thumbnail_url", ""), "len": length}
    except Exception:
        return None


def main():
    out = {"fetchedAt": date.today().isoformat(), "entries": []}
    for name, user, sub, desc, site, pins in STUDIOS:
        videos = [{"id": vid, "title": t, "len": ln, "platform": "youtube"} for vid, t, ln in pins]
        if user:
            try:
                cands = rss_videos(user)
            except Exception as e:
                print(f"  ! {name} ({user}) RSS 실패: {e}")
                cands = []
            # 소소한 잡음 제거: BTS/케이스스터디/프로세스 영상은 뒤로
            cands.sort(key=lambda x: any(k in x[1].lower() for k in ("process", "behind", "bts", "breakdown", "case study")))
            with ThreadPoolExecutor(max_workers=8) as ex:
                metas = list(ex.map(lambda c: (c, oembed(c[0])), cands[:PER * 2]))
            for (vid, title), meta in metas:
                if meta and len(videos) < PER + len(pins):
                    videos.append({"id": vid, "title": title, "len": meta["len"],
                                   "platform": "vimeo", "thumb": meta["thumb"]})
        out["entries"].append({
            "section": SECTION, "name": name, "sub": sub, "desc": desc,
            "links": ([{"label": "공식 사이트", "url": site}] +
                      ([{"label": "Vimeo 포트폴리오", "url": f"https://vimeo.com/{user}"}] if user else [])),
            "videos": videos,
        })
        nv = sum(1 for v in videos if v["platform"] == "vimeo")
        print(f"  {name}: vimeo {nv}개 + 핀 {len(pins)}개")
        time.sleep(0.3)

    out["entries"] = [e for e in out["entries"] if e["videos"]]
    dest = Path(__file__).parent / "motionv.js"
    dest.write_text("window.TVC_MOTION = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    total = sum(len(e["videos"]) for e in out["entries"])
    print(f"\n완료: {len(out['entries'])}개 스튜디오, 총 {total}개 영상 → {dest}")


if __name__ == "__main__":
    main()
