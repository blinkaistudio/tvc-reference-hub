# -*- coding: utf-8 -*-
"""힙 스튜디오 100+ — 검증된 Vimeo 계정에서 최신작 수집 → hip.js"""
import sys, json, re, time, html, urllib.request
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
PER = 6

# 전수 탐색으로 계정 실존+본인 확인 완료된 목록 (이름, 카테고리, vimeo 유저명)
VIMEO_STUDIOS = [
    # ---- 모션/디자인 ----
    ("BUCK", "모션/디자인", "buck"), ("ManvsMachine", "모션/디자인", "mvsm"),
    ("Tendril", "모션/디자인", "tendril"), ("Golden Wolf", "모션/디자인", "goldenwolf"),
    ("Giant Ant", "모션/디자인", "giantant"), ("Ordinary Folk", "모션/디자인", "ordinaryfolk"),
    ("Oddfellows", "모션/디자인", "oddfellows"), ("Cub Studio", "모션/디자인", "cubstudio"),
    ("Art&Graft", "모션/디자인", "artandgraft"), ("Vucko", "모션/디자인", "vucko"),
    ("Hobbes", "모션/디자인", "hobbes"), ("State Design", "모션/디자인", "statedesign"),
    ("Sarofsky", "모션/디자인", "sarofsky"), ("Brand New School", "모션/디자인", "brandnewschool"),
    ("Psyop", "모션/디자인", "psyop"), ("We Are Royale", "모션/디자인", "weareroyale"),
    ("Shilo", "모션/디자인", "shilo"), ("Trollbäck+Company", "모션/디자인", "trollback"),
    ("Block & Tackle", "모션/디자인", "blockandtackle"), ("loyalkaspar", "모션/디자인", "loyalkaspar"),
    ("Alma Mater", "모션/디자인", "almamater"), ("FutureDeluxe", "모션/디자인", "futuredeluxe"),
    ("Builders Club", "모션/디자인", "buildersclub"), ("Ranger & Fox", "모션/디자인", "rangerandfox"),
    ("Mighty Nice", "모션/디자인", "mightynice"), ("Assembly", "모션/디자인", "assemblyltd"),
    ("Yukfoo", "모션/디자인", "yukfoo"), ("WIZZ", "모션/디자인", "wizzdesign"),
    ("Blackmeal", "모션/디자인", "blackmeal"), ("ILLO", "모션/디자인", "illo"),
    ("Dress Code", "모션/디자인", "dresscode"), ("Polyester", "모션/디자인", "polyester"),
    ("Serial Cut", "모션/디자인", "serialcut"), ("DVEIN", "모션/디자인", "dvein"),
    ("Zeitguised", "모션/디자인", "zeitguised"), ("Studio Dumbar", "모션/디자인", "studiodumbar"),
    ("Nerdo", "모션/디자인", "nerdo"), ("Dadomani", "모션/디자인", "dadomani"),
    ("Device", "모션/디자인", "device"), ("Roof Studio", "모션/디자인", "roofstudio"),
    ("Buda.tv", "모션/디자인", "budatv"), ("The Panics", "모션/디자인", "thepanics"),
    ("Vallée Duhamel", "모션/디자인", "valleeduhamel"), ("Optical Arts", "모션/디자인", "opticalarts"),
    ("Panoply", "모션/디자인", "panoply"), ("Bien", "모션/디자인", "bien"),
    ("Wednesday Studio", "모션/디자인", "wednesdaystudio"), ("Whitelight Motion", "모션/디자인", "whitelightmotion"),
    # 3차 웨이브 (probe_wave3.py 검증 완료)
    ("Gretel", "모션/디자인", "gretel"), ("Method Studios", "모션/디자인", "methodstudios"),
    ("Wonderlust", "모션/디자인", "wonderlust"), ("IV Studio", "모션/디자인", "ivstudio"),
    ("The Furrow", "모션/디자인", "thefurrow"), ("Slanted Studios", "모션/디자인", "slantedstudios"),
    ("Nomint", "모션/디자인", "nomint"), ("Moving Brands", "모션/디자인", "movingbrands"),
    ("Zelig", "모션/디자인", "zeligstudio"),
    # ---- CG/VFX ----
    ("The Mill", "CG/VFX", "millchannel"), ("Framestore", "CG/VFX", "framestore"),
    ("Analog", "CG/VFX", "analogstudio"), ("Electric Theatre Collective", "CG/VFX", "electrictheatre"),
    ("Time Based Arts", "CG/VFX", "timebasedarts"), ("Platige Image", "CG/VFX", "platige"),
    ("Ars Thanea", "CG/VFX", "arsthanea"), ("Aggressive", "CG/VFX", "aggressive"),
    ("Perception", "CG/VFX", "experienceperception"), ("Territory Studio", "CG/VFX", "territory"),
    ("Zombie Studio", "CG/VFX", "zombiestudio"),
    ("RISE FX", "CG/VFX", "risefx"), ("Blacksmith VFX", "CG/VFX", "blacksmithvfx"),
    ("Mathematic", "CG/VFX", "mathematicstudio"), ("Axis Studios", "CG/VFX", "axisstudios"),
    ("Mikros Animation", "CG/VFX", "mikrosanimation"), ("ILP (Important Looking Pirates)", "CG/VFX", "ilpvfx"),
    # ---- 애니메이션 ----
    ("Nexus Studios", "애니메이션", "nexusstudios"), ("Passion Pictures", "애니메이션", "passionpictures"),
    ("Moth Studio", "애니메이션", "mothstudio"), ("Le Cube", "애니메이션", "lecube"),
    ("2veinte", "애니메이션", "2veinte"), ("Plenty", "애니메이션", "plenty"),
    ("Punga", "애니메이션", "punga"), ("Bito", "애니메이션", "bito"),
    ("Not To Scale", "애니메이션", "nottoscale"), ("Titmouse", "애니메이션", "titmouse"),
    ("Aardman", "애니메이션", "aardman"), ("Studio AKA", "애니메이션", "studioaka"),
    ("Strange Beast", "애니메이션", "strangebeast"), ("Animade", "애니메이션", "animadetv"),
    ("Job, Joris & Marieke", "애니메이션", "jobjorisenmarieke"),
    ("The Line", "애니메이션", "thelineanimation"), ("Sun Creature", "애니메이션", "suncreature"),
    ("Rubber House", "애니메이션", "rubberhouse"),
    # ---- 타이틀/브랜딩 ----
    ("Imaginary Forces", "타이틀/브랜딩", "imaginaryforces"), ("Prologue Films", "타이틀/브랜딩", "prologuefilms"),
    ("Filmograph", "타이틀/브랜딩", "filmograph"), ("Digital Kitchen", "타이틀/브랜딩", "digitalkitchen"),
    # ---- 라이브액션 ----
    ("Somesuch", "라이브액션", "somesuch"), ("Riff Raff Films", "라이브액션", "riffrafffilms"),
    ("Rogue Films", "라이브액션", "roguefilms"), ("Caviar", "라이브액션", "caviarcontent"),
    ("Hungry Man", "라이브액션", "hungrymantv"), ("Iconoclast", "라이브액션", "iconoclastimage"),
    ("Megaforce", "라이브액션", "megaforce"), ("CANADA", "라이브액션", "canadalondon"),
    ("DIVISION", "라이브액션", "division"), ("SOLAB", "라이브액션", "solab"),
    ("Lief", "라이브액션", "lief"), ("Agile Films", "라이브액션", "agilefilms"),
    ("Knucklehead", "라이브액션", "knucklehead"), ("FRIEND", "라이브액션", "friendlondon"),
    ("BWGTBLD", "라이브액션", "bwgtbld"), ("Academy Films", "라이브액션", "academy"),
    ("Superprime", "라이브액션", "superprime"), ("The Directors Bureau", "라이브액션", "thedirectorsbureau"),
    ("Scoundrel", "라이브액션", "scoundrelfilms"), ("Exit Films", "라이브액션", "exitfilms"),
    ("Blink Productions", "라이브액션", "blinkprods"), ("New Land", "라이브액션", "newland"),
    # ---- 미디어아트 ----
    ("Universal Everything", "미디어아트", "universaleverything"), ("FIELD.IO", "미디어아트", "field"),
    ("Sila Sveta", "미디어아트", "silasveta"), ("Moment Factory", "미디어아트", "momentfactory"),
    ("onformative", "미디어아트", "onformative"), ("Random Studio", "미디어아트", "randomstudio"),
    ("WOW inc.", "미디어아트", "wowinc"),
    ("teamLab", "미디어아트", "teamlab"), ("Nohlab", "미디어아트", "nohlab"),
    ("Ouchhh", "미디어아트", "ouchhh"), ("Marshmallow Laser Feast", "미디어아트", "marshmallowlaserfeast"),
    ("AntiVJ", "미디어아트", "antivj"),
]

