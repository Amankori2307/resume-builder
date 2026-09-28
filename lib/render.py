#!/usr/bin/env python3
"""Render a resume profile into LaTeX and plain text.

A profile is a directory containing:
  resume.json    structured content (single source of truth)
  settings.json  documents, variants, formats, output naming

Everything the builder emits is derived from those two files, so the PDF and
the DOCX can never drift apart.

Subcommands:
  plan    print one TSV row per (document, variant) build target
  render  write the .tex and .txt for one (document, variant) pair
  check   validate a profile and report problems
"""

import argparse
import json
import os
import re
import sys

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# Order matters: the backslash rule has to run before the rules that insert
# backslashes of their own.
TEX_ESCAPES = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


class ProfileError(Exception):
    pass


# ---------------------------------------------------------------- utilities

def tex_escape(text):
    for char, replacement in TEX_ESCAPES:
        text = text.replace(char, replacement)
    return text


def tex_inline(text):
    """Escape for LaTeX, then turn **bold** into \\textbf{bold}."""
    return re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", tex_escape(text))


def txt_inline(text):
    """Strip the **bold** markers; plain text carries no emphasis."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", text)


def parse_date(value):
    """Accept 'YYYY-MM', 'YYYY', 'present' or null. Return (year, month)."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in ("present", "current", "now"):
        return None
    match = re.fullmatch(r"(\d{4})(?:-(\d{1,2}))?", text)
    if not match:
        raise ProfileError(
            f"bad date {value!r}: use 'YYYY-MM', 'YYYY', or 'Present'")
    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else None
    if month is not None and not 1 <= month <= 12:
        raise ProfileError(f"bad month in date {value!r}")
    return (year, month)


def format_date(value, style, precision="month", present="Present"):
    parsed = parse_date(value)
    if parsed is None:
        return present
    year, month = parsed
    if precision == "year" or month is None:
        return str(year)
    if style == "numeric":
        return f"{month:02d}/{year}"
    return f"{MONTHS[month - 1]} {year}"


def date_range(item, style, precision="month", dash=" - "):
    start = format_date(item.get("start"), style, precision)
    end = format_date(item.get("end"), style, precision)
    if not start:
        return end
    return f"{start}{dash}{end}"


def visible(obj, document_id, variant_id):
    """Honour the include_in (documents) and variants tags on any node."""
    if not isinstance(obj, dict):
        return True
    docs = obj.get("include_in")
    if docs is not None and document_id not in docs:
        return False
    variants = obj.get("variants")
    if variants is not None and variant_id not in variants:
        return False
    return True


def bullet_text(bullet):
    if isinstance(bullet, str):
        return bullet
    return bullet.get("text", "")


