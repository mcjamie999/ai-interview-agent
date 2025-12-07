# How to Generate PDF Documentation

This guide explains how to convert the Markdown documentation (`documentation.md`) into a PDF file.

## Option 1: Using Python Script (Recommended)

### Prerequisites

Install required library:
```bash
pip install reportlab
```

Or alternatively:
```bash
pip install fpdf2
```

### Generate PDF

Run the Python script:
```bash
python generate_pdf.py
```

This will create `Job_Interview_Simulator_Documentation.pdf` in the current directory.

## Option 2: Using Online Converters

1. Open `documentation.md` in a text editor
2. Copy the content
3. Use an online Markdown to PDF converter such as:
   - https://www.markdowntopdf.com/
   - https://dillinger.io/ (export as PDF)
   - https://stackedit.io/ (export as PDF)

## Option 3: Using Pandoc (Command Line)

If you have Pandoc installed:

```bash
pandoc documentation.md -o Job_Interview_Simulator_Documentation.pdf --pdf-engine=xelatex
```

Or using wkhtmltopdf:
```bash
pandoc documentation.md -o Job_Interview_Simulator_Documentation.pdf --pdf-engine=wkhtmltopdf
```

## Option 4: Using VS Code Extension

1. Install "Markdown PDF" extension in VS Code
2. Open `documentation.md`
3. Right-click and select "Markdown PDF: Export (pdf)"

## Option 5: Using Browser Print

1. Open `documentation.md` in a Markdown previewer (VS Code, GitHub, etc.)
2. Use browser print function (Ctrl+P / Cmd+P)
3. Select "Save as PDF" as the destination

---

## Troubleshooting

### Python Script Errors

If `generate_pdf.py` fails:

1. **Missing reportlab**: Install with `pip install reportlab`
2. **Missing fpdf2**: Install with `pip install fpdf2`
3. **Encoding errors**: Ensure `documentation.md` is UTF-8 encoded

### PDF Formatting Issues

The Python script may not perfectly preserve all Markdown formatting. For best results:
- Use Pandoc (Option 3) for professional formatting
- Use online converters (Option 2) for quick conversion
- Use VS Code extension (Option 4) for integrated workflow

---

## File Locations

- **Source**: `documentation.md` - Markdown documentation
- **Output**: `Job_Interview_Simulator_Documentation.pdf` - Generated PDF
- **Script**: `generate_pdf.py` - PDF generation script

