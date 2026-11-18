#!/usr/bin/env python3
"""把 projects/*.md 转成同站可读的 .html。

为什么不用现成库：这套站点要能在国内网络直连打开，不依赖 GitHub 主站渲染、
也不引任何 CDN。一个零依赖的小转换器就够。

用法：python3 build.py
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
TPL = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · 冷饭</title>
<style>
  :root{{--paper:#faf8f5;--ink:#1c1a17;--ink-2:#57534c;--ink-3:#8a847a;--line:#e0dbd1;--accent:#8c3a26;--card:#fffdfa}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--paper);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;line-height:1.75;font-size:16px;padding:0 20px 80px}}
  .wrap{{max-width:720px;margin:0 auto}}
  a.back{{display:inline-block;margin:28px 0 0;font-size:13px;color:var(--ink-3);text-decoration:none;letter-spacing:.04em}}
  a.back:hover{{color:var(--accent)}}
  h1{{font-size:27px;line-height:1.3;font-weight:600;letter-spacing:-.01em;margin:20px 0 22px}}
  h2{{font-size:15px;letter-spacing:.06em;font-weight:600;margin:38px 0 12px;padding-top:18px;border-top:1px solid var(--line)}}
  h3{{font-size:15px;font-weight:600;margin:24px 0 8px}}
  p{{margin:12px 0;font-size:15.5px}}
  strong{{font-weight:600}}
  blockquote{{margin:0;padding:2px 0 2px 16px;border-left:2px solid var(--accent);color:var(--ink-2);font-size:15px}}
  ul,ol{{margin:12px 0 12px 20px}}
  li{{margin:6px 0;font-size:15.5px}}
  table{{width:100%;border-collapse:collapse;margin:16px 0;font-size:14px}}
  th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
  th{{background:#f3efe8;font-weight:600}}
  td img{{max-width:100%;height:auto;border:1px solid var(--line)}}
  code{{background:#f0ece5;padding:1px 5px;border-radius:2px;font-size:13.5px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
  pre{{background:#f3efe8;border:1px solid var(--line);padding:14px 16px;overflow-x:auto;margin:16px 0;border-radius:2px}}
  pre code{{background:none;padding:0;font-size:12.5px;line-height:1.6}}
  hr{{border:0;border-top:1px solid var(--line);margin:34px 0}}
  em{{color:var(--ink-3);font-style:normal;font-size:14px}}
  footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);font-size:13px;color:var(--ink-3)}}
  footer a{{color:var(--ink-2);text-decoration:none;border-bottom:1px solid var(--line)}}
</style>
</head>
<body><div class="wrap">
<a class="back" href="../index.html">← 全部项目</a>
{body}
<footer>冷饭 · <a href="../index.html">作品集</a> · <a href="https://github.com/linlin-alt">GitHub</a></footer>
</div></body></html>
"""

PROTECT = re.compile(r"(<img\b[^>]*>|<br\s*/?>|<b>|</b>)")


def inline(text: str) -> str:
    keep = []

    def stash(m):
        keep.append(m.group(1))
        return f"\x00{len(keep) - 1}\x00"

    text = PROTECT.sub(stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    for i, raw in enumerate(keep):
        text = text.replace(f"\x00{i}\x00", raw)
    return text


def convert(md: str) -> str:
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            continue

        if re.match(r"^#{1,3} ", ln):
            lvl = len(ln) - len(ln.lstrip("#"))
            out.append(f"<h{lvl}>{inline(ln[lvl + 1:])}</h{lvl}>")
            i += 1
            continue

        if ln.strip() == "---":
            out.append("<hr>")
            i += 1
            continue

        if ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i])
                i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            body = "".join(
                "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
                for r in cells
                if not all(re.fullmatch(r":?-{2,}:?", c or "-") for c in r)
            )
            head = cells[0]
            out.append(
                "<table><thead><tr>"
                + "".join(f"<th>{inline(c)}</th>" for c in head)
                + "</tr></thead><tbody>" + body + "</tbody></table>"
            )
            continue

        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue

        if re.match(r"^\s*[-*] ", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*] ", lines[i]):
                items.append(inline(re.sub(r"^\s*[-*] ", "", lines[i])))
                i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue

        if re.match(r"^\s*\d+\. ", ln):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\. ", lines[i]):
                items.append(inline(re.sub(r"^\s*\d+\. ", "", lines[i])))
                i += 1
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>")
            continue

        if not ln.strip():
            i += 1
            continue

        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,3} |\||>|```|\s*[-*] |\s*\d+\. )", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        para = " ".join(buf)
        out.append("<p><em>" + inline(para) + "</em></p>" if para.startswith("*") and para.endswith("*") and para.count("*") == 2 else "<p>" + inline(para) + "</p>")

    return "\n".join(out)


def main():
    for md in sorted((ROOT / "projects").glob("*.md")):
        text = md.read_text(encoding="utf-8")
        title = text.split("\n", 1)[0].lstrip("# ").strip()
        out = md.with_suffix(".html")
        out.write_text(TPL.format(title=title, body=convert(text)), encoding="utf-8")
        print(f"{md.name} -> {out.name}")


if __name__ == "__main__":
    main()
