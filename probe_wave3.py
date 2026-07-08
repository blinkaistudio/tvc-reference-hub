# -*- coding: utf-8 -*-
"""힙 스튜디오 3차 웨이브 후보 검증 (probe_hip.py 재사용)"""
import sys, json, re
from concurrent.futures import ThreadPoolExecutor
from probe_hip import probe, norm

sys.stdout.reconfigure(encoding="utf-8")

CANDIDATES = [
    # ---- 모션/디자인 ----
    ("Gretel", "모션/디자인", ["gretel", "gretelny"]),
    ("Method Design", "모션/디자인", ["methoddesign", "methodstudios"]),
    ("Wonderlust", "모션/디자인", ["wonderlust"]),
    ("Hue & Cry", "모션/디자인", ["hueandcry", "huecry"]),
    ("IV Studio", "모션/디자인", ["ivstudio"]),
    ("The Furrow", "모션/디자인", ["thefurrow"]),
    ("Slanted Studios", "모션/디자인", ["slantedstudios"]),
    ("Baillat Studio", "모션/디자인", ["baillat", "baillatstudio"]),
    ("Wolf & Crow", "모션/디자인", ["wolfandcrow"]),
    ("Nomint", "모션/디자인", ["nomint"]),
    ("Caravan", "모션/디자인", ["caravan", "caravanla"]),
    ("Sons & Daughters?스킵", "모션/디자인", []),
    ("Moving Brands", "모션/디자인", ["movingbrands"]),
    ("Order Design", "모션/디자인", ["orderdesign"]),
    ("Zelig", "모션/디자인", ["zelig", "zeligstudio"]),
    ("Motionlab?스킵", "모션/디자인", []),
    # ---- CG/VFX ----
    ("Digital Domain", "CG/VFX", ["digitaldomain"]),
    ("RISE FX", "CG/VFX", ["risefx"]),
    ("Blacksmith VFX", "CG/VFX", ["blacksmithvfx", "blacksmith"]),
    ("Preymaker", "CG/VFX", ["preymaker"]),
    ("Mathematic", "CG/VFX", ["mathematic", "mathematicstudio"]),
    ("Unit Image", "CG/VFX", ["unitimage"]),
    ("Axis Studios", "CG/VFX", ["axisstudios", "axisanimation"]),
    ("Goodbye Kansas", "CG/VFX", ["goodbyekansas"]),
    ("RealtimeUK", "CG/VFX", ["realtimeuk"]),
    ("ILP", "CG/VFX", ["ilpvfx", "importantlookingpirates"]),
    ("Parliament VFX", "CG/VFX", ["parliamentvfx", "parliament"]),
    ("Mikros", "CG/VFX", ["mikrosanimation", "mikrosimage"]),
    # ---- 애니메이션 ----
    ("The Line", "애니메이션", ["thelineanimation", "theline"]),
    ("Cartoon Saloon", "애니메이션", ["cartoonsaloon"]),
    ("Sun Creature", "애니메이션", ["suncreature"]),
    ("Tumblehead", "애니메이션", ["tumblehead"]),
    ("Rubber House", "애니메이션", ["rubberhouse"]),
    ("Studio Meala", "애니메이션", ["studiomeala"]),
    ("Blinkink", "애니메이션", ["blinkink"]),
    ("Wednesday?중복스킵", "애니메이션", []),
    # ---- 라이브액션 ----
    ("RadicalMedia", "라이브액션", ["radicalmedia"]),
    ("Anonymous Content", "라이브액션", ["anonymouscontent"]),
    ("Superprime", "라이브액션", ["superprime", "superprimefilms"]),
    ("The Directors Bureau", "라이브액션", ["thedirectorsbureau"]),
    ("Partizan", "라이브액션", ["partizan"]),
    ("The Sweet Shop", "라이브액션", ["thesweetshop"]),
    ("Revolver", "라이브액션", ["revolverfilms", "revolver"]),
    ("Scoundrel", "라이브액션", ["scoundrelfilms", "scoundrel"]),
    ("Exit Films", "라이브액션", ["exitfilms"]),
    ("Halal", "라이브액션", ["halal", "halalamsterdam"]),
    ("Czar", "라이브액션", ["czarbe", "czar"]),
    ("Blink Productions", "라이브액션", ["blinkprods", "blinkproductions"]),
    ("Bacon", "라이브액션", ["baconcph", "bacon"]),
    ("New Land", "라이브액션", ["newland"]),
    ("Ways & Means", "라이브액션", ["waysandmeans"]),
    ("Serial Pictures", "라이브액션", ["serialpictures"]),
    ("Love Song", "라이브액션", ["lovesongfilms", "lovesong"]),
    ("Object & Animal", "라이브액션", ["objectanimal", "objectandanimal"]),
    # ---- 미디어아트 ----
    ("teamLab", "미디어아트", ["teamlab", "teamlabnet"]),
    ("Nohlab", "미디어아트", ["nohlab"]),
    ("Ouchhh", "미디어아트", ["ouchhh"]),
    ("Marshmallow Laser Feast", "미디어아트", ["marshmallowlaserfeast", "mlfeast"]),
    ("AntiVJ", "미디어아트", ["antivj"]),
    ("1024 architecture", "미디어아트", ["1024architecture"]),
    ("fuse*", "미디어아트", ["fuseworks", "fusestudio"]),
]


def main():
    tasks = []
    for name, cat, users in CANDIDATES:
        for u in users:
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
            best[name] = {"name": name, "cat": cat, "user": user, "channel": title,
                          "items": n, "match": match, "score": score}
    ok = [v for v in best.values() if v["match"]]
    doubt = [v for v in best.values() if not v["match"]]
    print(f"확실 {len(ok)} / 의심 {len(doubt)}\n=== 확실 ===")
    for v in sorted(ok, key=lambda x: x["cat"]):
        print(f'  ("{v["name"]}", "{v["cat"]}", "{v["user"]}"),  # {v["channel"]}, {v["items"]}개')
    print("\n=== 의심 (검수 필요) ===")
    for v in sorted(doubt, key=lambda x: x["cat"]):
        print(f"  [{v['cat']}] {v['name']} → @{v['user']} 채널명='{v['channel']}' ({v['items']}개)")
    for v in best.values():
        v.pop("score")
    json.dump(list(best.values()), open("hip_probe3.json", "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
