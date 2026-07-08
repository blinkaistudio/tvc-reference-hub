# -*- coding: utf-8 -*-
"""패싯 태깅 도구 (API 미사용)
  python tag_tools.py sheets   : 미태깅 영상 썸네일 → 콘택트 시트 + manifest 생성 (Claude가 보고 태깅)
  python tag_tools.py apply    : sheets/facets_batch_*.json + facets_cache.json → data.js 반영
  python tag_tools.py fallback : 남은 미태깅 영상에 제목 키워드 규칙으로 기본 태그 부여
"""
import sys, json, re, urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
DATA_JS = HERE / "data.js"
CACHE = HERE / "facets_cache.json"
SHEET_DIR = HERE / "sheets"
THUMB_DIR = HERE / "thumbs"

FACETS = {
    "people": ["인물없음", "여성 1인", "남성 1인", "아이/청소년", "커플", "가족", "그룹/여럿", "셀럽/모델", "동물", "캐릭터/애니"],
    "place": ["스튜디오/세트", "도심/거리", "집/실내", "오피스/상업공간", "자연/야외", "바다/수변", "야간/네온", "차량/도로", "CG/가상공간"],
    "mood": ["감성/서정", "유머/위트", "럭셔리/하이엔드", "시네마틱", "미니멀/클린", "에너지/다이내믹", "따뜻함/가족적", "힙/트렌디", "노스탤지어", "스케일/임팩트"],
    "tone": ["밝고 화사", "뉴트럴/차분", "무디/어두움", "비비드/팝", "모노톤/흑백", "필름룩/빈티지"],
    "format": ["스토리/내러티브", "제품/비주얼 중심", "모델/뷰티컷", "모음집", "뮤직/퍼포먼스", "인터뷰/실사례", "정보/자막형"],
}

COLS, ROWS = 5, 5
CW, CH = 320, 180
GAP = 6
LABEL_H = 26


def load_data():
    text = DATA_JS.read_text(encoding="utf-8")
    m = re.match(r"window\.TVC_DATA = (.*);\s*$", text, re.DOTALL)
    return json.loads(m.group(1))


def save_data(data):
    DATA_JS.write_text("window.TVC_DATA = " + json.dumps(data, ensure_ascii=False) + ";", encoding="utf-8")


def load_cache():
    return json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}


def all_videos(data):
    out = []
    for cid, c in data["countries"].items():
        for v in c["videos"]:
            out.append((cid, v))
    return out


# 3x5 픽셀 숫자 비트맵 (폰트 렌더링 크래시 회피용)
DIGITS = {
    "0": ["111","101","101","101","111"], "1": ["010","110","010","010","111"],
    "2": ["111","001","111","100","111"], "3": ["111","001","111","001","111"],
    "4": ["101","101","111","001","001"], "5": ["111","100","111","001","111"],
    "6": ["111","100","111","101","111"], "7": ["111","001","010","010","010"],
    "8": ["111","101","111","101","111"], "9": ["111","101","111","001","111"],
}

def draw_number(draw, x, y, text, scale=4, color=(245, 197, 66)):
    for ch in text:
        bm = DIGITS.get(ch)
        if bm:
            for ry, row in enumerate(bm):
                for rx, bit in enumerate(row):
                    if bit == "1":
                        draw.rectangle([x + rx * scale, y + ry * scale,
                                        x + (rx + 1) * scale - 1, y + (ry + 1) * scale - 1], fill=color)
        x += 4 * scale


