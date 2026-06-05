#!/usr/bin/env python3
"""
맞춤법 검사 → 원본 MD 수정 → 태그 삽입 → 블로그 발행  v2.0

기능:
  1. 네이버 맞춤법 검사 (passportKey 자동 획득)
  2. 오류 항목별 체크박스로 선택적 교정 적용
  3. 콘텐츠 기반 태그 자동 추천 + 직접 입력
  4. 원본 Obsidian MD 파일 업데이트 (교정 + 태그)
  5. 블로그 발행 (publish_to_blog.py 호출)

Usage: python spell_check_and_publish.py <파일경로>
"""

import sys
import os
import re
import json
import html as html_module
import time
import urllib.parse
import urllib.request
import http.cookiejar
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from collections import Counter

# ── 경로 설정 ─────────────────────────────────────────────────────────────────

PUBLISH_SCRIPT = os.path.join(os.path.dirname(__file__), "publish_to_blog.py")

# ── 상수 ──────────────────────────────────────────────────────────────────────

CHUNK_SIZE = 500
MAX_CHARS  = 3000

ERROR_TYPE  = {"1": "맞춤법", "2": "띄어쓰기", "3": "표준어 의심", "4": "통계 교정"}
ERROR_COLOR = {"1": "#e74c3c", "2": "#e67e22", "3": "#8e44ad", "4": "#2980b9"}

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

KO_STOPWORDS = {
    "입니다", "합니다", "있습니다", "됩니다", "없습니다", "같습니다", "하겠습니다",
    "그리고", "하지만", "또한", "이것", "저것", "그것", "우리", "위해", "통해",
    "대해", "이런", "저런", "하면", "되면", "경우", "지금", "이제", "오늘",
    "어제", "때문", "이후", "이전", "방법", "내용", "모든", "다른", "이상",
    "가능", "일반", "사용", "관련", "부분", "기반", "통한", "위한", "대한",
    "따라", "통해서", "있어서", "있으며", "있도록", "하도록", "수있", "있는",
    "하는", "이는", "하게", "되어", "해서", "해야", "하여", "대한", "적인",
    "이며", "로서", "으로", "에서", "에게", "부터", "까지", "처럼", "보다",
    "이나", "하나", "모두", "전체", "각각", "이번", "다음", "이전",
}

EN_STOPWORDS = {
    "the", "and", "for", "are", "not", "with", "this", "that", "from",
    "have", "will", "can", "been", "was", "has", "its", "but", "you",
    "all", "our", "one", "out", "use", "your", "also", "more", "than",
    "into", "when", "about", "they", "then", "some", "each",
}

# ── 텍스트 추출 ───────────────────────────────────────────────────────────────

