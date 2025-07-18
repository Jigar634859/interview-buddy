import pandas as pd
import json
import re
from io import BytesIO
from collections import Counter
from datetime import datetime

from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, ListFlowable, ListItem,
                                KeepTogether, HRFlowable)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch

from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie

# --- Constants & Prompts (Unchanged) ---
CODING_TOPICS = [
    "Array", "String", "Tree", "Graph", "DP", "Recursion", "Greedy", "Hashmap",
    "Stack", "Queue", "Linked List", "Heap", "Binary Search", "Matrix"
]
JOURNEY_PROMPT_TEMPLATE = """
You are an expert interview coach. Analyze the provided candidate journeys.
Return a single JSON object with keys: "summary_paragraph", "mistakes_to_avoid", and "key_tips".
- "summary_paragraph": A concise paragraph covering preparation timeframes and strategies.
- "mistakes_to_avoid": A list of key mistakes candidates should avoid.
- "key_tips": A list of actionable tips for success.

Journeys data:
{sample_data}
"""
ROUND_PROMPT_TEMPLATE = """
You are a senior technical interviewer. Summarize the interview experiences for Round {round_index}.
Return a single JSON object with keys: "overview", "coding_questions", and "problem_links".
- "overview": A paragraph on the round's format, duration, and difficulty.
- "coding_questions": A list of strings, each describing a question and its topic.
- "problem_links": A list of all unique problem URLs mentioned.

Round {round_index} data:
{sample_data}
"""