# 국내 (Vimeo 미활동 → YouTube 채널 RSS / 고정핀)
KR_YT = [
    ("돌고래유괴단", "라이브액션", "UCUsLcIQq0poAfOxRyJbxlLA"),
    ("스튜디오좋", "라이브액션", "UCxFdgtAN5xWDpsfvyJVUWLw"),
]
KR_PINS = [
    ("자이언트스텝", "CG/VFX", [("lsXPCVm0ZXs", "2019 GIANTSTEP VFX REEL", "2:00"),
                                ("6X28U3L-93Y", "2020 GIANTSTEP NEW MEDIA REEL", "1:44"),
                                ("ZdZLI_au74I", "GIANTSTEP AI PROJECT: SPACE GREEN", "1:30")]),
    ("디스트릭트 (d'strict)", "미디어아트", [("CZxKdgiisAU", "Public Media Art \"WAVE\" Full ver.", "1:00"),
                                            ("OB5NxwEBoIA", "ARTE MUSEUM — WAVE", "2:00"),
                                            ("ZzxuftgFuoE", "WAVE Short ver.", "0:30")]),
]


def get(url, timeout=18):
    req = urllib.request.Request(url, headers=H)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def vimeo_rss(user):
    body = get(f"https://vimeo.com/{user}/videos/rss")
    out = []
    for item in re.findall(r"<item>(.*?)</item>", body, re.DOTALL):
        t = re.search(r"<title>(.*?)</title>", item, re.DOTALL)
        l = re.search(r"<link>https://vimeo\.com/(\d+)</link>", item)
        if t and l:
            out.append((l.group(1), html.unescape(re.sub(r"\s+", " ", t.group(1)).strip())))
    return out