def extract_text(file_path: str) -> str:
    """마크다운 → 순수 텍스트 (맞춤법 검사용)."""
    with open(file_path, encoding="utf-8") as f:
        text = f.read()
    text = re.sub(r"^---.*?---\s*\n", "", text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", " ", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_~|>]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ── 프론트매터 파싱 ───────────────────────────────────────────────────────────

def parse_tags_from_frontmatter(content: str) -> list[str]:
    """현재 파일의 tags 추출 (인라인/블록 둘 다 지원)."""
    fm = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not fm:
        return []
    fm_body = fm.group(1)

    # tags: [a, b, c]
    m = re.search(r"^tags:\s*\[([^\]]*)\]", fm_body, re.MULTILINE)
    if m:
        return [t.strip().strip("\"'") for t in m.group(1).split(",") if t.strip()]

    # tags:\n  - a
    m = re.search(r"^tags:\s*\n((?:\s+-[^\n]+\n?)*)", fm_body, re.MULTILINE)
    if m:
        return [re.sub(r"^\s*-\s*", "", l).strip().strip("\"'")
                for l in m.group(1).splitlines() if l.strip()]
    return []

def update_frontmatter_tags(content: str, all_tags: list[str]) -> str:
    """frontmatter의 tags 필드를 인라인 배열 형식으로 갱신 (없으면 추가)."""
    if not all_tags:
        return content

    fm = re.match(r"^(---\s*\n)(.*?)(---\s*\n)", content, re.DOTALL)
    if not fm:
        return content

    pre, body, post = fm.group(1), fm.group(2), fm.group(3)
    rest = content[fm.end():]

    # 중복 제거 (순서 유지)
    all_tags = list(dict.fromkeys(all_tags))
    tags_str = ", ".join(all_tags)
    new_tag_line = f"tags: [{tags_str}]\n"

    # 인라인 교체
    new_body, n = re.subn(r"^tags:\s*\[.*?\]\n", new_tag_line, body, flags=re.MULTILINE)
    if n == 0:
        # 블록 교체
        new_body, n = re.subn(
            r"^tags:\s*\n(?:\s+-[^\n]+\n?)*",
            new_tag_line, body, flags=re.MULTILINE
        )
    if n == 0:
        # 없으면 마지막에 추가
        new_body = body + new_tag_line

    return pre + new_body + post + rest

# ── 태그 추천 ─────────────────────────────────────────────────────────────────

# 콘텐츠 패턴 기반 카테고리 태그
CATEGORY_PATTERNS: dict[str, str] = {
    "Python":   r"\bpython\b|\bpip\b|\bpyenv\b",
    "AI":       r"\bai\b|인공지능|머신러닝|딥러닝|\bclaude\b|\bgpt\b|\bllm\b",
    "자동화":   r"자동화|자동\s|스크립트|cron|크론|배치",
    "옵시디언": r"obsidian|옵시디언|볼트|vault",
    "블로그":   r"블로그|포스트|발행|배포|publish",
    "개발":     r"개발|코딩|프로그래밍|coding|programming",
    "맞춤법":   r"맞춤법|교정|스펠|spelling",
    "Jekyll":   r"\bjekyll\b|\bgithub\s*pages\b",
    "Git":      r"\bgit\b|\bgithub\b",
}

def suggest_tags(text: str, existing: list[str]) -> list[str]:
    """콘텐츠에서 태그 후보 추출."""
    text_lower = text.lower()
    suggestions: list[str] = []

    # 1. 패턴 기반
    for tag, pattern in CATEGORY_PATTERNS.items():
        if re.search(pattern, text_lower, re.IGNORECASE):
            suggestions.append(tag)

    # 2. 영문 기술 용어 (3자 이상, 빈도 2+)
    en_words = re.findall(r"\b[A-Za-z][A-Za-z0-9\-\.]{2,}\b", text)
    en_freq = Counter(w.lower() for w in en_words if w.lower() not in EN_STOPWORDS)
    for w, c in en_freq.most_common(5):
        if c >= 2 and w not in [s.lower() for s in suggestions]:
            suggestions.append(w)

    # 3. 한국어 명사 (3자 이상, 빈도 3+)
    ko_words = re.findall(r"[가-힣]{3,8}", text)
    ko_freq = Counter(w for w in ko_words if w not in KO_STOPWORDS)
    for w, c in ko_freq.most_common(6):
        if c >= 3 and w not in suggestions:
            suggestions.append(w)

    # 기존 태그 제외, 최대 12개
    existing_lower = [t.lower() for t in existing]
    return [s for s in suggestions if s.lower() not in existing_lower][:12]

# ── 네이버 맞춤법 API ─────────────────────────────────────────────────────────

def _get_session():
    try:
        import requests as _r
        s = _r.Session()
        s.headers.update({"User-Agent": _UA})
        resp = s.get(
            "https://search.naver.com/search.naver",
            params={"where": "nexearch", "query": "맞춤법검사"},
            timeout=10,
        )
        m = re.search(r"passportKey\W+([A-Za-z0-9_\-]{20,})", resp.text)
        return s, (m.group(1) if m else "")
    except ImportError:
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        opener.addheaders = [("User-Agent", _UA)]
        url = ("https://search.naver.com/search.naver?"
               + urllib.parse.urlencode({"where": "nexearch", "query": "맞춤법검사"}))
        page = opener.open(url, timeout=10).read().decode("utf-8", errors="replace")
        m = re.search(r"passportKey\W+([A-Za-z0-9_\-]{20,})", page)
        return opener, (m.group(1) if m else "")

def _parse_html_errors(origin_html: str, result_html: str) -> list[dict]:
    originals   = re.findall(r"<span class='result_underline'>(.*?)</span>", origin_html)
    corrections = re.findall(r"<em class='(\w+)_text'>(.*?)</em>", result_html)
    type_map    = {"red": "1", "green": "2", "violet": "3", "blue": "4"}
    errors = []
    for orig, (cls, corr) in zip(originals, corrections):
        o = html_module.unescape(re.sub(r"<[^>]+>", "", orig))
        c = html_module.unescape(re.sub(r"<[^>]+>", "", corr))
        if o != c:
            errors.append({"original": o, "correct": c, "type": type_map.get(cls, "1")})
    return errors

def _call_api(session, key: str, chunk: str) -> list[dict]:
    url    = "https://m.search.naver.com/p/csearch/ocontent/util/SpellerProxy"
    params = {"q": chunk, "where": "nexearch", "color_blindness": "0", "passportKey": key}
    hdrs   = {"Referer": "https://search.naver.com/", "Accept": "application/json",
               "X-Requested-With": "XMLHttpRequest"}
    try:
        import requests as _r
        data = session.get(url, params=params, headers=hdrs, timeout=15).json()
    except ImportError:
        qs  = urllib.parse.urlencode(params)
        req = urllib.request.Request(f"{url}?{qs}", headers=hdrs)
        data = json.loads(session.open(req, timeout=15).read().decode("utf-8"))

    result = data.get("message", {}).get("result", {})
    if not result:
        return []
    words = result.get("words", [])
    if words:
        tm = {"1": "1", "2": "2", "3": "3", "4": "4"}
        return [
            {"original": w.get("orgStr", ""), "correct": w.get("correctText", ""),
             "type": tm.get(str(w.get("type", "1")), "1")}
            for w in words
            if w.get("orgStr") != w.get("correctText") and str(w.get("type", "0")) in tm
        ]
    return _parse_html_errors(result.get("origin_html", ""), result.get("html", ""))

def check_spelling(text: str) -> tuple[list[dict], str | None]:
    text = text[:MAX_CHARS]
    chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    try:
        session, key = _get_session()
    except Exception as e:
        return [], f"세션 초기화 실패: {e}"
    if not key:
        return [], "passportKey를 가져올 수 없습니다. 인터넷 연결을 확인하세요."
    errors = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        try:
            errors.extend(_call_api(session, key, chunk))
            if i < len(chunks) - 1:
                time.sleep(0.4)
        except Exception as e:
            return errors, f"API 오류 (청크 {i+1}): {e}"
    return errors, None

# ── 파일 수정 ─────────────────────────────────────────────────────────────────

def apply_changes(file_path: str, selected_errors: list[dict], final_tags: list[str]) -> None:
    """선택된 교정 + 최종 태그를 원본 MD 파일에 적용 후 저장."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # ── 1. 맞춤법 교정 ────────────────────────────────────────────────────────
    if selected_errors:
        fm_m = re.match(r"^(---\s*\n.*?\n---\s*\n)", content, re.DOTALL)
        fm_part   = fm_m.group(1) if fm_m else ""
        body_part = content[len(fm_part):]

        # 코드 블록 / URL 보호
        placeholders: dict[str, str] = {}
        counter = [0]

        def protect(m):
            k = f"\x00P{counter[0]}\x00"
            placeholders[k] = m.group(0)
            counter[0] += 1
            return k

        body = re.sub(r"```[\s\S]*?```", protect, body_part)
        body = re.sub(r"`[^`\n]+`",      protect, body)
        body = re.sub(r"https?://\S+",   protect, body)

        for e in selected_errors:
            body = body.replace(e["original"], e["correct"])

        for k, v in placeholders.items():
            body = body.replace(k, v)

        content = fm_part + body

    # ── 2. 태그 업데이트 ──────────────────────────────────────────────────────
    if final_tags is not None:
        content = update_frontmatter_tags(content, final_tags)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── GUI ───────────────────────────────────────────────────────────────────────

def _make_scrollable(parent) -> tk.Frame:
    """Canvas + Scrollbar 래퍼. 내부 Frame 반환."""
    container = tk.Frame(parent)
    container.pack(fill="both", expand=True)
    canvas = tk.Canvas(container, highlightthickness=0)
    vsb    = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    inner  = tk.Frame(canvas)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # 마우스 휠 지원
    def _on_wheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    canvas.bind_all("<MouseWheel>", _on_wheel)
    return inner

def show_main_window(
    file_path: str,
    errors: list[dict],
    api_err: str | None,
    current_tags: list[str],
    suggested_tags: list[str],
) -> tuple[bool, list[dict], list[str]]:
    """
    결과 창 표시.
    Returns (should_publish, selected_errors, final_tags)
    """
    root = tk.Tk()
    root.title("발행 전 검토")
    root.minsize(680, 520)
    root.resizable(True, True)
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    w, h = 760, 580
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    result: dict = {"publish": False, "sel_errors": [], "tags": current_tags[:]}

    # ── 헤더 ──────────────────────────────────────────────────────────────────
    hdr = tk.Frame(root, bg="#2c3e50", pady=8)
    hdr.pack(fill="x")
    tk.Label(hdr, text=f"\U0001f4dd  {os.path.basename(file_path)}",
             fg="white", bg="#2c3e50", font=("Malgun Gothic", 11, "bold"),
             anchor="w", padx=12).pack(fill="x")

    if api_err:
        ef = tk.Frame(root, bg="#f8d7da", pady=3)
        ef.pack(fill="x")
        tk.Label(ef, text=f"⚠  {api_err}", fg="#721c24", bg="#f8d7da",
                 font=("Malgun Gothic", 8), anchor="w", padx=12).pack(fill="x")

    # 요약 배너
    sp_cnt = sum(1 for e in errors if e["type"] == "1")
    if not errors:
        b_text, b_bg = "✅  맞춤법 오류 없음 — 태그 확인 후 발행하세요.", "#27ae60"
    elif sp_cnt:
        b_text = f"⚠  {len(errors)}개 항목 발견 (맞춤법 {sp_cnt}개 포함)"
        b_bg   = "#e74c3c"
    else:
        b_text, b_bg = f"⚠  {len(errors)}개 항목 발견 (주로 띄어쓰기)", "#e67e22"
    bf = tk.Frame(root, bg=b_bg, pady=6)
    bf.pack(fill="x")
    tk.Label(bf, text=b_text, fg="white", bg=b_bg,
             font=("Malgun Gothic", 10, "bold"), padx=12).pack(anchor="w")

    # ── 탭 ────────────────────────────────────────────────────────────────────
    nb = ttk.Notebook(root)
    nb.pack(fill="both", expand=True, padx=8, pady=6)

    # ════════════════════════════════════════════════════════
    # 탭 1: 맞춤법 교정
    # ════════════════════════════════════════════════════════
    tab_spell = tk.Frame(nb, padx=6, pady=4)
    nb.add(tab_spell, text=f"📋  맞춤법 교정  ({len(errors)})")

    err_vars: list[tk.BooleanVar] = []

    if errors:
        # 전체 선택/해제
        ctrl = tk.Frame(tab_spell)
        ctrl.pack(fill="x", pady=(0, 4))
        all_var = tk.BooleanVar(value=True)

        def toggle_all():
            for v in err_vars:
                v.set(all_var.get())

        tk.Checkbutton(ctrl, text="전체 선택 / 해제", variable=all_var,
                       command=toggle_all, font=("Malgun Gothic", 9)).pack(side="left")
        tk.Label(ctrl, text="✓ 체크된 항목이 파일에 적용됩니다.",
                 fg="#7f8c8d", font=("Malgun Gothic", 8)).pack(side="left", padx=8)

        inner = _make_scrollable(tab_spell)
        inner.columnconfigure(0, minsize=80)
        inner.columnconfigure(1, minsize=180)
        inner.columnconfigure(2, minsize=20)
        inner.columnconfigure(3, minsize=200)

        # 헤더 행
        for col, (text, w_) in enumerate([("종류", 80), ("원문 (오류)", 180),
                                          ("→", 20), ("교정 제안", 200)]):
            tk.Label(inner, text=text, font=("Malgun Gothic", 8, "bold"),
                     fg="#555", width=w_ // 8).grid(row=0, column=col, sticky="w", padx=4)

        ttk.Separator(inner, orient="horizontal").grid(
            row=1, column=0, columnspan=4, sticky="ew", pady=2)

        for i, e in enumerate(errors):
            var = tk.BooleanVar(value=True)
            err_vars.append(var)
            row = i + 2
            color = ERROR_COLOR.get(e["type"], "#333")
            cb = tk.Checkbutton(inner, variable=var)
            cb.grid(row=row, column=0, sticky="w", padx=(2, 0))
            tk.Label(inner, text=ERROR_TYPE.get(e["type"], "?"),
                     font=("Malgun Gothic", 9), fg=color).grid(
                row=row, column=0, sticky="e", padx=(0, 4))
            tk.Label(inner, text=e["original"], font=("Malgun Gothic", 9),
                     fg="#c0392b").grid(row=row, column=1, sticky="w", padx=4)
            tk.Label(inner, text="→", font=("Malgun Gothic", 9)).grid(
                row=row, column=2)
            tk.Label(inner, text=e["correct"], font=("Malgun Gothic", 9),
                     fg="#27ae60").grid(row=row, column=3, sticky="w", padx=4)
    else:
        tk.Label(tab_spell, text="✅  발견된 맞춤법 오류가 없습니다.",
                 font=("Malgun Gothic", 10), fg="#27ae60").pack(pady=30)

    # ════════════════════════════════════════════════════════
    # 탭 2: 태그 관리
    # ════════════════════════════════════════════════════════
    tab_tags = tk.Frame(nb, padx=10, pady=8)
    nb.add(tab_tags, text="🏷️  태그 관리")

    # 현재 태그
    tk.Label(tab_tags, text="현재 태그 (frontmatter)", font=("Malgun Gothic", 9, "bold"),
             fg="#2c3e50").pack(anchor="w")
    cur_frame = tk.Frame(tab_tags, pady=4)
    cur_frame.pack(fill="x")
    if current_tags:
        for t in current_tags:
            tk.Label(cur_frame, text=f" {t} ", relief="solid", bd=1, padx=4, pady=1,
                     bg="#eaf4fb", fg="#2980b9", font=("Malgun Gothic", 9),
                     cursor="hand2").pack(side="left", padx=3, pady=2)
    else:
        tk.Label(cur_frame, text="(없음)", fg="#999",
                 font=("Malgun Gothic", 9)).pack(side="left")

    ttk.Separator(tab_tags, orient="horizontal").pack(fill="x", pady=6)

    # 추천 태그
    tk.Label(tab_tags, text="추천 태그 (콘텐츠 기반 자동 추출)",
             font=("Malgun Gothic", 9, "bold"), fg="#2c3e50").pack(anchor="w")
    tk.Label(tab_tags, text="체크한 항목이 tags 필드에 추가됩니다.",
             font=("Malgun Gothic", 8), fg="#7f8c8d").pack(anchor="w")

    sug_vars: list[tuple[str, tk.BooleanVar]] = []
    sug_frame = tk.Frame(tab_tags, pady=6)
    sug_frame.pack(fill="x")
    if suggested_tags:
        for i, tag in enumerate(suggested_tags):
            var = tk.BooleanVar(value=False)
            sug_vars.append((tag, var))
            tk.Checkbutton(sug_frame, text=tag, variable=var,
                           font=("Malgun Gothic", 9)).grid(
                row=i // 4, column=i % 4, sticky="w", padx=6, pady=1)
    else:
        tk.Label(sug_frame, text="(추출된 추천 태그 없음)", fg="#999",
                 font=("Malgun Gothic", 9)).pack(side="left")

    ttk.Separator(tab_tags, orient="horizontal").pack(fill="x", pady=6)

    # 직접 입력
    tk.Label(tab_tags, text="직접 태그 추가", font=("Malgun Gothic", 9, "bold"),
             fg="#2c3e50").pack(anchor="w")
    manual_frame = tk.Frame(tab_tags, pady=4)
    manual_frame.pack(fill="x")

    manual_entry = tk.Entry(manual_frame, font=("Malgun Gothic", 9), width=20)
    manual_entry.pack(side="left", padx=(0, 6))

    manual_tags: list[str] = []
    manual_tag_frame = tk.Frame(manual_frame)
    manual_tag_frame.pack(side="left", fill="x", expand=True)

    def add_manual_tag(event=None):
        tag = manual_entry.get().strip()
        if tag and tag not in current_tags and tag not in manual_tags:
            manual_tags.append(tag)
            tk.Label(manual_tag_frame, text=f" {tag} ", relief="solid", bd=1,
                     padx=4, pady=1, bg="#fef9e7", fg="#e67e22",
                     font=("Malgun Gothic", 9)).pack(side="left", padx=3)
        manual_entry.delete(0, "end")

    manual_entry.bind("<Return>", add_manual_tag)
    tk.Button(manual_frame, text="추가", font=("Malgun Gothic", 9),
              command=add_manual_tag).pack(side="left")

    # ── 하단 버튼 ──────────────────────────────────────────────────────────────
    btn_outer = tk.Frame(root, pady=10, padx=10)
    btn_outer.pack(fill="x")
    tk.Label(btn_outer,
             text="[수정+태그+발행] 클릭 시: 교정 적용 → tags 업데이트 → 원본 MD 저장 → 블로그 발행",
             fg="#7f8c8d", font=("Malgun Gothic", 8)).pack(anchor="w")

    btn_right = tk.Frame(btn_outer)
    btn_right.pack(anchor="e", pady=(4, 0))

    def on_cancel():
        root.destroy()

    def on_publish():
        # 선택된 교정 수집
        result["sel_errors"] = [e for e, v in zip(errors, err_vars) if v.get()]
        # 최종 태그 = 현재 + 체크된 추천 + 직접 입력
        checked_sug = [t for t, v in sug_vars if v.get()]
        all_tags = list(dict.fromkeys(current_tags + checked_sug + manual_tags))
        result["tags"] = all_tags
        result["publish"] = True
        root.destroy()

    tk.Button(btn_right, text="  취소  ", font=("Malgun Gothic", 9),
              command=on_cancel).pack(side="right", padx=(8, 0))
    tk.Button(
        btn_right,
        text="수정 + 태그 + 발행  ▶",
        font=("Malgun Gothic", 10, "bold"),
        bg="#2980b9", fg="white", activebackground="#1a6fa8",
        relief="flat", cursor="hand2", padx=10, pady=4,
        command=on_publish,
    ).pack(side="right")

    root.mainloop()
    return result["publish"], result["sel_errors"], result["tags"]

# ── 메인 ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python spell_check_and_publish.py <파일경로>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.isfile(file_path):
        messagebox.showerror("오류", f"파일을 찾을 수 없습니다:\n{file_path}")
        sys.exit(1)

    # 1. 파일 읽기
    with open(file_path, encoding="utf-8") as f:
        raw_content = f.read()

    # 2. 텍스트 추출 + 현재 태그 파싱
    text         = extract_text(file_path)
    current_tags = parse_tags_from_frontmatter(raw_content)

    # 3. 맞춤법 검사
    errors, api_err = check_spelling(text) if text else ([], "추출할 텍스트 없음")

    # 4. 태그 추천
    suggested = suggest_tags(text, current_tags)

    # 5. GUI 표시 → 사용자 결정
    should_publish, sel_errors, final_tags = show_main_window(
        file_path, errors, api_err, current_tags, suggested
    )

    if not should_publish:
        print("[취소] 발행이 취소되었습니다.")
        sys.exit(0)

    # 6. 파일 수정 (교정 + 태그)
    apply_changes(file_path, sel_errors, final_tags)
    print(f"[수정] 교정 {len(sel_errors)}건 적용, 태그: {final_tags}")

    # 7. 블로그 발행
    print(f"[발행] {file_path}")
    ret = subprocess.run([sys.executable, PUBLISH_SCRIPT, file_path], text=True)
    sys.exit(ret.returncode)


if __name__ == "__main__":
    main()