class PDFReportBuilder:
    """
    Builds a professional, multi-page PDF report with a cover page,
    headers, footers, and corrected styling.
    """
    def __init__(self, df: pd.DataFrame, llm, company_name: str, role_name: str):
        self.df = df
        self.llm = llm
        self.company_name = company_name
        self.role_name = role_name
        self.elements = []
        self._init_styles()

    def _init_styles(self):
        """Initializes and configures all necessary paragraph and table styles."""
        styles = getSampleStyleSheet()
        self.styles = {
            'CoverTitle': ParagraphStyle(name='CoverTitle', fontSize=28, alignment=TA_CENTER, spaceAfter=24, textColor=colors.HexColor('#004085')),
            'CoverSubTitle': ParagraphStyle(name='CoverSubTitle', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER, spaceAfter=12),
            'CoverDate': ParagraphStyle(name='CoverDate', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=colors.grey),
            'Title': ParagraphStyle(name='Title', parent=styles['h1'], fontSize=20, alignment=TA_CENTER, spaceAfter=12),
            'Section': ParagraphStyle(name='Section', parent=styles['h2'], fontSize=16, leading=20, spaceAfter=12, textColor=colors.HexColor('#004085')),
            'SubSection': ParagraphStyle(name='SubSection', parent=styles['h3'], fontSize=12, leading=16, spaceAfter=8, textColor=colors.black, fontName='Helvetica-Bold'),
            'Body': ParagraphStyle(name='Body', parent=styles['Normal'], fontSize=11, leading=15, spaceAfter=12),
            'Bullet': ParagraphStyle(name='Bullet', parent=styles['Normal'], fontSize=10, leading=14, leftIndent=18, spaceBefore=4),
            'Link': ParagraphStyle(name='Link', fontSize=9, textColor=colors.blue, wordWrap='break-word'),
        }
        self.hr_line = HRFlowable(width="100%", thickness=1, color=colors.lightgrey, spaceBefore=10, spaceAfter=10)

    def _header_footer(self, canvas, doc):
        """Adds a footer to each page, skipping the cover page."""
        if doc.page == 1:
            return
        canvas.saveState()
        # Footer is kept.
        footer_text = f"Page {doc.page} | Generated: {datetime.now().strftime('%Y-%m-%d')}"
        footer = Paragraph(footer_text, self.styles['CoverDate'])
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, h)
        canvas.restoreState()

    def _get_llm_summary(self, prompt_template: str, column_data: pd.Series, **kwargs) -> dict:
        """Invokes LLM and robustly parses the JSON response."""
        texts = [str(c).strip() for c in column_data.dropna() if str(c).strip()]
        if not texts: return {}
        sample_data = "\n---\n".join(texts)
        prompt = prompt_template.format(sample_data=sample_data, **kwargs)
        try:
            response = self.llm.invoke(prompt.strip())
            cleaned_response = re.sub(r"```json\n|```", "", response.content.strip())
            return json.loads(cleaned_response)
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"Warning: Could not parse LLM response. Error: {e}")
            return {}

    def build_pdf(self) -> BytesIO:
        """Assembles all components into the final PDF document."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)

        # Build document flowables in sequence
        self._build_cover_page()
        self._build_journey_section()
        self._build_rounds_sections()
        self._build_pie_chart_section()

        doc.build(self.elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)
        buffer.seek(0)
        return buffer

    def _build_cover_page(self):
        """Creates a professional cover page."""
        self.elements.append(Paragraph('Interview Insights Report', self.styles['CoverTitle']))
        self.elements.append(Spacer(1, 0.5 * inch))
        self.elements.append(Paragraph(f"Analysis for {self.company_name} - {self.role_name}", self.styles['CoverSubTitle']))
        self.elements.append(Spacer(1, 3 * inch))
        self.elements.append(Paragraph(f"Report Generated on: {datetime.now().strftime('%B %d, %Y')}", self.styles['CoverDate']))
        self.elements.append(PageBreak())

    def _build_journey_section(self):
        """Builds the 'Preparation Journey' section."""
        # FIX: The title is now INSIDE the list that will be kept together.
        section_content = [Paragraph('🧭 Preparation Journey', self.styles['Section'])]
        data = self._get_llm_summary(JOURNEY_PROMPT_TEMPLATE, self.df['journey'])

        if summary := data.get("summary_paragraph"):
            section_content.append(Paragraph(summary, self.styles['Body']))
        if mistakes := data.get("mistakes_to_avoid"):
            section_content.append(Paragraph('Mistakes to Avoid:', self.styles['SubSection']))
            items = [ListItem(Paragraph(m.lstrip('•*- ').strip(), self.styles['Bullet'])) for m in mistakes]
            section_content.append(ListFlowable(items, bulletType='bullet'))
        if tips := data.get("key_tips"):
            section_content.append(Paragraph('Key Tips:', self.styles['SubSection']))
            items = [ListItem(Paragraph(t.lstrip('•*- ').strip(), self.styles['Bullet'])) for t in tips]
            section_content.append(ListFlowable(items, bulletType='bullet'))

        self.elements.append(KeepTogether(section_content))
        self.elements.append(self.hr_line)

    def _build_rounds_sections(self):
        """Builds detailed sections for each interview round."""
        round_cols = sorted([c for c in self.df.columns if c.startswith('round_')], key=lambda x: int(x.split('_')[1]))
        for col in round_cols:
            idx = col.split('_')[1]

            # FIX: The title is now INSIDE the list that will be kept together.
            section_content = [Paragraph(f'🧪 Round {idx} Overview', self.styles['Section'])]
            data = self._get_llm_summary(ROUND_PROMPT_TEMPLATE, self.df[col], round_index=idx)

            if overview := data.get("overview"):
                section_content.append(Paragraph(overview, self.styles['Body']))
            if questions := data.get("coding_questions"):
                section_content.append(Paragraph('Coding Questions by Topic:', self.styles['SubSection']))
                items = [ListItem(Paragraph(q.lstrip('•*- ').strip(), self.styles['Bullet'])) for q in questions]
                section_content.append(ListFlowable(items, bulletType='bullet'))
            if links := data.get("problem_links"):
                section_content.append(Spacer(1, 0.2 * inch))
                section_content.append(Paragraph('🔗 Problem Links:', self.styles['SubSection']))
                table_data = [[Paragraph("Link to Online Problem", self.styles['SubSection'])]] + [[Paragraph(f'<a href="{link}">{link}</a>', self.styles['Link'])] for link in links]
                tbl = Table(table_data, colWidths=['100%'], repeatRows=1)
                tbl.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.lightgrey), ('GRID', (0,0), (-1,-1), 1, colors.black)]))
                section_content.append(tbl)

            self.elements.append(KeepTogether(section_content))
            self.elements.append(self.hr_line)

    def _build_pie_chart_section(self):
        """Builds a single, clean pie chart for the final page."""
        # FIX: The title is also grouped with its content here for consistency.
        section_content = [Paragraph('📊 Coding Topic Distribution', self.styles['Section'])]
        section_content.append(Spacer(1, 0.9 * inch))

        all_text = ' '.join(item.lower() for col in self.df.columns if col.startswith('round_') for item in self.df[col].dropna().astype(str))
        counts = Counter(topic for topic in CODING_TOPICS if topic.lower() in all_text)

        if not counts:
            section_content.append(Paragraph("No relevant coding topics found.", self.styles['Body']))
            self.elements.append(KeepTogether(section_content))
            return

        d = Drawing(4 * inch, 3 * inch)
        pie = Pie()
        pie.x = 140
        pie.y = 80
        pie.width = 150
        pie.height = 150
        pie.data = [v for k, v in counts.most_common()]
        pie.labels = [f"{k} ({v})" for k, v in counts.most_common()]
        pie.slices.strokeWidth = 0.5
        pie.sideLabels = True
        d.add(pie)

        section_content.append(d)
        self.elements.append(KeepTogether(section_content))

# --- Main Entry Point ---
def build_pdf(df: pd.DataFrame, llm, company_name: str, role_name: str) -> BytesIO:
    """Main entry point that your Streamlit app can call."""
    builder = PDFReportBuilder(df, llm, company_name, role_name)
    return builder.build_pdf()