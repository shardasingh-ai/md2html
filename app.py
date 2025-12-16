import re
import io
import tempfile
from pathlib import Path

import streamlit as st
import markdown as mdlib
from bs4 import BeautifulSoup

# Playwright for PDF
from playwright.sync_api import sync_playwright


# ============================================================
# 1) YOUR STANDARD CSS (FINAL)
# ============================================================
STANDARD_CSS = r"""
@page { size: A4; margin: 14mm 12mm; }
html, body { height: 100%; }
body{
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  color: #0f2433;
  text-rendering: geometricPrecision;
  -webkit-font-smoothing: antialiased;
}
.book{ width: 100%; }
.prose{
  column-count: 2;
  column-gap: 18mm;
  column-fill: auto;
  column-rule: 1px solid rgba(15,36,51,.10);
  font-size: 12.2px;
  line-height: 1.55;
}
.prose *{ box-sizing: border-box; }
.prose p{ margin: 0 0 8px 0; }
.prose strong{ font-weight: 800; }

/* Main header */
.prose h1{
  column-span: all;
  -webkit-column-span: all;
  margin: 0 0 18px 0;
  padding: 28px 22px;
  min-height: 108px;
  display:flex;
  align-items:center;
  justify-content:center;
  text-align:center;

  background: linear-gradient(180deg, rgba(74,107,135,.22) 0%, rgba(74,107,135,.12) 100%);
  border: 1px solid rgba(15,36,51,.12);
  border-left: 12px solid rgba(74,107,135,.86);
  border-radius: 16px;

  font-weight: 950;
  letter-spacing: .12em;
  text-transform: uppercase;
  font-size: 34px;
  line-height: 1.12;

  box-shadow: 0 12px 26px rgba(15,36,51,.12);
}

/* Default headings */
.prose h2{
  column-span: none !important;
  -webkit-column-span: none !important;
  display:block;
  margin: 14px 0 10px 0;
  padding: 10px 12px;

  background: rgba(74,107,135,.10);
  border: 1px solid rgba(15,36,51,.10);
  border-left: 8px solid rgba(74,107,135,.70);
  border-radius: 12px;

  font-weight: 900;
  letter-spacing: .01em;
}
.prose h3{ margin: 12px 0 8px 0; font-weight: 900; }
.prose h4{ margin: 10px 0 6px 0; font-weight: 900; }
.prose h5{ margin: 9px 0 6px 0; font-weight: 900; }
.prose h6{ margin: 9px 0 6px 0; font-weight: 900; }

/* Topic titles: strong differentiator */
.prose h2.topic-title{
  padding: 16px 14px 14px 16px !important;
  margin: 14px 0 12px 0 !important;
  border-radius: 18px !important;
  border: 1px solid rgba(15,36,51,.12) !important;

  background: linear-gradient(135deg, rgba(26,152,202,.16) 0%, rgba(47,125,74,.10) 55%, rgba(92,56,181,.10) 100%) !important;
  box-shadow: 0 14px 28px rgba(15,36,51,.10) !important;

  border-left: 0 !important;
  font-weight: 950 !important;
  font-size: 18.2px !important;
  line-height: 1.22 !important;
  position: relative;
}
.prose h2.topic-title::before{
  content: "TOPIC";
  display:inline-block;
  font-size: 10px;
  letter-spacing: .20em;
  font-weight: 900;
  color: rgba(15,36,51,.60);
  background: rgba(255,255,255,.55);
  border: 1px solid rgba(15,36,51,.10);
  padding: 4px 8px;
  border-radius: 999px;
  margin-right: 10px;
  vertical-align: middle;
}
.prose h2.topic-title::after{
  content:"";
  position:absolute;
  left:16px;
  right:16px;
  bottom:10px;
  height:2px;
  background: rgba(15,36,51,.18);
  border-radius: 999px;
}

/* Lists */
.prose ul{ margin: 6px 0 8px 0; padding-left: 16px; }
.prose li{ margin: 4px 0; }
.prose li::marker{ color: rgba(15,36,51,.55); }

.prose hr{
  border: none;
  height: 1px;
  background: rgba(15,36,51,.18);
  margin: 18px 0;
}

/* Premium pastel palette */
:root{
  --blue-bg:  rgba(43,106,164,.10);
  --blue-bar: rgba(43,106,164,.80);

  --green-bg: rgba(47,125,74,.10);
  --amber-bg: rgba(176,106,0,.11);
  --violet-bg: rgba(92,56,181,.10);

  --green-top: rgba(47,125,74,.35);
  --amber-top: rgba(176,106,0,.35);
  --violet-top: rgba(92,56,181,.35);
}

.colorbox{
  padding: 10px 12px;
  border-radius: 16px;
  margin: 8px 0 10px 0;
  border: 1px solid rgba(15,36,51,.10);
  box-shadow: 0 10px 24px rgba(15,36,51,.08);
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;

  print-color-adjust: exact;
  -webkit-print-color-adjust: exact;

  background-image: radial-gradient(rgba(255,255,255,.35) 1px, transparent 1px);
  background-size: 18px 18px;
}
.colorbox + .colorbox{ margin-top: 12px !important; }

/* Section 1 & 2 keep left accent (blue) */
.colorbox.syllabus, .colorbox.context{
  background-color: var(--blue-bg) !important;
  border-left: 10px solid var(--blue-bar) !important;
}

/* Section 4/5/6: shaded only (no left accent bar) */
.colorbox.beyond{
  background-color: var(--green-bg) !important;
  border-left: 0 !important;
  border-top: 6px solid var(--green-top) !important;
}
.colorbox.prelims{
  background-color: var(--amber-bg) !important;
  border-left: 0 !important;
  border-top: 6px solid var(--amber-top) !important;
}
.colorbox.mains{
  background-color: var(--violet-bg) !important;
  border-left: 0 !important;
  border-top: 6px solid var(--violet-top) !important;
}

/* Heading chips inside boxes */
.colorbox > h2, .colorbox > h3, .colorbox > h4, .colorbox > h5, .colorbox > h6{
  display:block;
  padding: 10px 12px;
  border-radius: 12px;
  margin: 0 0 8px 0;
  border: 1px solid rgba(15,36,51,.10);
  background: rgba(255,255,255,.60);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.40);
  font-weight: 950;
}

/* Subtle tint per section */
.colorbox.syllabus > h2, .colorbox.syllabus > h3, .colorbox.syllabus > h4,
.colorbox.context  > h2, .colorbox.context  > h3, .colorbox.context  > h4{
  background: rgba(43,106,164,.14) !important;
}
.colorbox.beyond > h2, .colorbox.beyond > h3, .colorbox.beyond > h4{
  background: rgba(47,125,74,.14) !important;
}
.colorbox.prelims > h2, .colorbox.prelims > h3, .colorbox.prelims > h4, .colorbox.prelims > h5{
  background: rgba(176,106,0,.15) !important;
}
.colorbox.mains > h2, .colorbox.mains > h3, .colorbox.mains > h4, .colorbox.mains > h5, .colorbox.mains > h6{
  background: rgba(92,56,181,.14) !important;
}

/* Splittable table */
.gridtable{
  display:block;
  width: 100%;
  border: 1px solid rgba(15,36,51,.12);
  border-radius: 12px;
  background: rgba(255,255,255,.85);
  overflow: visible;
  -webkit-box-decoration-break: clone;
  box-decoration-break: clone;
}
.gridtable .gt-row{ display:block; }
.gridtable .gt-cell{
  display:inline-block;
  width: 34%;
  vertical-align: top;
  padding: 8px 10px;
  border-top: 1px solid rgba(15,36,51,.08);
  border-right: 1px solid rgba(15,36,51,.08);
  box-sizing: border-box;
  font-size: 0.95em;
}
.gridtable .gt-row .gt-cell:last-child{ width: 66%; border-right: none; }
.gridtable .gt-head .gt-cell{
  font-weight: 900;
  background: rgba(15,36,51,.04);
  border-top: none;
  letter-spacing: .02em;
}
"""