def cmd_sheets():
    from PIL import Image, ImageDraw
    data = load_data()
    cache = load_cache()
    todo = [(cid, v) for cid, v in all_videos(data) if v["id"] not in cache]
    print(f"미태깅 {len(todo)}개 → 시트 생성")
    THUMB_DIR.mkdir(exist_ok=True)
    SHEET_DIR.mkdir(exist_ok=True)
    for old in SHEET_DIR.glob("sheet_*.jpg"):
        old.unlink()

    def dl(item):
        _, v = item
        dest = THUMB_DIR / (v["id"] + ".jpg")
        if dest.exists():
            return
        try:
            url = f"https://img.youtube.com/vi/{v['id']}/mqdefault.jpg"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                dest.write_bytes(r.read())
        except Exception as e:
            print(f"  ! 썸네일 실패 {v['id']}: {e}")

    with ThreadPoolExecutor(max_workers=12) as ex:
        list(ex.map(dl, todo))

    per = COLS * ROWS
    manifest = []
    n_sheets = (len(todo) + per - 1) // per
    for s in range(n_sheets):
        batch = todo[s * per:(s + 1) * per]
        W = COLS * CW + (COLS + 1) * GAP
        H = ROWS * (CH + LABEL_H) + (ROWS + 1) * GAP
        sheet = Image.new("RGB", (W, H), (18, 20, 28))
        draw = ImageDraw.Draw(sheet)
        entries = []
        for i, (cid, v) in enumerate(batch):
            r, cch = divmod(i, COLS)
            x = GAP + cch * (CW + GAP)
            y = GAP + r * (CH + LABEL_H + GAP)
            idx = s * per + i + 1
            p = THUMB_DIR / (v["id"] + ".jpg")
            if p.exists():
                try:
                    im = Image.open(p).convert("RGB").resize((CW, CH))
                    sheet.paste(im, (x, y + LABEL_H))
                except Exception:
                    pass
            draw.rectangle([x, y, x + CW, y + LABEL_H], fill=(40, 44, 60))
            draw_number(draw, x + 8, y + 3, str(idx))
            entries.append({"n": idx, "id": v["id"], "country": cid, "cat": v.get("cat", ""),
                            "title": v["title"][:70], "ch": v.get("ch", "")[:30]})
        sheet.save(SHEET_DIR / f"sheet_{s+1:02d}.jpg", quality=82)
        manifest.extend(entries)
    (SHEET_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"시트 {n_sheets}장 + manifest.json → {SHEET_DIR}")


def cmd_apply():
    data = load_data()
    cache = load_cache()
    for f in sorted(SHEET_DIR.glob("facets_batch_*.json")):
        batch = json.loads(f.read_text(encoding="utf-8"))
        cache.update(batch)
    # 어휘 검증
    clean = {}
    for vid, fc in cache.items():
        out = {}
        for k, vocab in FACETS.items():
            vals = fc.get(k, [])
            if isinstance(vals, str):
                vals = [vals]
            out[k] = [x for x in vals if x in vocab]
        clean[vid] = out
    CACHE.write_text(json.dumps(clean, ensure_ascii=False), encoding="utf-8")
    n = 0
    for _, v in all_videos(data):
        if v["id"] in clean:
            v["facets"] = clean[v["id"]]
            n += 1
    save_data(data)
    total = len(all_videos(data))
    print(f"적용: {n}/{total}개 태깅됨")


RULES_FORMAT = [
    (r"모음|모아보기|集|傑作|compilation|best .*(ads|adverts|commercials)|top \d", "모음집"),
    (r"뮤직|music|dance|댄스|song", "뮤직/퍼포먼스"),
]

def cmd_fallback():
    data = load_data()
    cache = load_cache()
    n = 0
    for _, v in all_videos(data):
        if v.get("facets"):
            continue
        title = (v["title"] + " " + v.get("ch", "")).lower()
        fc = {"people": [], "place": [], "mood": [], "tone": [], "format": []}
        for pat, val in RULES_FORMAT:
            if re.search(pat, title):
                fc["format"] = [val]
                break
        v["facets"] = fc
        cache[v["id"]] = fc
        n += 1
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    save_data(data)
    print(f"규칙 기반 기본 태그 {n}개 부여 (빈 태그 포함) — 정밀 태깅은 Claude에게 '새 영상 태깅해줘' 요청")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "sheets":
        cmd_sheets()
    elif cmd == "apply":
        cmd_apply()
    elif cmd == "fallback":
        cmd_fallback()
    else:
        print(__doc__)
