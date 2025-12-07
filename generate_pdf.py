"""
PDF Generator for Job Interview Simulator Documentation

This script converts the Markdown documentation to a well-formatted PDF.
Uses reportlab for PDF generation and markdown parsing.
"""

import re
from typing import List, Tuple

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. Install with: pip install reportlab")


def parse_markdown(markdown_text: str) -> List[Tuple[str, str]]:
    """
    Simple markdown parser that extracts sections and content.
    Returns list of (element_type, content) tuples.
    """
    elements = []
    lines = markdown_text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Headers
        if line.startswith('# '):
            elements.append(('h1', line[2:].strip()))
        elif line.startswith('## '):
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            elements.append(('h3', line[4:].strip()))
        elif line.startswith('#### '):
            elements.append(('h4', line[5:].strip()))
        
        # Code blocks
        elif line.startswith('```'):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            elements.append(('code', '\n'.join(code_lines)))
        
        # Lists
        elif line.startswith('- ') or line.startswith('* '):
            list_items = []
            while i < len(lines) and (lines[i].strip().startswith('- ') or lines[i].strip().startswith('* ')):
                list_items.append(lines[i].strip()[2:].strip())
                i += 1
            elements.append(('list', list_items))
            continue
        
        # Regular paragraphs
        elif not line.startswith('#') and not line.startswith('```') and not line.startswith('---'):
            para_lines = []
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('```') and not lines[i].strip().startswith('- ') and not lines[i].strip().startswith('* ') and not lines[i].strip().startswith('---'):
                para_lines.append(lines[i].strip())
                i += 1
            if para_lines:
                elements.append(('para', ' '.join(para_lines)))
            continue
        
        i += 1
    
    return elements


def create_pdf_from_markdown(markdown_file: str, output_pdf: str):
    """Create PDF from Markdown file."""
    if not REPORTLAB_AVAILABLE:
        print("Error: reportlab library is required to generate PDF.")
        print("Install it with: pip install reportlab")
        return
    
    # Read markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Parse markdown
    elements = parse_markdown(markdown_content)
    
    # Create PDF document
    doc = SimpleDocTemplate(output_pdf, pagesize=letter,
                           rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        alignment=TA_JUSTIFY,
        leading=14
    )
    
    code_style = ParagraphStyle(
        'CustomCode',
        parent=styles['Code'],
        fontSize=9,
        textColor=colors.HexColor('#2c3e50'),
        backColor=colors.HexColor('#f5f5f5'),
        leftIndent=20,
        rightIndent=20,
        spaceAfter=12,
        fontName='Courier'
    )
    
    # Process elements
    for elem_type, content in elements:
        if elem_type == 'h1':
            # Add page break before major sections (except first)
            if story:  # Not the first element
                story.append(PageBreak())
            story.append(Paragraph(content, h1_style))
            story.append(Spacer(1, 0.2*inch))
        
        elif elem_type == 'h2':
            story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(content, h2_style))
            story.append(Spacer(1, 0.05*inch))
        
        elif elem_type == 'h3':
            story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(content, h3_style))
        
        elif elem_type == 'para':
            # Clean up markdown formatting in paragraphs
            para_text = content
            # Remove inline code markers
            para_text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', para_text)
            # Handle bold
            para_text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', para_text)
            # Handle italic
            para_text = re.sub(r'\*([^\*]+)\*', r'<i>\1</i>', para_text)
            
            story.append(Paragraph(para_text, normal_style))
        
        elif elem_type == 'list':
            for item in content:
                # Clean up list items
                item_text = item
                item_text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', item_text)
                item_text = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', item_text)
                
                story.append(Paragraph(f"• {item_text}", normal_style))
                story.append(Spacer(1, 0.05*inch))
        
        elif elem_type == 'code':
            # Format code blocks
            code_text = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            story.append(Paragraph(f'<font name="Courier" size="8">{code_text}</font>', code_style))
            story.append(Spacer(1, 0.1*inch))
    
    # Build PDF
    doc.build(story)
    print(f"PDF generated successfully: {output_pdf}")


def create_simple_pdf_alternative(markdown_file: str, output_pdf: str):
    """
    Alternative PDF creation using fpdf if reportlab is not available.
    This is a simpler implementation.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        print("Error: Neither reportlab nor fpdf is available.")
        print("Install one with: pip install reportlab OR pip install fpdf2")
        return
    
    # Read markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Create PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Set font
    pdf.set_font("Arial", size=12)
    
    # Parse and write content
    lines = markdown_content.split('\n')
    in_code_block = False
    code_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        if line_stripped.startswith('```'):
            if in_code_block:
                # End code block
                pdf.set_font("Courier", size=9)
                for code_line in code_lines:
                    pdf.cell(0, 6, code_line[:80], ln=1)
                code_lines = []
                pdf.set_font("Arial", size=12)
                in_code_block = False
            else:
                in_code_block = True
            continue
        
        if in_code_block:
            code_lines.append(line)
            continue
        
        if not line_stripped:
            pdf.ln(5)
            continue
        
        if line_stripped.startswith('# '):
            pdf.set_font("Arial", "B", 20)
            pdf.cell(0, 10, line_stripped[2:], ln=1)
            pdf.ln(5)
            pdf.set_font("Arial", size=12)
        
        elif line_stripped.startswith('## '):
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 8, line_stripped[3:], ln=1)
            pdf.ln(3)
            pdf.set_font("Arial", size=12)
        
        elif line_stripped.startswith('### '):
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 7, line_stripped[4:], ln=1)
            pdf.ln(2)
            pdf.set_font("Arial", size=12)
        
        elif line_stripped.startswith('- ') or line_stripped.startswith('* '):
            pdf.cell(10)
            pdf.cell(0, 6, "• " + line_stripped[2:], ln=1)
        
        elif line_stripped.startswith('---'):
            pdf.ln(5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
        
        else:
            # Regular paragraph
            # Remove markdown formatting
            text = line_stripped
            text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^\*]+)\*', r'\1', text)
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            # Wrap text
            pdf.multi_cell(0, 6, text)
            pdf.ln(3)
    
    pdf.output(output_pdf)
    print(f"PDF generated successfully: {output_pdf}")


if __name__ == "__main__":
    markdown_file = "documentation.md"
    output_pdf = "Job_Interview_Simulator_Documentation.pdf"
    
    print("Generating PDF from Markdown documentation...")
    
    if REPORTLAB_AVAILABLE:
        try:
            create_pdf_from_markdown(markdown_file, output_pdf)
        except Exception as e:
            print(f"Error with reportlab: {e}")
            print("Trying alternative method...")
            create_simple_pdf_alternative(markdown_file, output_pdf)
    else:
        create_simple_pdf_alternative(markdown_file, output_pdf)

