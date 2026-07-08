# -*- coding: utf-8 -*-
"""힙 스튜디오 후보들의 Vimeo 계정 전수 탐색 → hip_probe_result.json"""
import sys, json, re, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}

# (표시명, 카테고리, [계정 후보들])
CANDIDATES = [
    # ---- 모션/디자인 ----
    ("BUCK", "모션/디자인", ["buck"]),
    ("ManvsMachine", "모션/디자인", ["mvsm"]),
    ("Tendril", "모션/디자인", ["tendril"]),
    ("Golden Wolf", "모션/디자인", ["goldenwolf"]),
    ("Giant Ant", "모션/디자인", ["giantant"]),
    ("Ordinary Folk", "모션/디자인", ["ordinaryfolk"]),
    ("Oddfellows", "모션/디자인", ["oddfellows"]),
    ("Cub Studio", "모션/디자인", ["cubstudio"]),
    ("Art&Graft", "모션/디자인", ["artandgraft"]),
    ("Vucko", "모션/디자인", ["vucko"]),
    ("Gunner", "모션/디자인", ["gunner", "gunnerinc"]),
    ("Hobbes", "모션/디자인", ["hobbes", "hobbesdesign"]),
    ("State Design", "모션/디자인", ["statedesign", "state"]),
    ("Sarofsky", "모션/디자인", ["sarofsky"]),
    ("Brand New School", "모션/디자인", ["brandnewschool"]),
    ("Psyop", "모션/디자인", ["psyop"]),
    ("Hornet", "모션/디자인", ["hornetinc", "hornet"]),
    ("Laundry", "모션/디자인", ["laundry", "laundrydesign"]),
    ("Royale", "모션/디자인", ["weareroyale", "royale"]),
    ("Shilo", "모션/디자인", ["shilo", "shilodesign"]),
    ("Blind", "모션/디자인", ["blind", "blindinc"]),
    ("Trollbäck+Company", "모션/디자인", ["trollback", "trollbackco"]),
    ("Block & Tackle", "모션/디자인", ["blockandtackle", "blocktackle"]),
    ("loyalkaspar", "모션/디자인", ["loyalkaspar"]),
    ("Alma Mater", "모션/디자인", ["almamater", "almamaterny"]),
    ("MK12", "모션/디자인", ["mk12"]),
    ("FutureDeluxe", "모션/디자인", ["futuredeluxe"]),
    ("Builders Club", "모션/디자인", ["buildersclub", "builders-club"]),
    ("weareseventeen", "모션/디자인", ["weareseventeen"]),
    ("Ranger & Fox", "모션/디자인", ["rangerandfox"]),
    ("Mighty Nice", "모션/디자인", ["mightynice"]),
    ("Assembly", "모션/디자인", ["assemblyltd", "assembly"]),
    ("Yukfoo", "모션/디자인", ["yukfoo"]),
    ("Wizz", "모션/디자인", ["wizzdesign", "wizz"]),
    ("Blackmeal", "모션/디자인", ["blackmeal"]),
    ("ILLO", "모션/디자인", ["illo", "illostudio"]),
    ("Dress Code", "모션/디자인", ["dresscodeny", "dresscode"]),
    ("Polyester", "모션/디자인", ["polyester"]),
    ("Serial Cut", "모션/디자인", ["serialcut"]),
    ("DVEIN", "모션/디자인", ["dvein"]),
    ("Six N. Five", "모션/디자인", ["sixnfive"]),
    ("Zeitguised", "모션/디자인", ["zeitguised"]),
    ("Found Studio", "모션/디자인", ["foundstudio", "found-studio", "wearefound"]),
    ("Gentleman Scholar", "모션/디자인", ["gentlemanscholar", "gentleman-scholar", "wearescholar"]),
    # ---- CG/VFX ----
    ("The Mill", "CG/VFX", ["millchannel"]),
    ("Framestore", "CG/VFX", ["framestore"]),
    ("Untold Studios", "CG/VFX", ["untoldstudios"]),
    ("Analog", "CG/VFX", ["analogstudio", "analog"]),
    ("Electric Theatre Collective", "CG/VFX", ["electrictheatre", "wearetheetc"]),
    ("Coffee & TV", "CG/VFX", ["coffeeandtv"]),
    ("Time Based Arts", "CG/VFX", ["timebasedarts"]),
    ("Platige Image", "CG/VFX", ["platige"]),
    ("Ars Thanea", "CG/VFX", ["arsthanea"]),
    ("Aggressive", "CG/VFX", ["aggressive"]),
    ("Zombie Studio", "CG/VFX", ["zombiestudio"]),
    ("Perception", "CG/VFX", ["perception", "experienceperception"]),
    ("Territory Studio", "CG/VFX", ["territory"]),
    # ---- 애니메이션 ----
    ("Nexus Studios", "애니메이션", ["nexusstudios"]),
    ("Passion Pictures", "애니메이션", ["passionpictures", "passionanimation"]),
    ("Blinkink", "애니메이션", ["blinkink"]),
    ("Moth", "애니메이션", ["mothcollective", "mothstudio"]),
    ("Animade", "애니메이션", ["animade"]),
    ("Le Cube", "애니메이션", ["lecube", "wearelecube"]),
    ("2veinte", "애니메이션", ["2veinte"]),
    ("Plenty", "애니메이션", ["plenty", "weareplenty"]),
    ("Punga", "애니메이션", ["punga"]),
    ("Lobo", "애니메이션", ["lobo", "lobocc"]),
    ("Bito", "애니메이션", ["bito", "bitostudio"]),
    ("Not To Scale", "애니메이션", ["nottoscale"]),
    ("Titmouse", "애니메이션", ["titmouse"]),
    ("Golden Frog?스킵", "애니메이션", []),
    # ---- 타이틀/브랜딩 ----
    ("Elastic", "타이틀/브랜딩", ["elastictv", "elastic"]),
    ("Imaginary Forces", "타이틀/브랜딩", ["imaginaryforces"]),
    ("Prologue", "타이틀/브랜딩", ["prologuefilms", "prologue"]),
    ("Filmograph", "타이틀/브랜딩", ["filmograph"]),
    ("yU+co", "타이틀/브랜딩", ["yuco", "yu-co"]),
    ("Digital Kitchen", "타이틀/브랜딩", ["digitalkitchen", "dkny?no"]),
    ("Antibody", "타이틀/브랜딩", ["antibody"]),
    # ---- 라이브액션 프로덕션 ----
    ("Somesuch", "라이브액션", ["somesuch"]),
    ("Riff Raff Films", "라이브액션", ["riffrafffilms", "riffraff"]),
    ("Pulse Films", "라이브액션", ["pulsefilms"]),
    ("Object & Animal", "라이브액션", ["objectanimal", "object-animal"]),
    ("Academy Films", "라이브액션", ["academyfilms"]),
    ("Rogue Films", "라이브액션", ["roguefilms"]),
    ("Stink Films", "라이브액션", ["stinkfilms", "stink"]),
    ("Caviar", "라이브액션", ["caviarcontent", "caviar"]),
    ("PRETTYBIRD", "라이브액션", ["prettybird"]),
    ("Epoch Films", "라이브액션", ["epochfilms", "epoch"]),
    ("Biscuit Filmworks", "라이브액션", ["biscuitfilmworks", "biscuit"]),
    ("SMUGGLER", "라이브액션", ["smuggler", "smugglersite"]),
    ("Hungry Man", "라이브액션", ["hungryman", "hungrymantv"]),
    ("MJZ", "라이브액션", ["mjz", "mjzhouse"]),
    ("Park Pictures", "라이브액션", ["parkpictures"]),
    ("Iconoclast", "라이브액션", ["iconoclast", "iconoclastimage"]),
    ("Megaforce", "라이브액션", ["megaforce"]),
    ("CANADA", "라이브액션", ["canadalondon", "lawebdecanada"]),
    ("Division", "라이브액션", ["division", "divisionparis"]),
    ("SOLAB", "라이브액션", ["solab", "solabpictures"]),
    ("Lief", "라이브액션", ["lief", "liefldn"]),
    ("Agile Films", "라이브액션", ["agilefilms"]),
    ("Knucklehead", "라이브액션", ["knucklehead"]),
    ("Arts & Sciences", "라이브액션", ["artsandsciences", "arts-sciences"]),
    ("Love Song", "라이브액션", ["lovesong", "lovesongfilms"]),
]


