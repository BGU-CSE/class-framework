"""Extractors: one source file in, Markdown with explicit anchors out (spec §8.7).

Conversion is code, not agent work (D-018): it must produce **the same anchors every time**,
or locators rot. Each format's anchor:

    PPTX                    one `## Slide N` per slide, N = position in the deck
    PDF                     one `## Page N` per page, N = physical page (1-based)
    DOCX, MD, and pandoc    the document's own headings
    TXT                     none — a plain-text file has no structure to point into

Adding a format is one function registered by extension (`@register`) — an extension point
like adding a methodology. Anything without an extractor is recorded `unsupported` with a hint,
never dropped; audio and video are `media`; a PDF with no text layer is `no-text`.

The third-party readers (python-pptx, python-docx, pypdf) are imported inside the functions
that use them, so `classkit validate` — which imports this package to compare hashes — does
not pay for them.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

INGESTED = "ingested"
UNSUPPORTED = "unsupported"
NO_TEXT = "no-text"
MEDIA = "media"
LINK = "link"

#: Below this many non-blank characters per page on average, a PDF is treated as having no
#: text layer (a scan). A scan often carries a few stray characters — page numbers, a stamp.
NO_TEXT_CHARS_PER_PAGE = 10

MEDIA_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv",
    ".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac",
}

_URL = re.compile(r"https?://[^\s<>\"'`\]\[)(]+", re.I)
_URL_TRAILING = ".,;:!?'\""


@dataclass
class Extraction:
    """What an extractor produced from one source file."""

    status: str
    body: str = ""
    title: str = ""
    #: URLs found inside the material, each with the anchor it was found under ("" if none)
    links: list[tuple[str, str]] = field(default_factory=list)
    reason: str = ""
    #: anchor → one-line labels for a private material's index (D-040): a slide's title, a
    #: page's printed label and the sections that start on it. Never body text.
    labels: dict[str, list[str]] = field(default_factory=dict)
    #: True when `title` was taken from the body text (a PDF's or a text file's first line)
    #: rather than a heading, a slide title or metadata — so a private material does not carry
    #: a line of its text into the committed manifest and index
    title_from_body: bool = False


@dataclass
class Probe:
    """What the pre-flight report can learn about a file without converting it."""

    slides: int = 0
    pages: int = 0
    links: int = 0
    status: str = INGESTED  # the status conversion is expected to produce
    reason: str = ""


@dataclass
class Extractor:
    extract: Callable[[Path], Extraction]
    probe: Callable[[Path], Probe]
    #: rough seconds per file, for the pre-flight time estimate
    seconds: float = 0.2


#: The registry: file extension (lowercase, with the dot) → extractor.
EXTRACTORS: dict[str, Extractor] = {}


def register(*extensions: str, probe: Callable[[Path], Probe] | None = None, seconds: float = 0.2):
    """Register an extractor for one or more extensions — how a format is added."""

    def decorate(function: Callable[[Path], Extraction]):
        for extension in extensions:
            EXTRACTORS[extension.lower()] = Extractor(function, probe or (lambda _p: Probe()), seconds)
        return function

    return decorate


def format_of(path: Path) -> str:
    return path.suffix.lower().lstrip(".") or "none"


def extract(path: Path) -> Extraction:
    """Convert one file. Never raises for a bad file: an unreadable one is `unsupported`."""
    extension = path.suffix.lower()
    if extension in MEDIA_EXTENSIONS:
        return Extraction(MEDIA, title=path.stem,
                          reason="audio/video: recorded, content not extracted in Core")
    extractor = EXTRACTORS.get(extension)
    if extractor is None:
        return Extraction(UNSUPPORTED, title=path.stem, reason=_unsupported_hint(extension))
    try:
        result = extractor.extract(path)
    except Exception as exc:  # a corrupt or password-protected file must not stop the run
        return Extraction(UNSUPPORTED, title=path.stem,
                          reason=f"could not be read ({type(exc).__name__}: {exc}); "
                                 "try exporting it to PDF")
    result.title = _clean(result.title) or path.stem
    return result


def probe(path: Path) -> Probe:
    """Cheap facts for the pre-flight report: slide/page/link counts, expected status."""
    extension = path.suffix.lower()
    if extension in MEDIA_EXTENSIONS:
        return Probe(status=MEDIA, reason="audio/video: recorded, content not extracted")
    extractor = EXTRACTORS.get(extension)
    if extractor is None:
        return Probe(status=UNSUPPORTED, reason=_unsupported_hint(extension))
    try:
        return extractor.probe(path)
    except Exception as exc:
        return Probe(status=UNSUPPORTED, reason=f"could not be read ({type(exc).__name__})")


def seconds_for(path: Path) -> float:
    extractor = EXTRACTORS.get(path.suffix.lower())
    return extractor.seconds if extractor else 0.0


# -- anchors -----------------------------------------------------------------

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$")
_FENCE = re.compile(r"^[ \t]*(```|~~~)")


def slug(text: str) -> str:
    """A heading's anchor: lowercased, every run of non-word characters → '-'.

    `Slide 18` → `slide-18`, `Question 3: heaps` → `question-3-heaps`. Unicode letters are kept,
    so a heading in another script still gets an anchor.
    """
    return re.sub(r"[\W_]+", "-", text.lower()).strip("-")


def headings(markdown: str) -> list[tuple[int, str]]:
    """Every ATX heading outside fenced code blocks: (level, text)."""
    found: list[tuple[int, str]] = []
    fenced = False
    for line in markdown.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = _HEADING.match(line)
        if match:
            found.append((len(match.group(1)), match.group(2)))
    return found


def anchors(markdown: str) -> list[str]:
    """The anchors a locator can name in this document, in order.

    A repeated heading gets `-1`, `-2`, … appended, as GitHub's Markdown renderer does, so the
    anchor a teacher sees in a preview is the one a locator uses.
    """
    seen: dict[str, int] = {}
    result: list[str] = []
    for _level, text in headings(markdown):
        base = slug(text)
        if not base:
            continue
        if base in seen:
            seen[base] += 1
            result.append(f"{base}-{seen[base]}")
        else:
            seen[base] = 0
            result.append(base)
    return result


#: A label in an index is one line, and short: it names a place, it does not quote it.
LABEL_CHARS = 120


def label(text: str) -> str:
    """One index label: a single line, at most LABEL_CHARS, never a heading."""
    text = _clean(text)
    if len(text) > LABEL_CHARS:
        text = text[:LABEL_CHARS - 1].rstrip() + "…"
    return _escape_heading(text)


def index_body(markdown: str, labels: dict[str, list[str]]) -> str:
    """The index of a private material (D-040): every anchor heading the full text has, in the
    same order and so with the same anchors, each followed only by its one-line labels. No body
    text — this is what is committed for a file whose text may not be."""
    lines: list[str] = []
    seen: dict[str, int] = {}
    for level, text in headings(markdown):
        lines += [f"{'#' * level} {text}", ""]
        base = slug(text)
        if not base:
            continue
        if base in seen:
            seen[base] += 1
            anchor = f"{base}-{seen[base]}"
        else:
            seen[base] = 0
            anchor = base
        for line in labels.get(anchor, []):
            lines += [line, ""]
    return "\n".join(lines).rstrip() + "\n" if lines else ""


def find_urls(text: str) -> list[str]:
    urls = []
    for match in _URL.finditer(text):
        url = match.group(0).rstrip(_URL_TRAILING)
        if url not in urls:
            urls.append(url)
    return urls


def _clean(text: str | None) -> str:
    return " ".join(str(text or "").split())


# Metadata titles that are really the authoring tool talking, not the author.
_JUNK_TITLE = re.compile(r"^(powerpoint presentation|presentation\d*|untitled.*|slide \d+|"
                         r"microsoft (word|powerpoint) - .*|document\d*)$", re.I)


def _title_from_metadata(value: str | None) -> str:
    value = _clean(value)
    return "" if not value or _JUNK_TITLE.match(value) else value


# -- built in: Markdown and plain text ----------------------------------------

def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1")


def _markdown_probe(path: Path) -> Probe:
    return Probe(links=len(find_urls(_read_text(path))))


@register(".md", ".markdown", probe=_markdown_probe, seconds=0.01)
def extract_markdown(path: Path) -> Extraction:
    text = _read_text(path).replace("\r\n", "\n")
    found = headings(text)
    title = found[0][1] if found else ""
    links = _links_by_anchor(text)
    return Extraction(INGESTED, body=text.rstrip() + "\n", title=title, links=links)


@register(".txt", ".text", probe=_markdown_probe, seconds=0.01)
def extract_text(path: Path) -> Extraction:
    text = _read_text(path).replace("\r\n", "\n")
    # A plain-text file has no headings, so it has no anchors: it is cited by its id alone.
    # A line that happens to start with '#' must not become one, so it is escaped.
    body = "\n".join(("\\" + line) if line.lstrip().startswith("#") else line
                     for line in text.splitlines())
    first = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return Extraction(INGESTED, body=body.rstrip() + "\n", title=first[:80],
                      links=[(u, "") for u in find_urls(text)], title_from_body=True)


def _links_by_anchor(markdown: str) -> list[tuple[str, str]]:
    """URLs in a Markdown document, each with the anchor of the heading it sits under."""
    found: list[tuple[str, str]] = []
    current = ""
    names = iter(anchors(markdown))
    fenced = False
    for line in markdown.splitlines():
        if _FENCE.match(line):
            fenced = not fenced
        elif not fenced and _HEADING.match(line) and slug(_HEADING.match(line).group(2)):
            current = next(names, current)
            continue
        for url in find_urls(line):
            if all(url != u for u, _ in found):
                found.append((url, current))
    return found


# -- built in: PowerPoint -----------------------------------------------------

def _pptx_probe(path: Path) -> Probe:
    import zipfile  # noqa: PLC0415

    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        slides = sum(1 for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n))
        links = _count_external_links(archive, r"ppt/slides/_rels/slide\d+\.xml\.rels")
    return Probe(slides=slides, links=links)


def _count_external_links(archive, pattern: str) -> int:
    total = 0
    for name in archive.namelist():
        if re.fullmatch(pattern, name):
            xml = archive.read(name).decode("utf-8", "replace")
            total += len(re.findall(r'relationships/hyperlink"[^>]*TargetMode="External"', xml))
            total += len(re.findall(r'TargetMode="External"[^>]*relationships/hyperlink"', xml))
    return total


@register(".pptx", probe=_pptx_probe, seconds=0.05)
def extract_pptx(path: Path) -> Extraction:
    from pptx import Presentation  # noqa: PLC0415

    deck = Presentation(str(path))
    lines: list[str] = []
    links: list[tuple[str, str]] = []
    labels: dict[str, list[str]] = {}
    first_title = ""

    for number, slide in enumerate(deck.slides, start=1):
        anchor = f"slide-{number}"
        start = len(lines)
        lines += [f"## Slide {number}", ""]
        if slide._element.get("show") == "0":
            lines += ["*(hidden slide)*", ""]
            labels.setdefault(anchor, []).append("*(hidden slide)*")

        title_shape = slide.shapes.title
        title = _clean(title_shape.text_frame.text) if title_shape is not None and title_shape.has_text_frame else ""
        if title:
            first_title = first_title or title
            lines += [f"**{title}**", ""]
            labels.setdefault(anchor, []).append(f"**{label(title)}**")

        for shape in _shapes(slide.shapes):
            if title_shape is not None and shape.shape_id == title_shape.shape_id:
                continue
            if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = _clean("".join(run.text for run in paragraph.runs))
                    for run in paragraph.runs:
                        address = run.hyperlink.address if run.hyperlink is not None else None
                        if address:
                            links.append((address, anchor))
                    if text:
                        lines.append(("  " * paragraph.level) + f"- {_escape_heading(text)}")
                lines.append("")
            if getattr(shape, "has_table", False) and shape.has_table:
                lines += _table_rows([[cell.text for cell in row.cells] for row in shape.table.rows])
                lines.append("")
            click = getattr(shape, "click_action", None)
            address = getattr(getattr(click, "hyperlink", None), "address", None) if click else None
            if address:
                links.append((address, anchor))

        if slide.has_notes_slide:
            notes = slide.notes_slide.notes_text_frame.text.strip() if slide.notes_slide.notes_text_frame else ""
            if notes:
                lines.append("> **Notes:** " + " ".join(notes.split()))
                lines.append("")

        for url in find_urls("\n".join(lines[start:])):
            links.append((url, anchor))

    title = first_title or _title_from_metadata(deck.core_properties.title)
    return Extraction(INGESTED, body="\n".join(lines).rstrip() + "\n", title=title,
                      links=_unique(links), labels=labels)


def _shapes(shapes):
    """Every shape, descending into groups, in slide order."""
    for shape in shapes:
        if getattr(shape, "shape_type", None) == 6:  # MSO_SHAPE_TYPE.GROUP
            yield from _shapes(shape.shapes)
        else:
            yield shape


# -- built in: PDF (text layer) -----------------------------------------------

def _pdf_probe(path: Path) -> Probe:
    from pypdf import PdfReader  # noqa: PLC0415

    reader = PdfReader(str(path))
    links = 0
    for page in reader.pages:
        for annotation in page.get("/Annots") or []:
            obj = annotation.get_object()
            if obj.get("/Subtype") == "/Link" and "/URI" in (obj.get("/A") or {}):
                links += 1
    return Probe(pages=len(reader.pages), links=links)


@register(".pdf", probe=_pdf_probe, seconds=0.08)
def extract_pdf(path: Path) -> Extraction:
    from pypdf import PdfReader  # noqa: PLC0415

    reader = PdfReader(str(path))
    lines: list[str] = []
    links: list[tuple[str, str]] = []
    characters = 0
    printed = list(getattr(reader, "page_labels", []) or [])
    sections = _outline_by_page(reader)
    labels: dict[str, list[str]] = {}

    for index, page in enumerate(reader.pages):
        number = index + 1
        anchor = f"page-{number}"
        lines += [f"## Page {number}", ""]
        # Locators use the physical page, which always exists and never repeats. A printed
        # page number that differs (front matter, a textbook's own numbering) is noted, so a
        # teacher citing "p. 45" can find page-63.
        page_label = printed[index] if index < len(printed) else str(number)
        if page_label and page_label != str(number):
            lines += [f"*(printed page {page_label})*", ""]
            labels.setdefault(anchor, []).append(f"*(printed page {label(page_label)})*")
        for title in sections.get(index, []):
            labels.setdefault(anchor, []).append(f"*(section: {label(title)})*")
        try:
            text = page.extract_text() or ""
        except Exception:  # one bad page must not lose the rest of the document
            text = ""
        characters += len("".join(text.split()))
        for line in text.splitlines():
            line = line.rstrip()
            lines.append(_escape_heading(line) if line else "")
        lines.append("")
        for url in find_urls(text):
            links.append((url, anchor))
        for annotation in page.get("/Annots") or []:
            obj = annotation.get_object()
            action = obj.get("/A") or {}
            if obj.get("/Subtype") == "/Link" and "/URI" in action:
                links.append((str(action["/URI"]), anchor))

    pages = len(reader.pages)
    metadata_title = _title_from_metadata((reader.metadata or {}).get("/Title"))
    body = "\n".join(lines).rstrip() + "\n"

    if pages == 0 or characters < NO_TEXT_CHARS_PER_PAGE * pages:
        # Scanned: no text to extract. The page headings are still written, so a locator to a
        # page that exists resolves, and the teacher may type in the text by hand.
        return Extraction(NO_TEXT, body=body, title=metadata_title, links=_unique(links),
                          reason="no text layer (a scan?) — OCR is not done in Core; "
                                 "pages are anchored, the text is empty", labels=labels)

    first_line = next((ln.strip() for ln in lines if ln.strip() and not ln.startswith(("## ", "*("))), "")
    return Extraction(INGESTED, body=body, title=metadata_title or first_line[:80],
                      links=_unique(links), labels=labels, title_from_body=not metadata_title)


def _outline_by_page(reader) -> dict[int, list[str]]:
    """The PDF's outline (bookmarks) as page index → titles of the sections starting there, in
    outline order. Empty for a PDF without one — a scan, some exports — or a broken one: the
    index then has pages and printed labels only."""
    found: dict[int, list[str]] = {}

    def walk(items) -> None:
        for item in items:
            if isinstance(item, list):
                walk(item)
                continue
            try:
                page = reader.get_destination_page_number(item)
            except Exception:  # a dangling or malformed bookmark names no page
                continue
            title = _clean(getattr(item, "title", None) or "")
            if title and page is not None and page >= 0:
                found.setdefault(page, []).append(title)

    try:
        walk(reader.outline or [])
    except Exception:
        return {}
    return found


# -- built in: Word -----------------------------------------------------------

def _docx_probe(path: Path) -> Probe:
    import zipfile  # noqa: PLC0415

    with zipfile.ZipFile(path) as archive:
        links = _count_external_links(archive, r"word/_rels/document\.xml\.rels")
    return Probe(links=links)


@register(".docx", probe=_docx_probe, seconds=0.2)
def extract_docx(path: Path) -> Extraction:
    import docx  # noqa: PLC0415
    from docx.oxml.ns import qn  # noqa: PLC0415
    from docx.table import Table  # noqa: PLC0415
    from docx.text.paragraph import Paragraph  # noqa: PLC0415

    document = docx.Document(str(path))
    lines: list[str] = []
    first_heading = ""

    body = document.element.body
    for child in body.iterchildren():
        if child.tag == qn("w:p"):
            paragraph = Paragraph(child, document)
            text = _clean(paragraph.text)
            if not text:
                continue
            level = _heading_level(paragraph.style.name if paragraph.style is not None else "")
            if level:
                first_heading = first_heading or text
                lines += ["", f"{'#' * level} {text}", ""]
            elif (paragraph.style is not None and "List" in paragraph.style.name):
                lines.append(f"- {_escape_heading(text)}")
            else:
                lines += [_escape_heading(text), ""]
        elif child.tag == qn("w:tbl"):
            table = Table(child, document)
            lines += [""] + _table_rows([[cell.text for cell in row.cells] for row in table.rows]) + [""]

    markdown = "\n".join(lines).strip() + "\n"
    markdown = re.sub(r"\n{3,}", "\n\n", markdown)

    hyperlinks = [
        rel.target_ref
        for rel in document.part.rels.values()
        if rel.reltype.endswith("/hyperlink") and rel.is_external
    ]
    links = _links_by_anchor(markdown)
    for url in hyperlinks:
        if all(url != u for u, _ in links):
            links.append((url, ""))

    title = first_heading or _title_from_metadata(document.core_properties.title)
    return Extraction(INGESTED, body=markdown, title=title, links=links)


def _heading_level(style: str) -> int:
    if style == "Title":
        return 1
    match = re.fullmatch(r"Heading (\d)", style)
    return min(int(match.group(1)), 6) if match else 0


# -- optional: pandoc and LibreOffice, used only when installed ---------------

PANDOC_EXTENSIONS = {".odt": "odt", ".rtf": "rtf", ".html": "html", ".htm": "html", ".epub": "epub"}
LIBREOFFICE_EXTENSIONS = {".ppt": "pptx", ".odp": "pptx", ".doc": "docx"}


def pandoc() -> str | None:
    return shutil.which("pandoc")


def libreoffice() -> str | None:
    return shutil.which("soffice") or shutil.which("libreoffice")


def _unsupported_hint(extension: str) -> str:
    if extension in PANDOC_EXTENSIONS:
        return "install pandoc to read this format, or export it to PDF"
    if extension in LIBREOFFICE_EXTENSIONS:
        return "install LibreOffice to read this format, or export it to PDF"
    if extension in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".tif", ".tiff", ".bmp", ".heic"}:
        return "an image: text in images is not extracted in Core (no OCR)"
    if extension in {".zip", ".tar", ".gz", ".7z", ".rar"}:
        return "an archive: unpack it into materials/source/ and re-run"
    if extension in {".xlsx", ".xls", ".csv", ".ods"}:
        return "a spreadsheet: no extractor in Core — export the relevant part to PDF"
    return "no extractor for this format — export it to PDF and re-run"


def _optional_probe(path: Path) -> Probe:
    extension = path.suffix.lower()
    if extension in PANDOC_EXTENSIONS and pandoc() is None:
        return Probe(status=UNSUPPORTED, reason=_unsupported_hint(extension))
    if extension in LIBREOFFICE_EXTENSIONS and libreoffice() is None:
        return Probe(status=UNSUPPORTED, reason=_unsupported_hint(extension))
    return Probe()


@register(*PANDOC_EXTENSIONS, probe=_optional_probe, seconds=1.0)
def extract_with_pandoc(path: Path) -> Extraction:
    tool = pandoc()
    if tool is None:
        return Extraction(UNSUPPORTED, reason=_unsupported_hint(path.suffix.lower()))
    source_format = PANDOC_EXTENSIONS[path.suffix.lower()]
    completed = subprocess.run(
        [tool, "--from", source_format, "--to", "gfm", "--wrap=none", str(path)],
        capture_output=True, text=True, timeout=300, check=True,
    )
    markdown = completed.stdout
    found = headings(markdown)
    return Extraction(INGESTED, body=markdown.rstrip() + "\n", title=found[0][1] if found else "",
                      links=_links_by_anchor(markdown))


@register(*LIBREOFFICE_EXTENSIONS, probe=_optional_probe, seconds=4.0)
def extract_with_libreoffice(path: Path) -> Extraction:
    tool = libreoffice()
    if tool is None:
        return Extraction(UNSUPPORTED, reason=_unsupported_hint(path.suffix.lower()))
    target = LIBREOFFICE_EXTENSIONS[path.suffix.lower()]
    # Converted into a scratch directory — never next to the teacher's file in source/.
    with tempfile.TemporaryDirectory(prefix="classkit-") as scratch:
        subprocess.run(
            [tool, "--headless", "--convert-to", target, "--outdir", scratch, str(path)],
            capture_output=True, timeout=300, check=True,
        )
        converted = Path(scratch) / f"{path.stem}.{target}"
        return EXTRACTORS[f".{target}"].extract(converted)


# -- helpers ------------------------------------------------------------------

def _escape_heading(text: str) -> str:
    """Body text that starts with '#' must not become a heading — it would invent an anchor."""
    return ("\\" + text) if text.lstrip().startswith("#") else text


def _table_rows(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    cleaned = [[_clean(cell).replace("|", "\\|") for cell in row] for row in rows]
    width = max(len(row) for row in cleaned)
    cleaned = [row + [""] * (width - len(row)) for row in cleaned]
    out = ["| " + " | ".join(cleaned[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(row) + " |" for row in cleaned[1:]]
    return out


def _unique(links: list[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    result = []
    for url, anchor in links:
        url = url.strip()
        if url and url not in seen:
            seen.add(url)
            result.append((url, anchor))
    return result
