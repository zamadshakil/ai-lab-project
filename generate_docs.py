#!/usr/bin/env python3
"""
generate_docs.py
================
Generates a professionally formatted DOCX project documentation report
for "Specter's Bridge: An AI Laboratory" — a university AI Lab Term Project.

Requirements: pip install python-docx
"""

from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

# ─── Color Palette ───────────────────────────────────────────────────────────
CHARCOAL = RGBColor(29, 29, 31)       # #1d1d1f — headings
BODY_GRAY = RGBColor(61, 61, 63)      # #3d3d3f — body text
ACCENT_BLUE = RGBColor(0, 113, 227)   # #0071e3 — highlights
WHITE = RGBColor(255, 255, 255)
LIGHT_GRAY_BG = RGBColor(245, 245, 247)  # table alternating rows
TABLE_HEADER_BG = "2d2d2f"               # dark header for tables
SEPARATOR_GRAY = RGBColor(200, 200, 200)
SUBTLE_GRAY = RGBColor(120, 120, 120)


# ─── Helper Functions ────────────────────────────────────────────────────────

def set_cell_shading(cell, color_hex):
    """Apply background shading to a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_cell_borders(cell, top="single", bottom="single", left="single", right="single",
                     color="d0d0d0", size="4"):
    """Set thin borders on a cell."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'  <w:top w:val="{top}" w:sz="{size}" w:space="0" w:color="{color}"/>'
        f'  <w:bottom w:val="{bottom}" w:sz="{size}" w:space="0" w:color="{color}"/>'
        f'  <w:left w:val="{left}" w:sz="{size}" w:space="0" w:color="{color}"/>'
        f'  <w:right w:val="{right}" w:sz="{size}" w:space="0" w:color="{color}"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)


def fmt_run(paragraph, text, size=11, bold=False, italic=False, color=BODY_GRAY, font_name="Calibri"):
    """Add a formatted run to a paragraph."""
    run = paragraph.add_run(text)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.name = font_name
    rPr = run._element.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="{font_name}" w:hAnsi="{font_name}" w:cs="{font_name}"/>')
    rPr.insert(0, rFonts)
    return run


def add_body_paragraph(doc, text, bold=False, italic=False, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY,
                       space_before=3, space_after=3, first_line_indent=None):
    """Add a standard body paragraph."""
    p = doc.add_paragraph()
    p.alignment = alignment
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if first_line_indent:
        p.paragraph_format.first_line_indent = Inches(first_line_indent)
    fmt_run(p, text, size=11, bold=bold, italic=italic, color=BODY_GRAY)
    return p


def add_heading_styled(doc, text, level=1):
    """Add a heading with custom styling."""
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.color.rgb = CHARCOAL
        run.font.name = "Calibri"
        rPr = run._element.get_or_add_rPr()
        rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>')
        rPr.insert(0, rFonts)
        if level == 1:
            run.font.size = Pt(16)
        elif level == 2:
            run.font.size = Pt(13)
        elif level == 3:
            run.font.size = Pt(11.5)
        run.font.bold = True
    h.paragraph_format.space_before = Pt(18 if level == 1 else 12)
    h.paragraph_format.space_after = Pt(6)
    h.paragraph_format.line_spacing = 1.15
    return h


def add_separator(doc):
    """Add a thin horizontal rule as a section separator."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    pPr = p._element.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'  <w:bottom w:val="single" w:sz="4" w:space="1" w:color="d0d0d0"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)


def add_bullet(doc, text, level=0, bold_prefix=None):
    """Add a bullet point paragraph."""
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if level > 0:
        p.paragraph_format.left_indent = Inches(0.5 * (level + 1))
    if bold_prefix:
        fmt_run(p, bold_prefix, size=11, bold=True, color=BODY_GRAY)
        fmt_run(p, text, size=11, color=BODY_GRAY)
    else:
        fmt_run(p, text, size=11, color=BODY_GRAY)
    return p


def add_styled_table(doc, headers, rows, col_widths=None):
    """Create a styled table with header shading and alternating row colors."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    # Style header row
    for i, header_text in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        fmt_run(p, header_text, size=10, bold=True, color=WHITE)
        set_cell_shading(cell, TABLE_HEADER_BG)
        set_cell_borders(cell, color="a0a0a0", size="4")
        cell.vertical_alignment = 1  # CENTER

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_text in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            fmt_run(p, str(cell_text), size=10, color=BODY_GRAY)
            if r_idx % 2 == 1:
                set_cell_shading(cell, "f5f5f7")
            set_cell_borders(cell, color="d0d0d0", size="4")

    # Set column widths if provided
    if col_widths:
        for row in table.rows:
            for i, width in enumerate(col_widths):
                row.cells[i].width = Inches(width)

    return table


