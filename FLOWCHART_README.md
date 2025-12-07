# Flowchart Documentation - Job Interview Simulator

This directory contains accurate flowcharts of the Job Interview Simulator system, based on the actual codebase implementation.

## Files Overview

1. **flowchart.md** - Comprehensive flowchart documentation with:
   - Mermaid flowchart code (copy-paste into Mermaid viewer)
   - Detailed text-based flow
   - Component interaction diagram
   - Data flow summary

2. **flowchart.dot** - Graphviz DOT format flowchart
   - Can be converted to PNG, SVG, PDF
   - Professional diagram format

3. **flowchart_simplified.md** - Simplified visual overview
   - Quick reference diagram
   - Step-by-step flow
   - Key data structures
   - Communication patterns
   - Timing diagram

## How to View/Generate Flowcharts

### Option 1: Mermaid Flowchart (Easiest)

1. Copy the Mermaid code from `flowchart.md` (between the ```mermaid blocks)
2. Paste into one of these viewers:
   - **Online**: https://mermaid.live/
   - **VS Code**: Install "Markdown Preview Mermaid Support" extension
   - **GitHub**: Markdown files with Mermaid render automatically

### Option 2: Graphviz DOT (Most Professional)

**Install Graphviz:**
- Windows: Download from https://graphviz.org/download/
- Mac: `brew install graphviz`
- Linux: `sudo apt-get install graphviz`

**Generate Images:**
```bash
# Generate PNG
dot -Tpng flowchart.dot -o flowchart.png

# Generate PDF
dot -Tpdf flowchart.dot -o flowchart.pdf

# Generate SVG (scalable)
dot -Tsvg flowchart.dot -o flowchart.svg
```

### Option 3: Online DOT Renderers

1. Copy content from `flowchart.dot`
2. Paste into:
   - https://dreampuf.github.io/GraphvizOnline/
   - https://edotor.net/
   - https://graphviz.it/

### Option 4: View Simplified Text Diagram

Simply open `flowchart_simplified.md` in any Markdown viewer or text editor. The ASCII diagrams are readable as-is.

## Flowchart Highlights

### Key Components Shown

1. **Interviewer Agent**
   - Session state management
   - Question generation
   - Answer processing
   - Final report generation

2. **MeTTa Knowledge Graph**
   - Pure Python implementation
   - Persona skill mappings
   - Topic priorities
   - Role requirements

3. **Evaluator Agent**
   - Answer evaluation
   - Score calculation
   - Feedback generation

4. **ASI Cloud API**
   - Question generation
   - Answer evaluation

### Key Flows Documented

1. **Initialization Flow**
   - User starts conversation
   - Role auto-set
   - Avatar selection

2. **Question Generation Flow**
   - KG query for persona skills
   - ASI Cloud API call
   - Adaptive question generation

3. **Interview Loop**
   - Answer storage
   - Async evaluation request
   - Immediate next question

4. **Evaluation Flow**
   - Async processing
   - Silent storage
   - No interruption to interview

5. **Final Report Flow**
   - Wait for all evaluations
   - Generate comprehensive report
   - Send to user

## Flowchart Accuracy

These flowcharts are based on:
- ✅ Actual code analysis from all 5 files
- ✅ Real message flow between agents
- ✅ Actual knowledge graph queries
- ✅ Actual API integration points
- ✅ Real session state management
- ✅ Accurate evaluation process

**Corrections from Original:**
- Knowledge graph is in-process Python calls (not network)
- Evaluation is async (interview continues without waiting)
- Questions are adaptive (use conversation history)
- Final report only sent after all evaluations received

## Integration with Documentation

These flowcharts complement:
- `documentation.md` - Full technical documentation
- Code files - Actual implementation

The flowcharts provide visual representation of the processes described in detail in the documentation.

## Quick Reference

### Mermaid Viewers
- https://mermaid.live/ (online, no install)
- VS Code extension: "Markdown Preview Mermaid Support"

### Graphviz Tools
- Command line: `dot` (after installing Graphviz)
- Online: https://dreampuf.github.io/GraphvizOnline/

### Best Format for PDF
1. Use Graphviz DOT → PDF (highest quality)
2. Or Mermaid → PNG → Insert into PDF
3. Or use simplified ASCII diagrams in documentation

## Recommendations

- **For Quick Viewing**: Use Mermaid online viewer with code from `flowchart.md`
- **For Documentation PDF**: Use Graphviz to generate high-quality PDF from `flowchart.dot`
- **For Quick Reference**: View `flowchart_simplified.md` directly
- **For Presentations**: Generate PNG from DOT file, insert into slides

