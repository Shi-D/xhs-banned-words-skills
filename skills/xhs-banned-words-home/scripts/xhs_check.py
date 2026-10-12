#!/usr/bin/env python3
"""小红书违禁词检测脚本（零依赖，Python 3.8+）。

用法示例：
    python3 xhs_check.py note.md                    # 检测文件
    python3 xhs_check.py --text "这是全网最好用的面霜"  # 检测一段文字
    cat note.md | python3 xhs_check.py              # 从标准输入读取
    python3 xhs_check.py note.md --industry beauty  # 只用 通用 + 美妆 词库
    python3 xhs_check.py note.md --format json      # 输出 JSON，方便程序处理
    python3 xhs_check.py note.md --annotate         # 在原文中用【】标出违禁词
    python3 xhs_check.py --list-industries          # 查看可用行业

词库默认读取本脚本同级目录的 ../references/*.txt。
退出码：发现高危词返回 1，否则返回 0（可用于 CI / pre-commit）。
"""

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

RISK_LEVELS = ["高危", "中危", "低危"]
RISK_RANK = {name: i for i, name in enumerate(RISK_LEVELS)}

# 导流类常见的“拆分”写法：v 信、薇❤、加 V 等。检测前会额外在“去掉分隔符”的文本上匹配。
SEPARATORS = re.compile(r"[\s\-_·.。,，、|/\\*~～+＋'\"“”‘’()（）【】\[\]<>《》❤♥❥☆★✨💗💕👉]+")


class Term:
    def __init__(self, raw, suggestions, exceptions, category, risk, industry, title):
        self.raw = raw
        self.suggestions = suggestions
        self.exceptions = exceptions
        self.category = category
        self.risk = risk
        self.industry = industry
        self.industry_title = title
        if raw.startswith("re:"):
            self.pattern = re.compile(raw[3:], re.IGNORECASE)
            self.label = raw[3:]
        else:
            self.pattern = re.compile(re.escape(raw), re.IGNORECASE)
            self.label = raw


def load_wordlist(path):
    """解析词库文件。格式见 wordlists/README.md。"""
    industry, title = path.stem, path.stem
    category, risk = "未分类", "中危"
    terms = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or (line.startswith("#") and not line.startswith("##")):
            continue
        if line.startswith("@industry:"):
            industry = line.split(":", 1)[1].strip()
            continue
        if line.startswith("@title:"):
            title = line.split(":", 1)[1].strip()
            continue
        if line.startswith("##"):
            m = re.match(r"##\s*(.+?)\s*(?:\[(高危|中危|低危)\])?\s*$", line)
            category = m.group(1)
            risk = m.group(2) or "中危"
            continue
        # 列分隔符是“空格|空格”，所以正则里可以放心使用不带空格的 |
        parts = [p.strip() for p in re.split(r"\s+\|\s*|\s*\|\s+", line)]
        word = parts[0]
        if not word:
            continue
        suggestions = [s for s in parts[1].split("、") if s] if len(parts) > 1 and parts[1] else []
        exceptions = [s for s in parts[2].split("、") if s] if len(parts) > 2 and parts[2] else []
        try:
            terms.append(Term(word, suggestions, exceptions, category, risk, industry, title))
        except re.error as e:
            sys.stderr.write(f"[警告] {path.name}:{lineno} 正则无效，已跳过：{e}\n")
    return industry, title, terms


def load_all(wordlist_dir):
    lists = {}
    for path in sorted(Path(wordlist_dir).glob("*.txt")):
        industry, title, terms = load_wordlist(path)
        lists[industry] = (title, terms)
    return lists


def normalize(text):
    """全角转半角（ＶＸ→VX、１００％→100%），便于匹配。长度保持不变。"""
    return "".join(unicodedata.normalize("NFKC", ch) if len(unicodedata.normalize("NFKC", ch)) == 1 else ch
                   for ch in text)