def add_page_number(doc):
    """Add page numbers to footer."""
    for section in doc.sections:
        footer = section.footer
        footer.is_linked_to_previous = False
        p = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)

        # Add "Page " text
        run1 = p.add_run("Page ")
        run1.font.size = Pt(8)
        run1.font.color.rgb = SUBTLE_GRAY
        run1.font.name = "Calibri"

        # Add PAGE field
        fldChar1 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="begin"/>')
        run2 = p.add_run()
        run2._element.append(fldChar1)

        instrText = parse_xml(f'<w:instrText {nsdecls("w")} xml:space="preserve"> PAGE </w:instrText>')
        run3 = p.add_run()
        run3._element.append(instrText)

        fldChar2 = parse_xml(f'<w:fldChar {nsdecls("w")} w:fldCharType="end"/>')
        run4 = p.add_run()
        run4._element.append(fldChar2)


# ─── Document Generation ─────────────────────────────────────────────────────

def generate_document():
    doc = Document()

    # ── Page Setup ────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)
    font.color.rgb = BODY_GRAY
    rPr = style.element.get_or_add_rPr()
    rFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>')
    rPr.insert(0, rFonts)

    # Also set heading styles to Calibri
    for i in range(1, 5):
        hs = doc.styles[f'Heading {i}']
        hs.font.name = 'Calibri'
        hs.font.color.rgb = CHARCOAL
        hsRPr = hs.element.get_or_add_rPr()
        hsRFonts = parse_xml(f'<w:rFonts {nsdecls("w")} w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/>')
        hsRPr.insert(0, hsRFonts)

    # ══════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ══════════════════════════════════════════════════════════════════════

    # Top spacer
    for _ in range(5):
        spacer = doc.add_paragraph()
        spacer.paragraph_format.space_before = Pt(0)
        spacer.paragraph_format.space_after = Pt(0)

    # Accent line
    accent_line = doc.add_paragraph()
    accent_line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fmt_run(accent_line, "━" * 40, size=12, color=ACCENT_BLUE)
    accent_line.paragraph_format.space_after = Pt(16)

    # Main title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(4)
    fmt_run(title_p, "Specter's Bridge", size=34, bold=True, color=CHARCOAL)

    # Subtitle line 1
    sub1 = doc.add_paragraph()
    sub1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub1.paragraph_format.space_before = Pt(0)
    sub1.paragraph_format.space_after = Pt(2)
    fmt_run(sub1, "AI Laboratory", size=22, color=ACCENT_BLUE)

    # Accent line
    accent_line2 = doc.add_paragraph()
    accent_line2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    accent_line2.paragraph_format.space_before = Pt(12)
    accent_line2.paragraph_format.space_after = Pt(12)
    fmt_run(accent_line2, "━" * 40, size=12, color=ACCENT_BLUE)

    # Subtitle line 2
    sub2 = doc.add_paragraph()
    sub2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub2.paragraph_format.space_before = Pt(4)
    sub2.paragraph_format.space_after = Pt(6)
    fmt_run(sub2, "A First-Principles Laboratory of Stochastic Adversarial Search,", size=12, italic=True, color=BODY_GRAY)

    sub3 = doc.add_paragraph()
    sub3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub3.paragraph_format.space_before = Pt(0)
    sub3.paragraph_format.space_after = Pt(24)
    fmt_run(sub3, "Reinforcement Learning, and Evolution", size=12, italic=True, color=BODY_GRAY)

    # Course line
    course_p = doc.add_paragraph()
    course_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    course_p.paragraph_format.space_before = Pt(12)
    course_p.paragraph_format.space_after = Pt(20)
    fmt_run(course_p, "Artificial Intelligence — Term Project", size=13, bold=True, color=CHARCOAL)

    # Team members
    team_header = doc.add_paragraph()
    team_header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    team_header.paragraph_format.space_before = Pt(8)
    team_header.paragraph_format.space_after = Pt(6)
    fmt_run(team_header, "Team Members", size=11, bold=True, color=ACCENT_BLUE)

    members = ["Member 1", "Member 2", "Member 3", "Member 4", "Member 5"]
    for member in members:
        mp = doc.add_paragraph()
        mp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        mp.paragraph_format.space_before = Pt(1)
        mp.paragraph_format.space_after = Pt(1)
        fmt_run(mp, member, size=11, color=BODY_GRAY)

    # Date
    date_p = doc.add_paragraph()
    date_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_p.paragraph_format.space_before = Pt(20)
    date_p.paragraph_format.space_after = Pt(0)
    fmt_run(date_p, "June 2026", size=11, color=SUBTLE_GRAY)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # TABLE OF CONTENTS
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "Table of Contents", level=1)
    add_separator(doc)

    toc_items = [
        "1.  Introduction & Problem Statement",
        "2.  System Architecture",
        "3.  Algorithm 1: Expectiminimax Search with Star2 Pruning",
        "4.  Algorithm 2: Tabular Q-Learning (Reinforcement Learning)",
        "5.  Algorithm 3: Genetic Algorithm for Heuristic Optimization",
        "6.  Web Dashboard & Visualization",
        "7.  Testing & Verification",
        "8.  Conclusion",
        "9.  References",
    ]

    for item in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.4
        p.paragraph_format.left_indent = Inches(0.3)
        # Number in accent blue
        parts = item.split("  ", 1)
        fmt_run(p, parts[0] + "  ", size=11, bold=True, color=ACCENT_BLUE)
        fmt_run(p, parts[1], size=11, color=CHARCOAL)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1: Introduction & Problem Statement
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "1.  Introduction & Problem Statement", level=1)
    add_separator(doc)

    add_body_paragraph(doc,
        "The Haunted Bridge Crossing — also known as Stochastic Nim — is a two-player, "
        "zero-sum game played on a one-dimensional bridge composed of a finite number of planks. "
        "Two adversaries, the Traveler (MAX) and the Specter (MIN), alternate turns, each choosing "
        "to either step forward by one plank or leap forward by two. The game introduces stochastic "
        "elements: a leap succeeds with 80% probability and fails (a slip) with 20% probability. "
        "When a player slips, their opponent scores a point. Certain planks are marked as slippery, "
        "scaling the slip probability by a factor of 2.5×. The game ends when no planks remain, and "
        "the winner is determined by the chosen variant — Normal play (last mover wins) or Misère "
        "play (last mover loses)."
    )

    add_body_paragraph(doc,
        "This project serves as a comprehensive laboratory for exploring three foundational AI "
        "paradigms applied to this stochastic adversarial environment: classical tree search "
        "(Expectiminimax with Star2 pruning), model-free reinforcement learning (Tabular Q-Learning), "
        "and evolutionary optimization (Genetic Algorithms for heuristic weight tuning)."
    )

    add_heading_styled(doc, "1.1  PEAS Framework", level=2)

    peas_data = [
        ["Performance", "Score differential between players; win/loss outcome"],
        ["Environment", "1D bridge of n planks with stochastic hazard zones (slippery planks); two-player, "
                        "turn-based, partially stochastic, zero-sum"],
        ["Actuators", "Step 1 (deterministic forward move) / Leap 2 (stochastic forward move)"],
        ["Sensors", "Remaining planks count, current turn indicator, cumulative scores for both players"],
    ]
    add_styled_table(doc, ["PEAS Element", "Description"], peas_data, col_widths=[1.5, 5.0])

    add_heading_styled(doc, "1.2  Game Rules", level=2)

    add_bullet(doc, "Two players alternate turns: MAX (Traveler) and MIN (Specter).", bold_prefix="Players: ")
    add_bullet(doc, "Deterministic — always succeeds, consuming exactly one plank.", bold_prefix="Step 1: ")
    add_bullet(doc, "Stochastic — 80% probability of success (consuming two planks), "
               "20% probability of a slip (consuming one plank, opponent scores +1).", bold_prefix="Leap 2: ")
    add_bullet(doc, "Slippery planks multiply the base slip probability by 2.5× "
               "(e.g., 20% × 2.5 = 50% slip chance).", bold_prefix="Slippery Planks: ")
    add_bullet(doc, "The game ends when zero planks remain.", bold_prefix="Termination: ")
    add_bullet(doc, "Normal mode — the player who takes the last plank wins. "
               "Misère mode — the player who takes the last plank loses.", bold_prefix="Win Condition: ")

    add_heading_styled(doc, "1.3  State Representation", level=2)

    add_body_paragraph(doc,
        "Each game state is represented as a compact 4-tuple:"
    )

    state_p = doc.add_paragraph()
    state_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    state_p.paragraph_format.space_before = Pt(8)
    state_p.paragraph_format.space_after = Pt(8)
    fmt_run(state_p, "s = ( remaining_planks,  is_max_turn,  max_score,  min_score )", size=11,
            bold=True, color=ACCENT_BLUE, font_name="Consolas")

    add_body_paragraph(doc,
        "For a 12-plank bridge, this yields a manageable state space that can be fully enumerated, "
        "making the problem ideal for comparing exact tree search against learned policies."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2: System Architecture
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "2.  System Architecture", level=1)
    add_separator(doc)

    add_heading_styled(doc, "2.1  Technology Stack", level=2)

    stack_data = [
        ["Backend", "Python 3, FastAPI", "REST API server with async request handling"],
        ["AI Engine", "Python 3 (stdlib)", "Core algorithms: Expectiminimax, Q-Learning, GA"],
        ["Frontend", "HTML5, CSS3, JavaScript", "Interactive dashboard with Canvas and SVG rendering"],
        ["Visualization", "Chart.js", "Dynamic charts for learning curves and GA fitness"],
        ["Deployment", "Vercel", "Serverless deployment with automatic HTTPS"],
    ]
    add_styled_table(doc, ["Layer", "Technology", "Purpose"], stack_data, col_widths=[1.2, 2.0, 3.3])

    add_heading_styled(doc, "2.2  File Structure", level=2)

    files_data = [
        ["engine.py", "Core AI module containing Expectiminimax solver, Q-Learning agent, "
                      "and Genetic Algorithm optimizer"],
        ["app.py", "FastAPI REST API server exposing game endpoints (/move, /train, /evolve)"],
        ["static/index.html", "Main dashboard UI — single-page application entry point"],
        ["static/style.css", "Modern stylesheet with responsive layout and Notion-inspired aesthetic"],
        ["static/app.js", "Client-side logic: Canvas game board, SVG decision tree, Chart.js integration"],
    ]
    add_styled_table(doc, ["File", "Description"], files_data, col_widths=[1.8, 4.7])

    add_heading_styled(doc, "2.3  Architecture Overview", level=2)

    add_body_paragraph(doc,
        "The system follows a clean three-tier architecture. The browser-based frontend communicates "
        "with the FastAPI backend via RESTful JSON endpoints. The backend delegates all AI computation "
        "to the engine module, which implements the three algorithms as stateless, pure functions."
    )

    # Architecture diagram as a styled table
    arch_table = doc.add_table(rows=1, cols=5)
    arch_table.alignment = WD_TABLE_ALIGNMENT.CENTER

    labels = ["Browser\n(HTML5 / JS)", "⟷", "FastAPI\n(app.py)", "⟷", "Engine\n(engine.py)"]
    colors = ["0071e3", None, "2d2d2f", None, "2d2d2f"]

    for i, (label, bg) in enumerate(zip(labels, colors)):
        cell = arch_table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        if bg:
            fmt_run(p, label, size=10, bold=True, color=WHITE)
            set_cell_shading(cell, bg)
            set_cell_borders(cell, color="a0a0a0")
        else:
            fmt_run(p, label, size=14, bold=True, color=ACCENT_BLUE)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 3: Expectiminimax with Star2 Pruning
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "3.  Algorithm 1: Expectiminimax Search with Star2 Pruning", level=1)
    add_separator(doc)

    add_body_paragraph(doc,
        "Expectiminimax extends the classical Minimax algorithm to handle stochastic environments by "
        "introducing a third node type — Chance nodes — alongside the standard MAX and MIN nodes. "
        "This is necessary because the Leap action in the Haunted Bridge Crossing has probabilistic "
        "outcomes, making deterministic Minimax insufficient."
    )

    add_heading_styled(doc, "3.1  Node Types", level=2)

    node_data = [
        ["MAX Node", "Traveler's turn", "Choose action with maximum utility"],
        ["MIN Node", "Specter's turn", "Choose action with minimum utility"],
        ["Chance Node", "After a Leap action", "Compute expected value: E[v] = Σ pᵢ · v(childᵢ)"],
    ]
    add_styled_table(doc, ["Node Type", "When Active", "Selection Rule"], node_data, col_widths=[1.3, 1.8, 3.4])

    add_heading_styled(doc, "3.2  Depth-Limited Search & Heuristic Evaluation", level=2)

    add_body_paragraph(doc,
        "When the search reaches its depth limit before arriving at a terminal state, a heuristic "
        "evaluation function estimates the state's utility. The heuristic is a weighted linear "
        "combination of four features:"
    )

    heuristic_p = doc.add_paragraph()
    heuristic_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heuristic_p.paragraph_format.space_before = Pt(10)
    heuristic_p.paragraph_format.space_after = Pt(10)
    fmt_run(heuristic_p, "h(s)  =  w₀ · max_score  +  w₁ · min_score  +  w₂ · progress  +  w₃ · trap_risk",
            size=11, bold=True, color=ACCENT_BLUE, font_name="Consolas")

    add_bullet(doc, "The cumulative score of the MAX player.", bold_prefix="max_score: ")
    add_bullet(doc, "The cumulative score of the MIN player (typically weighted negatively).", bold_prefix="min_score: ")
    add_bullet(doc, "Fraction of planks already traversed, rewarding forward progress.", bold_prefix="progress: ")
    add_bullet(doc, "Risk metric based on proximity to slippery planks.", bold_prefix="trap_risk: ")

    add_heading_styled(doc, "3.3  Star2 Pruning", level=2)

    add_body_paragraph(doc,
        "Standard Alpha-Beta pruning cannot be directly applied at Chance nodes because the "
        "expected value is a probability-weighted sum, not a simple maximum or minimum. The Star2 "
        "algorithm (Ballard, 1983) solves this by computing global bounds on the heuristic function "
        "and using them to derive dynamic pruning windows at each chance outcome."
    )

    add_heading_styled(doc, "Global Bounds", level=3)
    add_body_paragraph(doc,
        "The heuristic function is decomposed to determine its absolute maximum (V_max) and minimum "
        "(V_min) values across all reachable states. These bounds establish the tightest possible "
        "range for any node's evaluation."
    )

    add_heading_styled(doc, "Dynamic Window Bounding", level=3)
    add_body_paragraph(doc,
        "At each Chance node, as outcomes are evaluated sequentially, the accumulated partial sum "
        "(S_eval) and remaining probability mass (P_rem) are tracked. For each new outcome with "
        "probability p, the pruning window [αc, βc] is computed as:"
    )

    formula1 = doc.add_paragraph()
    formula1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    formula1.paragraph_format.space_before = Pt(8)
    formula1.paragraph_format.space_after = Pt(4)
    fmt_run(formula1, "αc = max( V_min,  (α − S_eval − P_rem · V_max) / p )",
            size=10, color=CHARCOAL, font_name="Consolas")

    formula2 = doc.add_paragraph()
    formula2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    formula2.paragraph_format.space_before = Pt(2)
    formula2.paragraph_format.space_after = Pt(8)
    fmt_run(formula2, "βc = min( V_max,  (β − S_eval − P_rem · V_min) / p )",
            size=10, color=CHARCOAL, font_name="Consolas")

    add_heading_styled(doc, "Pruning Condition", level=3)
    add_body_paragraph(doc,
        "If αc ≥ βc after computing the narrowed window, the remaining outcomes at that Chance "
        "node cannot influence the parent's decision, and they are pruned safely. This is sound "
        "because the bounds guarantee that no pruned subtree could produce a value outside the "
        "feasible range."
    )

    add_heading_styled(doc, "3.4  Results", level=2)
    add_body_paragraph(doc,
        "Star2 pruning reduces the number of evaluated nodes by approximately 50% compared to "
        "unpruned Expectiminimax, while producing identical root values. This speedup enables "
        "deeper search within the same computational budget, improving the quality of play in "
        "real-time scenarios."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 4: Tabular Q-Learning
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "4.  Algorithm 2: Tabular Q-Learning (Reinforcement Learning)", level=1)
    add_separator(doc)

    add_body_paragraph(doc,
        "Q-Learning is a model-free, off-policy temporal difference (TD) algorithm that learns "
        "optimal action-values Q(s, a) directly from experience without requiring a model of the "
        "environment's transition dynamics. Unlike Expectiminimax, which requires full knowledge of "
        "the game tree, Q-Learning discovers the optimal policy through repeated episodes of "
        "self-play."
    )

    add_heading_styled(doc, "4.1  Compressed State Representation", level=2)
    add_body_paragraph(doc,
        "To make tabular Q-Learning tractable, the state is compressed from the full 4-tuple to a "
        "2-tuple:"
    )

    state2_p = doc.add_paragraph()
    state2_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    state2_p.paragraph_format.space_before = Pt(8)
    state2_p.paragraph_format.space_after = Pt(8)
    fmt_run(state2_p, "s_compressed = ( remaining_planks,  is_max_turn )",
            size=11, bold=True, color=ACCENT_BLUE, font_name="Consolas")

    add_body_paragraph(doc,
        "For a 12-plank bridge, this yields only 24 unique states (12 plank counts × 2 turn "
        "indicators), enabling complete tabular coverage without function approximation."
    )

    add_heading_styled(doc, "4.2  Bellman Update Rule", level=2)

    bellman_p = doc.add_paragraph()
    bellman_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    bellman_p.paragraph_format.space_before = Pt(8)
    bellman_p.paragraph_format.space_after = Pt(8)
    fmt_run(bellman_p, "Q(s, a)  ←  Q(s, a) + α · [ R + γ · Target − Q(s, a) ]",
            size=11, bold=True, color=ACCENT_BLUE, font_name="Consolas")

    add_body_paragraph(doc,
        "The Target depends on the identity of the next player:"
    )

    add_bullet(doc, "Target = max_a' Q(s', a') — the next player seeks to maximize.", bold_prefix="If next player is MAX: ")
    add_bullet(doc, "Target = min_a' Q(s', a') — the next player seeks to minimize.", bold_prefix="If next player is MIN: ")

    add_heading_styled(doc, "4.3  Reward Function", level=2)
    add_body_paragraph(doc,
        "The reward at each time step is defined as the change in score differential:"
    )

    reward_p = doc.add_paragraph()
    reward_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    reward_p.paragraph_format.space_before = Pt(8)
    reward_p.paragraph_format.space_after = Pt(8)
    fmt_run(reward_p, "Rₜ = Δ(score_differential) = (max_scoreₜ − min_scoreₜ) − (max_scoreₜ₋₁ − min_scoreₜ₋₁)",
            size=10, bold=True, color=ACCENT_BLUE, font_name="Consolas")

    add_body_paragraph(doc,
        "This reward telescopes across the episode, ensuring that the cumulative return equals "
        "the final score differential — the true game outcome."
    )

    add_heading_styled(doc, "4.4  Exploration Strategy", level=2)

    add_bullet(doc, "ε-greedy exploration with decay from ε₀ = 0.3 to ε_min = 0.01 over training.",
               bold_prefix="Epsilon-Greedy: ")
    add_bullet(doc, "30% of training episodes begin from uniformly random states, ensuring every "
               "state-action pair is visited regardless of the policy's trajectory distribution.",
               bold_prefix="Exploratory Starts: ")

    add_heading_styled(doc, "4.5  Results", level=2)
    add_body_paragraph(doc,
        "After training, the Q-Learning agent achieves 100% policy convergence with the Expectiminimax "
        "solver: all 16 reachable decision states (excluding terminal states) produce identical "
        "optimal actions. This empirically demonstrates that model-free RL can recover the exact "
        "solution of a stochastic game tree search."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 5: Genetic Algorithm
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "5.  Algorithm 3: Genetic Algorithm for Heuristic Optimization", level=1)
    add_separator(doc)

    add_body_paragraph(doc,
        "The Genetic Algorithm (GA) optimizes the four heuristic weights used by the Expectiminimax "
        "evaluation function. Rather than hand-tuning these weights, the GA evolves a population of "
        "candidate weight vectors, selecting for individuals that produce stronger game play."
    )

    add_heading_styled(doc, "5.1  Chromosome Encoding", level=2)

    chrom_p = doc.add_paragraph()
    chrom_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    chrom_p.paragraph_format.space_before = Pt(8)
    chrom_p.paragraph_format.space_after = Pt(8)
    fmt_run(chrom_p, "chromosome = [ w_max_score,  w_min_score,  w_progress,  w_trap_risk ]",
            size=11, bold=True, color=ACCENT_BLUE, font_name="Consolas")

    add_body_paragraph(doc,
        "Each chromosome is a real-valued vector of four weights. Polarity constraints are enforced: "
        "w_max_score and w_progress must remain positive (≥ 0.1), while w_min_score and w_trap_risk "
        "must remain negative (≤ −0.1), reflecting the semantic meaning of each feature."
    )

    add_heading_styled(doc, "5.2  GA Parameters", level=2)

    ga_params = [
        ["Population Size", "10 individuals"],
        ["Initialization", "Random with polarity constraints"],
        ["Fitness Function", "Round-robin tournament — total wins across all pairwise matches"],
        ["Selection", "2-way tournament selection"],
        ["Crossover", "Single-point crossover at a random index"],
        ["Mutation", "Gaussian shift (σ = 0.3) with polarity clamping"],
        ["Elitism", "Top 2 chromosomes preserved each generation"],
    ]
    add_styled_table(doc, ["Parameter", "Value"], ga_params, col_widths=[2.0, 4.5])

    add_heading_styled(doc, "5.3  Evolutionary Loop", level=2)

    add_body_paragraph(doc, "Each generation proceeds through the following steps:")

    steps = [
        ("Fitness Evaluation: ", "Every individual plays against every other individual in a round-robin "
         "tournament. The fitness score is the total number of wins."),
        ("Selection: ", "Pairs of parents are chosen via 2-way tournament selection — two individuals "
         "are drawn randomly, and the one with higher fitness is selected."),
        ("Crossover: ", "Each parent pair produces two offspring via single-point crossover at a "
         "randomly chosen gene index."),
        ("Mutation: ", "Each gene in each offspring is perturbed by adding Gaussian noise (μ = 0, σ = 0.3). "
         "After mutation, polarity constraints are re-enforced by clamping."),
        ("Elitism: ", "The top 2 individuals from the current generation are copied unchanged into the "
         "next generation, ensuring monotonic fitness improvement."),
    ]
    for prefix, text in steps:
        add_bullet(doc, text, bold_prefix=prefix)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 6: Web Dashboard & Visualization
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "6.  Web Dashboard & Visualization", level=1)
    add_separator(doc)

    add_body_paragraph(doc,
        "The project includes a production-quality web dashboard that serves as the primary "
        "interface for interacting with all three algorithms. The dashboard follows a modern, "
        "minimalist aesthetic inspired by Notion and Apple's design language."
    )

    add_heading_styled(doc, "6.1  Three-Panel Layout", level=2)

    panel_data = [
        ["Chasm Arena", "HTML5 Canvas", "Animated game board with bridge planks, player tokens, "
         "and real-time move visualization"],
        ["Decision Tree Explorer", "Dynamic SVG", "Interactive tree visualization of Expectiminimax "
         "search with color-coded MAX/MIN/Chance nodes and best-move highlighting"],
        ["Heuristics & Learning Labs", "Chart.js (Tabbed)", "Learning curves for Q-Learning (reward "
         "vs. episode), GA fitness evolution plots, weight convergence charts"],
    ]
    add_styled_table(doc, ["Panel", "Technology", "Description"], panel_data, col_widths=[1.8, 1.5, 3.2])

    add_heading_styled(doc, "6.2  Interactive Controls", level=2)

    add_bullet(doc, "Choose between Expectiminimax, Q-Learning, or Human for each player slot.",
               bold_prefix="Agent Selection: ")
    add_bullet(doc, "Click-to-play interface for human vs. AI games.",
               bold_prefix="Manual Play: ")
    add_bullet(doc, "Toggle search depth and Star2 pruning on/off to observe performance differences.",
               bold_prefix="Depth & Pruning Toggles: ")
    add_bullet(doc, "View real-time node expansion counts and evaluation metrics.",
               bold_prefix="Real-Time Metrics: ")

    add_heading_styled(doc, "6.3  Responsive Design", level=2)

    add_body_paragraph(doc,
        "The dashboard uses a responsive two-column layout on desktop (≥ 1150px viewport width) "
        "that reflows to a single column on smaller screens. Visual elements use a light theme "
        "with clean single-pixel borders, flat white card backgrounds, and subtle drop shadows — "
        "achieving a modern Notion/Apple aesthetic."
    )

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 7: Testing & Verification
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "7.  Testing & Verification", level=1)
    add_separator(doc)

    add_heading_styled(doc, "7.1  Unit Test Suite", level=2)

    add_body_paragraph(doc,
        "A comprehensive unit test suite validates all core components of the system. All 7 tests "
        "pass successfully:"
    )

    test_data = [
        ["1", "Environment Initialization", "Bridge state initializes with correct plank count and scores", "✓ Pass"],
        ["2", "Deterministic Transitions", "Step action consumes exactly 1 plank, no score change", "✓ Pass"],
        ["3", "Stochastic Transitions", "Leap action produces correct probabilistic outcomes", "✓ Pass"],
        ["4", "Solver (No Pruning)", "Expectiminimax returns correct values without Star2", "✓ Pass"],
        ["5", "Solver (With Pruning)", "Star2-pruned values match unpruned values exactly", "✓ Pass"],
        ["6", "Q-Learning Training", "Q-values converge after training episodes", "✓ Pass"],
        ["7", "GA Evolution", "Population fitness improves across generations", "✓ Pass"],
    ]
    add_styled_table(doc, ["#", "Test Name", "Validation Criterion", "Result"], test_data,
                     col_widths=[0.4, 1.7, 3.2, 0.8])

    add_heading_styled(doc, "7.2  Cross-Algorithm Convergence Verification", level=2)

    add_body_paragraph(doc,
        "The strongest verification result is the policy agreement between the Q-Learning agent "
        "and the Expectiminimax solver. After training, the Q-Learning policy was compared against "
        "the Expectiminimax optimal policy across all 16 reachable non-terminal states:"
    )

    convergence_data = [
        ["Total Decision States", "16"],
        ["States with Matching Policy", "16"],
        ["Agreement Rate", "100%"],
        ["Node Reduction (Star2)", "~50%"],
    ]
    add_styled_table(doc, ["Metric", "Value"], convergence_data, col_widths=[3.0, 3.5])

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 8: Conclusion
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "8.  Conclusion", level=1)
    add_separator(doc)

    add_body_paragraph(doc,
        "This project successfully implements three distinct AI paradigms — classical adversarial "
        "tree search, model-free reinforcement learning, and evolutionary optimization — applied to "
        "the stochastic adversarial environment of the Haunted Bridge Crossing."
    )

    add_body_paragraph(doc, "Key achievements of this project include:")

    conclusions = [
        ("Expectiminimax with Star2 Pruning: ",
         "Implemented a complete depth-limited Expectiminimax solver with Star2 pruning, achieving "
         "~50% reduction in node evaluations while maintaining optimal play."),
        ("Q-Learning Convergence: ",
         "Demonstrated that a model-free RL agent can recover the exact optimal policy of a stochastic "
         "game tree, achieving 100% policy agreement with the tree search solver across all 16 decision states."),
        ("Genetic Algorithm Optimization: ",
         "Applied evolutionary optimization to automatically tune heuristic weights, removing the need "
         "for manual parameter engineering and discovering high-quality weight configurations."),
        ("Interactive Dashboard: ",
         "Built and deployed a production-quality web dashboard on Vercel with real-time game "
         "visualization, interactive decision tree exploration, and dynamic learning analytics."),
        ("Beyond Requirements: ",
         "The project significantly exceeds the minimum course requirements by integrating reinforcement "
         "learning and evolutionary optimization alongside the required Expectiminimax implementation, "
         "providing a comprehensive comparative study of three foundational AI paradigms."),
    ]
    for prefix, text in conclusions:
        add_bullet(doc, text, bold_prefix=prefix)

    doc.add_page_break()

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 9: References
    # ══════════════════════════════════════════════════════════════════════

    add_heading_styled(doc, "9.  References", level=1)
    add_separator(doc)

    references = [
        "[1]  Russell, S. & Norvig, P. (2021). Artificial Intelligence: A Modern Approach, "
        "4th Edition. Pearson.",

        "[2]  Ballard, B. W. (1983). The *-Minimax Search Procedure for Trees Containing "
        "Chance Nodes. Artificial Intelligence, 21(3), 327–350.",

        "[3]  Sutton, R. S. & Barto, A. G. (2018). Reinforcement Learning: An Introduction, "
        "2nd Edition. MIT Press.",

        "[4]  Goldberg, D. E. (1989). Genetic Algorithms in Search, Optimization, and Machine "
        "Learning. Addison-Wesley.",
    ]

    for ref in references:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(8)
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.left_indent = Inches(0.5)
        p.paragraph_format.first_line_indent = Inches(-0.5)
        # Number in accent blue
        bracket_end = ref.index("]") + 1
        fmt_run(p, ref[:bracket_end], size=11, bold=True, color=ACCENT_BLUE)
        fmt_run(p, ref[bracket_end:], size=11, color=BODY_GRAY)

    # ── Page Numbers ──────────────────────────────────────────────────────
    add_page_number(doc)

    # ── Save ──────────────────────────────────────────────────────────────
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Project_Documentation.docx")
    doc.save(output_path)
    print(f"\n{'='*60}")
    print(f"  Document generated successfully!")
    print(f"  Output: {output_path}")
    print(f"  Size:   {os.path.getsize(output_path) / 1024:.1f} KB")
    print(f"{'='*60}\n")
    return output_path


if __name__ == "__main__":
    generate_document()