def load_json(path):
    if not os.path.isfile(path):
        raise ProfileError(f"missing required file: {path}")
    with open(path, encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            raise ProfileError(f"{path} is not valid JSON: {exc}") from exc


def load_profile(profile_dir):
    resume = load_json(os.path.join(profile_dir, "resume.json"))
    settings = load_json(os.path.join(profile_dir, "settings.json"))
    return resume, settings


def documents(settings):
    docs = settings.get("documents")
    if not docs:
        raise ProfileError("settings.json needs at least one entry in 'documents'")
    return docs


def variants(settings):
    return settings.get("variants") or [{"id": "default", "label": ""}]


def output_basename(document, variant):
    base = document.get("basename") or document["id"]
    label = variant.get("label")
    return f"{base}-{label}" if label else base


# ------------------------------------------------------------ tex rendering

def render_tex_header(basics, document_id, variant_id):
    lines = ["\\begin{center}"]
    lines.append(
        f"    {{\\Huge \\bfseries {tex_escape(basics.get('name', ''))}}}"
        " \\\\ \\vspace{1pt}")
    lines.append("    \\small")

    contacts = [c for c in basics.get("contact", [])
                if visible(c, document_id, variant_id)]
    rendered = []
    for entry in contacts:
        text = tex_escape(entry["text"] if isinstance(entry, dict) else entry)
        href = entry.get("href") if isinstance(entry, dict) else None
        rendered.append(f"\\href{{{href}}}{{{text}}}" if href else text)
    if rendered:
        lines.append("    " + " \\textbullet{} ".join(rendered) + " \\\\")

    links = [l for l in basics.get("links", [])
             if visible(l, document_id, variant_id)]
    parts = []
    for link in links:
        text = tex_escape(link.get("text", ""))
        body = f"\\href{{{link['href']}}}{{{text}}}" if link.get("href") else text
        label = link.get("label")
        parts.append(f"{tex_escape(label)}: {body}" if label else body)
    if parts:
        lines.append("    " + (" \\textbullet{}\n    ".join(parts)))

    lines.append("\\end{center}")
    return "\n".join(lines)


def render_tex_bullets(bullets, document_id, variant_id):
    visible_bullets = [b for b in bullets if visible(b, document_id, variant_id)]
    if not visible_bullets:
        return []
    out = ["\\resumeItemListStart"]
    for bullet in visible_bullets:
        out.append(f"\\resumeItem{{{tex_inline(bullet_text(bullet))}}}")
    out.append("\\resumeItemListEnd")
    return out


def render_tex_section(section, document_id, variant_id, settings):
    style = settings.get("dates", {}).get("tex_style", "numeric")
    kind = section.get("type", "experience")
    items = [i for i in section.get("items", [])
             if visible(i, document_id, variant_id)]
    if not items:
        return ""

    out = [f"\\section{{{tex_escape(section.get('title', '').upper())}}}"]
    overrides = section.get("_title_overrides", {})

    if kind in ("experience", "education"):
        out.append("\\resumeSubHeadingListStart")
        for item in items:
            precision = "month"
            title = overrides.get(item.get("id"), item.get("title", ""))
            dates = date_range(item, style, precision, dash=" - ")
            out.append("\\resumeSubheading")
            out.append(f"{{{tex_inline(item.get('organization', ''))}}}{{{dates}}}")
            out.append(f"{{{tex_inline(title)}}}{{{tex_escape(item.get('location', ''))}}}")
            bullets = render_tex_bullets(item.get("bullets", []),
                                         document_id, variant_id)
            # \resumeSubheading ends with a negative vspace that assumes a
            # bullet list follows; without one the next heading overlaps it.
            out.extend(bullets or ["\\vspace{7pt}"])
        out.append("\\resumeSubHeadingListEnd")

    elif kind == "skills":
        out.append("\\resumeItemListStart")
        for item in items:
            label = tex_escape(item.get("label", ""))
            value = tex_inline(item.get("value", ""))
            out.append("\\resumeItem{")
            out.append(f"    \\textbf{{{label}:}} {value}")
            out.append("}")
        out.append("\\resumeItemListEnd")

    elif kind == "list":
        out.append("\\resumeItemListStart")
        for item in items:
            out.append(f"\\resumeItem{{{tex_inline(bullet_text(item))}}}")
        out.append("\\resumeItemListEnd")

    elif kind == "summary":
        paragraph = " ".join(tex_inline(bullet_text(i)) for i in items)
        out.append(f"\\resumeSummary{{{paragraph}}}")

    else:
        raise ProfileError(f"unknown section type {kind!r}")

    return "\n".join(out)



def fill_template(template, values):
    """Substitute {{NAME}} placeholders, leaving LaTeX comment lines alone.

    Templates document their own placeholders in % comments, so substituting
    blindly would corrupt the comment and, worse, silently swallow the real
    placeholder further down the file.
    """
    filled, seen = [], set()
    for line in template.split("\n"):
        if line.lstrip().startswith("%"):
            filled.append(line)
            continue
        for key, value in values.items():
            token = "{{" + key + "}}"
            if token in line:
                seen.add(key)
                line = line.replace(token, value)
        filled.append(line)

    missing = sorted(set(values) - seen)
    if missing:
        raise ProfileError(
            "template is missing placeholder(s): "
            + ", ".join("{{" + m + "}}" for m in missing))
    return "\n".join(filled)


def render_tex(resume, settings, document, variant, template):
    document_id, variant_id = document["id"], variant["id"]
    overrides = variant.get("title_overrides", {}) or {}

    header = render_tex_header(resume.get("basics", {}), document_id, variant_id)

    blocks = []
    for section in resume.get("sections", []):
        if not visible(section, document_id, variant_id):
            continue
        section = dict(section, _title_overrides=overrides)
        block = render_tex_section(section, document_id, variant_id, settings)
        if block:
            blocks.append(block)

    body = "\n\n".join(blocks)
    return fill_template(template, {"HEADER": header, "SECTIONS": body})


# ------------------------------------------------------------ txt rendering

def render_txt(resume, settings, document, variant):
    document_id, variant_id = document["id"], variant["id"]
    overrides = variant.get("title_overrides", {}) or {}
    style = settings.get("dates", {}).get("txt_style", "short_month")
    basics = resume.get("basics", {})

    lines = [basics.get("name", ""), ""]

    contacts = [c for c in basics.get("contact", [])
                if visible(c, document_id, variant_id)]
    rendered = [c["text"] if isinstance(c, dict) else c for c in contacts]
    if rendered:
        lines.append(" • ".join(rendered))

    links = [l for l in basics.get("links", [])
             if visible(l, document_id, variant_id)]
    parts = []
    for link in links:
        label, text = link.get("label"), link.get("text", "")
        parts.append(f"{label}: {text}" if label else text)
    if parts:
        lines.append(" • ".join(parts))

    for section in resume.get("sections", []):
        if not visible(section, document_id, variant_id):
            continue
        items = [i for i in section.get("items", [])
                 if visible(i, document_id, variant_id)]
        if not items:
            continue

        lines += ["", section.get("title", "").upper(), ""]
        kind = section.get("type", "experience")
        precision = section.get("text_date_precision", "month")

        if kind == "experience":
            for index, item in enumerate(items):
                if index:
                    lines.append("")
                title = overrides.get(item.get("id"), item.get("title", ""))
                dates = date_range(item, style, precision, dash=" – ")
                lines.append(f"{title} | {dates}")
                lines.append(f"{item.get('organization', '')} — {item.get('location', '')}")
                lines.append("")
                for bullet in item.get("bullets", []):
                    if visible(bullet, document_id, variant_id):
                        lines.append(f"• {txt_inline(bullet_text(bullet))}")

        elif kind == "education":
            for index, item in enumerate(items):
                if index:
                    lines.append("")
                dates = date_range(item, style, precision, dash=" – ")
                lines.append(item.get("title", ""))
                lines.append(
                    f"{item.get('organization', '')} — {item.get('location', '')} | {dates}")

        elif kind == "skills":
            for item in items:
                lines.append(f"{item.get('label', '')}: {txt_inline(item.get('value', ''))}")

        elif kind == "list":
            for item in items:
                lines.append(f"• {txt_inline(bullet_text(item))}")

        elif kind == "summary":
            lines.append(" ".join(txt_inline(bullet_text(i)) for i in items))

    return "\n".join(lines).rstrip() + "\n"


# ------------------------------------------------------------- validation

REQUIRED_BASICS = ["name"]
SECTION_TYPES = ("summary", "experience", "education", "skills", "list")


def check_profile(profile_dir):
    problems, warnings = [], []
    try:
        resume, settings = load_profile(profile_dir)
    except ProfileError as exc:
        return [str(exc)], []

    basics = resume.get("basics", {})
    for field in REQUIRED_BASICS:
        if not basics.get(field):
            problems.append(f"resume.json: basics.{field} is required")

    if not resume.get("sections"):
        problems.append("resume.json: 'sections' is empty")

    try:
        docs = documents(settings)
    except ProfileError as exc:
        problems.append(str(exc))
        docs = []

    doc_ids = {d.get("id") for d in docs}
    variant_ids = {v.get("id") for v in variants(settings)}
    if len(doc_ids) != len(docs):
        problems.append("settings.json: duplicate document ids")

    item_ids = set()
    for section in resume.get("sections", []):
        kind = section.get("type", "experience")
        if kind not in SECTION_TYPES:
            problems.append(f"resume.json: unknown section type {kind!r}")
        for item in section.get("items", []):
            if item.get("id"):
                item_ids.add(item["id"])
            for node in [item] + list(item.get("bullets", [])):
                if not isinstance(node, dict):
                    continue
                for tag in node.get("include_in", []) or []:
                    if tag not in doc_ids:
                        problems.append(
                            f"resume.json: include_in references unknown document {tag!r}")
                for tag in node.get("variants", []) or []:
                    if tag not in variant_ids:
                        problems.append(
                            f"resume.json: variants references unknown variant {tag!r}")
            for date_field in ("start", "end"):
                if date_field in item:
                    try:
                        parse_date(item[date_field])
                    except ProfileError as exc:
                        problems.append(f"resume.json: {exc}")

    for variant in variants(settings):
        for key in (variant.get("title_overrides") or {}):
            if key not in item_ids:
                warnings.append(
                    f"settings.json: variant {variant.get('id')!r} overrides "
                    f"title for unknown item id {key!r}")

    # Every (document, variant) pair must produce a distinct filename.
    seen = {}
    for document in docs:
        for variant in variants(settings):
            name = output_basename(document, variant)
            key = (variant.get("id"), name)
            if key in seen:
                problems.append(f"output filename collision: {name}")
            seen[key] = True

    return problems, warnings


# ------------------------------------------------------------------ command

def cmd_plan(args):
    _, settings = load_profile(args.profile_dir)
    formats = settings.get("formats", ["pdf", "docx"])
    for document in documents(settings):
        for variant in variants(settings):
            print("\t".join([
                document["id"],
                variant["id"],
                output_basename(document, variant),
                ",".join(formats),
            ]))
    return 0


def cmd_render(args):
    resume, settings = load_profile(args.profile_dir)

    document = next((d for d in documents(settings) if d["id"] == args.document), None)
    if document is None:
        raise ProfileError(f"no document with id {args.document!r}")
    variant = next((v for v in variants(settings) if v["id"] == args.variant), None)
    if variant is None:
        raise ProfileError(f"no variant with id {args.variant!r}")

    if args.out_tex:
        template_name = document.get("template") or settings.get("template", "classic")
        template_path = os.path.join(args.templates_dir, f"{template_name}.tex.tmpl")
        if not os.path.isfile(template_path):
            raise ProfileError(f"missing template: {template_path}")
        with open(template_path, encoding="utf-8") as handle:
            template = handle.read()
        os.makedirs(os.path.dirname(os.path.abspath(args.out_tex)), exist_ok=True)
        with open(args.out_tex, "w", encoding="utf-8") as handle:
            handle.write(render_tex(resume, settings, document, variant, template))

    if args.out_txt:
        os.makedirs(os.path.dirname(os.path.abspath(args.out_txt)), exist_ok=True)
        with open(args.out_txt, "w", encoding="utf-8") as handle:
            handle.write(render_txt(resume, settings, document, variant))

    return 0


def cmd_check(args):
    problems, warnings = check_profile(args.profile_dir)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for problem in problems:
        print(f"error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"{args.profile_dir}: OK")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("plan", "render", "check"):
        child = sub.add_parser(name)
        child.add_argument("--profile-dir", required=True)
        if name == "render":
            child.add_argument("--document", required=True)
            child.add_argument("--variant", required=True)
            child.add_argument("--templates-dir", default="templates")
            child.add_argument("--out-tex")
            child.add_argument("--out-txt")

    args = parser.parse_args(argv)
    handler = {"plan": cmd_plan, "render": cmd_render, "check": cmd_check}[args.command]
    try:
        return handler(args)
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