def exception_spans(line, term):
    spans = []
    for exc in term.exceptions:
        for m in re.finditer(re.escape(exc), line, re.IGNORECASE):
            spans.append((m.start(), m.end()))
    return spans


def scan_line(line, terms):
    hits = []
    for term in terms:
        exc = exception_spans(line, term)
        for m in term.pattern.finditer(line):
            s, e = m.span()
            if s == e:
                continue
            if any(es <= s and e <= ee for es, ee in exc):
                continue
            hits.append((s, e, m.group(0), term))
    return hits


def scan_split_variants(line, terms, already):
    """在去掉分隔符/表情的文本上再匹配一次，抓 “微 信”“v·x” 这类拆分写法。"""
    keep = [(i, ch) for i, ch in enumerate(line) if not SEPARATORS.fullmatch(ch)]
    compact = "".join(ch for _, ch in keep)
    if len(compact) == len(line):
        return []
    hits = []
    for s, e, text, term in scan_line(compact, terms):
        os_, oe = keep[s][0], keep[e - 1][0] + 1
        if (oe - os_) == (e - s):  # 原文本身就是连续的，普通扫描已覆盖
            continue
        if any(a <= os_ and oe <= b for a, b in already):
            continue
        hits.append((os_, oe, line[os_:oe], term))
    return hits


def dedupe(hits):
    """同一位置被多个词命中时，只保留最长的那个（如“全网第一”优先于“第一”）。"""
    # 同长度时：风险更高的优先；同风险时行业词库优先于通用词库（行业替换建议更具体）
    hits.sort(key=lambda h: (-(h[1] - h[0]), RISK_RANK[h[3].risk], h[3].industry == "general", h[0]))
    kept = []
    for h in hits:
        if any(k[0] <= h[0] and h[1] <= k[1] for k in kept):
            continue
        kept.append(h)
    kept.sort(key=lambda h: h[0])
    return kept


def scan(text, terms, min_risk="低危"):
    max_rank = RISK_RANK[min_risk]
    results = []
    for lineno, raw_line in enumerate(text.splitlines(), 1):
        line = normalize(raw_line)
        hits = scan_line(line, terms)
        hits += scan_split_variants(line, terms, [(h[0], h[1]) for h in hits])
        for s, e, matched, term in dedupe(hits):
            if RISK_RANK[term.risk] > max_rank:
                continue
            ctx_s, ctx_e = max(0, s - 12), min(len(raw_line), e + 12)
            results.append({
                "line": lineno,
                "column": s + 1,
                "start": s,
                "end": e,
                "matched": raw_line[s:e],
                "term": term.label,
                "risk": term.risk,
                "category": term.category,
                "industry": term.industry,
                "industry_title": term.industry_title,
                "suggestions": term.suggestions,
                "context": ("…" if ctx_s > 0 else "") + raw_line[ctx_s:ctx_e] + ("…" if ctx_e < len(raw_line) else ""),
            })
    return results


def annotate(text, results):
    by_line = {}
    for r in results:
        by_line.setdefault(r["line"], []).append(r)
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        for r in sorted(by_line.get(lineno, []), key=lambda r: -r["start"]):
            tag = f"【{line[r['start']:r['end']]}⚠{r['risk']}】"
            line = line[:r["start"]] + tag + line[r["end"]:]
        out.append(line)
    return "\n".join(out)


def summary_counts(results):
    return {lvl: sum(1 for r in results if r["risk"] == lvl) for lvl in RISK_LEVELS}


def print_text(results, source):
    counts = summary_counts(results)
    if not results:
        print(f"✅ {source}：未发现词库中的违禁/限制词。（词库无法覆盖全部情况，仍建议人工复核语义层面的夸大与承诺）")
        return
    print(f"⚠️  {source}：共 {len(results)} 处风险 —— 高危 {counts['高危']} / 中危 {counts['中危']} / 低危 {counts['低危']}\n")
    for r in sorted(results, key=lambda r: (RISK_RANK[r["risk"]], r["line"], r["column"])):
        print(f"[{r['risk']}] 第{r['line']}行第{r['column']}列「{r['matched']}」  {r['industry_title']} · {r['category']}")
        print(f"        原文：{r['context']}")
        if r["suggestions"]:
            print(f"        建议：{' / '.join(r['suggestions'])}")
        print()