# ============================================================
# 2) Core renderer (MD -> HTML with boxes + grid tables)
# ============================================================
SECTION_RE = re.compile(r"^\s*([1-6])\.\s+", re.I)

def cleanup_markdown(md: str) -> str:
    md = re.sub(r"(?m)^\s*#{1,6}\s*$\n?", "", md)  # remove empty headings
    md = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>~])", r"\1", md)  # unescape markdown punctuation

    # ensure blank line after table row if next is heading
    lines = md.splitlines()
    out = []
    for i, line in enumerate(lines):
        out.append(line)
        if re.match(r"^\s*\|.*\|\s*$", line):
            if i + 1 < len(lines):
                nxt = lines[i + 1]
                if nxt.strip() and re.match(r"^\s*#{1,6}\s+\S", nxt):
                    out.append("")
    return "\n".join(out)

def heading_text(h) -> str:
    return re.sub(r"\s+", " ", h.get_text(" ", strip=True)).strip()

def is_heading(node) -> bool:
    return getattr(node, "name", None) in ("h1", "h2", "h3", "h4", "h5", "h6")

def is_section_heading(h) -> bool:
    return bool(SECTION_RE.match(heading_text(h)))

def section_num(h):
    m = SECTION_RE.match(heading_text(h))
    return int(m.group(1)) if m else None

def is_topic_title(h) -> bool:
    return h.name == "h2" and not is_section_heading(h) and heading_text(h) != ""

