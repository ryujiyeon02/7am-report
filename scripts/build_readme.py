"""
reports.json 을 읽어 README.md 를 다시 만듭니다.

- 최신 리포트 1면을 previews/latest.png 로 렌더링해 미리보기로 표시
- 리포트 목록은 날짜 내림차순(최신이 맨 위)

사용법
  python scripts/build_readme.py

새 리포트 추가(파일 복사 + reports.json 등록 + README 갱신을 한 번에)
  python scripts/build_readme.py add <PDF경로> --date 2026-11-14 --type daily \
      --title "제목" [--subtitle "부제"]

  --type : daily(데일리) / forecast(지수 예측) / quant(퀀트 분석)

필요 패키지: pip install pymupdf
"""
import argparse
import json
import shutil
from datetime import date as _date
from pathlib import Path

import pymupdf  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "reports.json"
README = ROOT / "README.md"
PREVIEW = ROOT / "previews" / "latest.png"

TYPES = {
    "daily": "📰 Daily",
    "forecast": "🎯 지수 예측",
    "quant": "📊 퀀트 분석",
}
WEEKDAY = "월화수목금토일"


def load():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else []


def save(items):
    DB.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sort_key(r):
    # 같은 날짜면 daily → forecast → quant 순
    order = list(TYPES).index(r["type"]) if r["type"] in TYPES else 9
    return (r["date"], -order)


def kdate(d):
    y, m, dd = map(int, d.split("-"))
    return f"{d} ({WEEKDAY[_date(y, m, dd).weekday()]})"


def render_preview(pdf_path):
    PREVIEW.parent.mkdir(exist_ok=True)
    with pymupdf.open(pdf_path) as doc:
        pix = doc[0].get_pixmap(dpi=110)
        pix.save(PREVIEW)


def build():
    items = sorted(load(), key=sort_key, reverse=True)
    latest = items[0] if items else None
    if latest:
        render_preview(ROOT / latest["file"])

    L = []
    L.append("# QUANTIFI 7시 리포트\n")
    L.append("> 매일 아침 07:00 (일요일 제외) · 06:00 미국장 마감 이후 이슈 반영\n")
    L.append("**구성** : 미국 증시 → 매크로 → 오늘의 한국 주식 전망 및 전일 장 마감 → FICC 동향  ")
    L.append("**+α** : 주요 지표 발표 전날 학회원 토론 기반 지수 예측치 · 퀀트 분석(비정기)\n")

    if latest:
        L.append("## 🆕 최신 리포트\n")
        L.append(f"### [{latest['title']}]({latest['file']})")
        if latest.get("subtitle"):
            L.append(f"*{latest['subtitle']}*  ")
        L.append(f"{kdate(latest['date'])} · {TYPES.get(latest['type'], latest['type'])}\n")
        L.append(f'<a href="{latest["file"]}"><img src="previews/latest.png" width="520" alt="최신 리포트 미리보기"></a>\n')

    L.append("## 📚 리포트 목록\n")
    L.append("| 날짜 | 구분 | 제목 |")
    L.append("|---|---|---|")
    for r in items:
        L.append(f"| {kdate(r['date'])} | {TYPES.get(r['type'], r['type'])} | [{r['title']}]({r['file']}) |")
    L.append("")

    README.write_text("\n".join(L), encoding="utf-8")
    print(f"README.md 갱신 완료 ({len(items)}건)")


def add(a):
    src = Path(a.pdf)
    dest = Path("reports") / f"{a.date}_{a.type}{src.suffix}"
    (ROOT / "reports").mkdir(exist_ok=True)
    shutil.copy(src, ROOT / dest)
    items = [r for r in load() if r["file"] != str(dest)]
    items.append({"date": a.date, "type": a.type, "title": a.title,
                  "subtitle": a.subtitle or "", "file": str(dest)})
    save(sorted(items, key=sort_key, reverse=True))
    print(f"추가: {dest}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("add")
    s.add_argument("pdf")
    s.add_argument("--date", required=True)
    s.add_argument("--type", choices=list(TYPES), default="daily")
    s.add_argument("--title", required=True)
    s.add_argument("--subtitle")
    a = p.parse_args()
    if a.cmd == "add":
        add(a)
    build()