def print_markdown(results, source):
    counts = summary_counts(results)
    print(f"### 违禁词检测：{source}\n")
    print(f"高危 **{counts['高危']}** · 中危 **{counts['中危']}** · 低危 **{counts['低危']}**\n")
    if not results:
        print("未发现词库中的违禁/限制词。")
        return
    print("| 风险 | 位置 | 命中 | 分类 | 原文 | 替换建议 |")
    print("|---|---|---|---|---|---|")
    for r in sorted(results, key=lambda r: (RISK_RANK[r["risk"]], r["line"], r["column"])):
        sug = "、".join(r["suggestions"]) or "删除或改写"
        ctx = r["context"].replace("|", "\\|")
        print(f"| {r['risk']} | L{r['line']}:{r['column']} | {r['matched']} | {r['industry_title']}·{r['category']} | {ctx} | {sug} |")


def main(argv=None):
    default_dir = Path(__file__).resolve().parent.parent / "references"
    p = argparse.ArgumentParser(description="小红书违禁词检测")
    p.add_argument("files", nargs="*", help="要检测的文件；不填则读取 --text 或标准输入")
    p.add_argument("--text", help="直接检测一段文字")
    p.add_argument("--wordlist-dir", default=str(default_dir), help="词库目录（默认 ../references）")
    p.add_argument("--industry", help="只启用指定行业（逗号分隔，如 beauty,food）；通用词库 general 始终启用")
    p.add_argument("--no-general", action="store_true", help="不启用通用词库")
    p.add_argument("--min-risk", choices=RISK_LEVELS, default="低危", help="只报告该等级及以上（默认全部）")
    p.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p.add_argument("--annotate", action="store_true", help="输出标注后的原文（违禁词用【】标出）")
    p.add_argument("--list-industries", action="store_true", help="列出可用行业词库")
    args = p.parse_args(argv)

    lists = load_all(args.wordlist_dir)
    if not lists:
        sys.exit(f"未在 {args.wordlist_dir} 找到词库 *.txt")

    if args.list_industries:
        for key, (title, terms) in lists.items():
            print(f"{key:<12} {title}（{len(terms)} 条）")
        return 0

    selected = set(lists)
    if args.industry:
        wanted = {s.strip() for s in args.industry.split(",") if s.strip()}
        unknown = wanted - set(lists)
        if unknown:
            sys.exit(f"未知行业：{', '.join(sorted(unknown))}。可用：{', '.join(lists)}")
        selected = wanted | ({"general"} & set(lists))
    if args.no_general:
        selected.discard("general")
    terms = [t for key in lists if key in selected for t in lists[key][1]]

    sources = []
    if args.text is not None:
        sources.append(("输入文本", args.text))
    for f in args.files:
        sources.append((f, Path(f).read_text(encoding="utf-8")))
    if not sources:
        if sys.stdin.isatty():
            p.print_help()
            return 0
        sources.append(("标准输入", sys.stdin.read()))

    has_high = False
    json_out = []
    for name, text in sources:
        results = scan(text, terms, args.min_risk)
        has_high = has_high or any(r["risk"] == "高危" for r in results)
        if args.format == "json":
            json_out.append({"source": name, "summary": summary_counts(results), "hits": results,
                             **({"annotated": annotate(text, results)} if args.annotate else {})})
            continue
        if args.format == "markdown":
            print_markdown(results, name)
        else:
            print_text(results, name)
        if args.annotate:
            print("----- 标注原文 -----")
            print(annotate(text, results))
            print()
    if args.format == "json":
        print(json.dumps(json_out if len(json_out) > 1 else json_out[0], ensure_ascii=False, indent=2))
    return 1 if has_high else 0


if __name__ == "__main__":
    sys.exit(main())