def tables_to_gridtables(soup: BeautifulSoup) -> None:
    def append_fragment(tag, fragment_html: str):
        frag = BeautifulSoup(fragment_html or "", "html.parser")
        for child in list(frag.contents):
            tag.append(child)

    for tbl in soup.find_all("table"):
        headers = []
        thead = tbl.find("thead")
        if thead:
            headers = [th.get_text(" ", strip=True) for th in thead.find_all("th")]

        rows = []
        tbody = tbl.find("tbody")
        if tbody:
            for tr in tbody.find_all("tr"):
                cells = tr.find_all(["td", "th"])
                rows.append([c.decode_contents().strip() for c in cells])

        gt = soup.new_tag("div", **{"class": "gridtable"})
        head = soup.new_tag("div", **{"class": "gt-row gt-head"})

        use_headers = headers[:2] if headers else ["Category", "Fact / Detail"]
        for h in use_headers:
            cell = soup.new_tag("div", **{"class": "gt-cell"})
            cell.string = h
            head.append(cell)
        gt.append(head)

        for r in rows:
            if not r:
                continue
            while len(r) < 2:
                r.append("")
            row = soup.new_tag("div", **{"class": "gt-row"})
            c1 = soup.new_tag("div", **{"class": "gt-cell"})
            append_fragment(c1, r[0])
            c2 = soup.new_tag("div", **{"class": "gt-cell"})
            append_fragment(c2, r[1])
            row.append(c1); row.append(c2)
            gt.append(row)

        tbl.replace_with(gt)

def wrap_sections_and_tag_topics(soup: BeautifulSoup) -> None:
    # tag topic titles
    for h2 in soup.find_all("h2"):
        if is_topic_title(h2):
            h2["class"] = (h2.get("class", []) + ["topic-title"])

    num_to_class = {1: "syllabus", 2: "context", 4: "beyond", 5: "prelims", 6: "mains"}
    headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

    def already_in_box(h):
        return h.find_parent(class_="colorbox") is not None

    def wrap_from(start_h, class_name: str):
        if already_in_box(start_h):
            return
        box = soup.new_tag("div", **{"class": f"colorbox {class_name}"})
        start_h.insert_before(box)

        cur = start_h
        while cur is not None:
            nxt = cur.next_sibling

            if cur is not start_h:
                if getattr(cur, "name", None) == "hr":
                    break
                if is_heading(cur) and (is_topic_title(cur) or is_section_heading(cur)):
                    break

            box.append(cur.extract())
            cur = nxt

    for h in headings:
        if not is_heading(h) or already_in_box(h):
            continue
        if is_section_heading(h):
            n = section_num(h)
            if n in num_to_class:
                wrap_from(h, num_to_class[n])

def md_to_html(md_text: str, title_fallback: str = "NIRNAY DAILY CA") -> str:
    md_text = cleanup_markdown(md_text)
    body = mdlib.markdown(md_text, extensions=["tables"])
    body = re.sub(r"<p>\s*######\s*</p>\s*", "", body, flags=re.I)

    soup = BeautifulSoup(body, "html.parser")
    tables_to_gridtables(soup)
    wrap_sections_and_tag_topics(soup)

    h1 = soup.find("h1")
    doc_title = h1.get_text(" ", strip=True).upper() if h1 else title_fallback.upper()

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{doc_title}</title>
  <style>{STANDARD_CSS}</style>
</head>
<body>
  <article class="book">
    <div class="prose">
      {str(soup)}
    </div>
  </article>
</body>
</html>
"""


# ============================================================
# 3) HTML -> PDF (Playwright)
# ============================================================
def html_to_pdf_bytes(html: str) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        html_path = td / "doc.html"
        html_path.write_text(html, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(html_path.as_uri(), wait_until="networkidle")

            pdf_bytes = page.pdf(
                format="A4",
                print_background=True,
                margin={"top": "14mm", "bottom": "14mm", "left": "12mm", "right": "12mm"},
            )
            browser.close()

        return pdf_bytes


# ============================================================
# 4) Streamlit UI
# ============================================================
st.set_page_config(page_title="Nirnay MD → HTML/PDF", layout="centered")

st.title("Nirnay Daily CA — Markdown to HTML + PDF")
st.caption("Upload a .md file → get consistent 2-column Nirnay HTML + PDF downloads.")

uploaded = st.file_uploader("Upload Markdown file", type=["md", "markdown"])

if uploaded:
    md_text = uploaded.read().decode("utf-8", errors="ignore")
    base_name = Path(uploaded.name).stem

    html = md_to_html(md_text, title_fallback=base_name)

    st.success("Rendered HTML successfully.")

    # Preview
    with st.expander("Preview (HTML)", expanded=False):
        st.components.v1.html(html, height=650, scrolling=True)

    # Download HTML
    st.download_button(
        "Download HTML",
        data=html.encode("utf-8"),
        file_name=f"{base_name}_nirnay.html",
        mime="text/html",
    )

    # PDF generation
    if st.button("Generate PDF"):
        try:
            pdf_bytes = html_to_pdf_bytes(html)
            st.download_button(
                "Download PDF",
                data=pdf_bytes,
                file_name=f"{base_name}_nirnay.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(
                "PDF generation failed. If you're running locally, make sure Playwright "
                "and Chromium are installed:\n\n"
                "python -m playwright install chromium\n\n"
                f"Error: {e}"
            )
