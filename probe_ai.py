# -*- coding: utf-8 -*-
"""AI 스튜디오/크리에이터 유튜브 채널 실존+채널명 검증 → 확정 목록 출력.

probe_hip.py와 같은 원칙: 핸들 추정 → 실제 채널명 대조 → 불일치는 제외(사칭 방지).
"""
import sys, json, re, html, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
     "Accept-Language": "en-US,en;q=0.9"}

# (표시명, [유튜브 핸들 후보])
CANDIDATES = [
    # ---- AI 프로덕션 스튜디오 ----
    ("Secret Level", ["secretlevel", "SecretLevelStudio", "secretlevelai"]),
    ("Native Foreign", ["nativeforeign"]),
    ("Shy Kids", ["shykids", "shykidsvideo"]),
    ("Promise Studios", ["promisestudios", "promise"]),
    ("Asteria Film", ["asteriafilm", "asteria"]),
    ("Toonstar", ["toonstar", "toonstartv"]),
    ("Deep Voodoo", ["deepvoodoo", "deepvoodoostudio"]),
    ("Waymark", ["waymark"]),
    ("Silverside AI", ["silversideai", "silverside"]),
    ("Genre.ai", ["genreai", "genre_ai"]),
    ("Staircase Studios AI", ["staircasestudios", "staircasestudiosai"]),
    ("Showrunner (Fable)", ["showrunner", "fablestudio", "thesimulation"]),
    ("Machine Cinema", ["machinecinema"]),
    ("Wonder Dynamics", ["wonderdynamics"]),
    ("Invisible Studio?스킵", []),
    # ---- AI 필름메이커 / 크리에이터 ----
    ("The Dor Brothers", ["thedorbrothers", "dorbrothers"]),
    ("Neural Viz", ["neuralviz", "NeuralViz"]),
    ("Paul Trillo", ["paultrillo"]),
    ("Curious Refuge", ["curiousrefuge"]),
    ("PJ Accetturo", ["pjaccetturo", "pjace"]),
    ("Kavan the Kid", ["kavanthekid", "kavancardoza"]),
    ("Dave Clark", ["daveclarkcreative", "daveclarkfilms", "immadaveclark"]),
    ("Hashem Al-Ghaili", ["hashemalghaili", "HashemAlGhaili"]),
    ("Aze Alter", ["azealter", "AzeAlter"]),
    ("Sagans", ["sagans", "sagansai"]),
    ("Metapuppet", ["metapuppet"]),
    ("Uncanny Harry", ["uncannyharry"]),
    ("Abandoned Films", ["abandonedfilms"]),
    ("demonflyingfox", ["demonflyingfox"]),
    ("Karen X. Cheng", ["karenxcheng"]),
    ("Bilawal Sidhu", ["bilawalsidhu", "bilawals"]),
    ("Don Allen Stevenson III", ["donallenIII", "donallenstevenson"]),
    ("The Reel Robot", ["thereelrobot"]),
    ("Matan Cohen-Grumi", ["matancohengrumi"]),
    ("Brandon Baum", ["brandonbaum", "baumsworld"]),
    ("Corridor Digital", ["corridordigital", "corridor"]),
    ("Theoretically Media", ["theoreticallymedia"]),
    ("CyberJungle", ["thecyberjungle", "cyberjungle"]),
    ("Diesol", ["diesol"]),
    ("Vallée?스킵", []),
    # ---- AI 플랫폼 쇼케이스 (공식) ----
    ("Runway", ["runwayml"]),
    ("Luma AI", ["lumalabsai", "lumaai"]),
    ("Pika", ["pika_labs", "pikalabs"]),
    ("OpenAI (Sora)", ["openai"]),
    ("Google DeepMind (Veo)", ["googledeepmind"]),
    ("Kling AI", ["klingai"]),
    ("Higgsfield", ["higgsfield", "higgsfieldai"]),
    ("Hailuo (MiniMax)", ["hailuoai", "minimaxai"]),
    ("Midjourney", ["midjourney"]),
    ("ElevenLabs", ["elevenlabsio", "elevenlabs"]),
    # ---- 국내 ----
    ("프리윌루전 Freewillusion", ["freewillusion"]),
    ("돌고래유괴단?중복스킵", []),
]


def norm(s):
    return re.sub(r"[^a-z0-9가-힣]", "", (s or "").lower())


def probe_handle(handle):
    try:
        req = urllib.request.Request(f"https://www.youtube.com/@{handle}", headers=H)
        body = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
        cid = (re.search(r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"', body)
               or re.search(r'<meta itemprop="identifier" content="(UC[\w-]{22})"', body)
               or re.search(r'"externalId":"(UC[\w-]{22})"', body)
               or re.search(r'"browseId":"(UC[\w-]{22})"', body)
               or re.search(r'"channelId":"(UC[\w-]{22})"', body))
        title = re.search(r'<meta property="og:title" content="([^"]*)"', body)
        subs = re.search(r'"subscriberCountText"[^}]*?"simpleText":"([^"]*)"', body)
        return (cid.group(1) if cid else None,
                html.unescape(title.group(1)) if title else "",
                subs.group(1) if subs else "")
    except Exception:
        return None, "", ""


def main():
    tasks = []
    for name, handles in CANDIDATES:
        for h in handles:
            tasks.append((name, h))
    with ThreadPoolExecutor(max_workers=12) as ex:
        results = list(ex.map(lambda t: (t[0], t[1], probe_handle(t[1])), tasks))
    best = {}
    for name, handle, (cid, title, subs) in results:
        if not cid:
            continue
        n1, n2 = norm(name), norm(title)
        match = (n1 in n2 or n2 in n1 or n2.startswith(n1[:6]) or n1.startswith(n2[:6])) and len(n2) >= 3
        cur = best.get(name)
        if not cur or (match, 1) > (cur["match"], 1):
            best[name] = {"name": name, "handle": handle, "cid": cid, "title": title,
                          "subs": subs, "match": match}
    ok = [v for v in best.values() if v["match"]]
    doubt = [v for v in best.values() if not v["match"]]
    print(f"확실 {len(ok)} / 의심 {len(doubt)}\n=== 확실 ===")
    for v in ok:
        print(f'  ("{v["name"]}", "AI", "{v["cid"]}"),  # @{v["handle"]} = {v["title"]} ({v["subs"]})')
    print("\n=== 의심 ===")
    for v in doubt:
        print(f"  {v['name']} → @{v['handle']} 채널명='{v['title']}' ({v['subs']})")
    json.dump(list(best.values()), open("ai_probe.json", "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
