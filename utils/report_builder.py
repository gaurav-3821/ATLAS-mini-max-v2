from __future__ import annotations

from io import BytesIO


def build_report_markdown(
    *,
    title: str,
    location_label: str,
    executive_summary: str,
    bullets: list[str],
    source_notes: list[str],
) -> str:
    bullet_block = "\n".join([f"- {item}" for item in bullets])
    source_block = "\n".join([f"- {item}" for item in source_notes])
    return (
        f"# {title}\n\n"
        f"**Location:** {location_label}\n\n"
        f"## Executive Summary\n\n{executive_summary}\n\n"
        f"## Key Findings\n\n{bullet_block}\n\n"
        f"## Source Notes\n\n{source_block}\n"
    )


def build_report_pdf(title: str, markdown_text: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception:
        return markdown_text.encode("utf-8")

    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, title=title)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    for block in markdown_text.split("\n\n"):
        text = block.replace("\n", "<br/>")
        story.append(Paragraph(text, styles["BodyText"]))
        story.append(Spacer(1, 10))
    document.build(story)
    return buffer.getvalue()