def vimeo_oembed(vid):
    try:
        d = json.loads(get(f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{vid}&width=640", 12))
        dur = d.get("duration") or 0
        return {"thumb": d.get("thumbnail_url", ""), "len": f"{dur // 60}:{dur % 60:02d}" if dur else ""}
    except Exception:
        return None


def yt_rss(channel_id):
    body = get(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    out = []
    for entry in re.findall(r"<entry>(.*?)</entry>", body, re.DOTALL):
        vid = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", entry)
        title = re.search(r"<title>([^<]*)</title>", entry)
        if vid and title:
            out.append({"id": vid.group(1), "title": html.unescape(title.group(1)),
                        "len": "", "platform": "youtube"})
    return out


def collect_vimeo(name, cat, user):
    try:
        cands = vimeo_rss(user)
    except Exception as e:
        return {"name": name, "cat": cat, "user": user, "videos": [], "err": str(e)}
    # 릴/신작 우선, BTS·프로세스 뒤로
    cands.sort(key=lambda x: any(k in x[1].lower() for k in ("process", "behind", "bts", "breakdown", "making of")))
    videos = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        metas = list(ex.map(lambda c: (c, vimeo_oembed(c[0])), cands[:PER + 3]))
    for (vid, title), meta in metas:
        if meta and len(videos) < PER:
            videos.append({"id": vid, "title": title, "len": meta["len"],
                           "platform": "vimeo", "thumb": meta["thumb"]})
    return {"name": name, "cat": cat, "user": user, "videos": videos}


def main():
    out = {"fetchedAt": date.today().isoformat(), "studios": []}
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda s: collect_vimeo(*s), VIMEO_STUDIOS))
    for r in results:
        if r.get("err"):
            print(f"  ! {r['name']}: {r['err']}")
        r.pop("err", None)
        if r["videos"]:
            r["url"] = f"https://vimeo.com/{r['user']}"
            out["studios"].append(r)
            print(f"  {r['name']}: {len(r['videos'])}개")
    for name, cat, cid in KR_YT:
        try:
            vids = yt_rss(cid)[:PER]
        except Exception as e:
            print(f"  ! {name}: {e}")
            continue
        out["studios"].append({"name": name, "cat": cat, "user": "",
                               "url": f"https://www.youtube.com/channel/{cid}", "videos": vids})
        print(f"  {name}: {len(vids)}개 (YouTube)")
    for name, cat, pins in KR_PINS:
        out["studios"].append({"name": name, "cat": cat, "user": "", "url": "",
                               "videos": [{"id": i, "title": t, "len": l, "platform": "youtube"} for i, t, l in pins]})
        print(f"  {name}: {len(pins)}개 (고정핀)")

    dest = Path(__file__).parent / "hip.js"
    dest.write_text("window.TVC_HIP = " + json.dumps(out, ensure_ascii=False) + ";", encoding="utf-8")
    total = sum(len(s["videos"]) for s in out["studios"])
    print(f"\n완료: 스튜디오 {len(out['studios'])}곳, 영상 {total}개 → {dest}")


if __name__ == "__main__":
    main()