def probe(user):
    try:
        req = urllib.request.Request(f"https://vimeo.com/{user}/videos/rss", headers=H)
        body = urllib.request.urlopen(req, timeout=12).read().decode("utf-8", "ignore")
        t = re.search(r"<title>Vimeo / (.*?)(?:['’]s videos)?</title>", body)
        n = len(re.findall(r"<item>", body))
        return user, (t.group(1).strip() if t else "?"), n
    except Exception:
        return user, None, 0


def norm(s):
    return re.sub(r"[^a-z0-9가-힣]", "", s.lower())


def main():
    tasks = []
    for name, cat, users in CANDIDATES:
        for u in users:
            if "?" not in u:
                tasks.append((name, cat, u))
    with ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(lambda t: (t[0], t[1], probe(t[2])), tasks))

    best = {}
    for name, cat, (user, title, n) in results:
        if title is None or n == 0:
            continue
        match = norm(name) in norm(title) or norm(title) in norm(name) or norm(title).startswith(norm(name)[:6])
        cur = best.get(name)
        score = (match, n)
        if not cur or score > cur["score"]:
            best[name] = {"name": name, "cat": cat, "user": user, "channel": title, "items": n,
                          "match": match, "score": score}
    ok = [v for v in best.values() if v["match"]]
    doubt = [v for v in best.values() if not v["match"]]
    print(f"확실 매칭 {len(ok)}곳 / 의심 {len(doubt)}곳 / 실패 {len(CANDIDATES) - len(best)}곳\n")
    print("=== 확실 ===")
    for v in sorted(ok, key=lambda x: x["cat"]):
        print(f"  [{v['cat']}] {v['name']} → @{v['user']} ({v['channel']}, {v['items']}개)")
    print("\n=== 의심 (채널명 불일치 — 검수 필요) ===")
    for v in sorted(doubt, key=lambda x: x["cat"]):
        print(f"  [{v['cat']}] {v['name']} → @{v['user']} 채널명='{v['channel']}' ({v['items']}개)")
    for v in best.values():
        v.pop("score")
    json.dump(list(best.values()), open("hip_probe_result.json", "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
