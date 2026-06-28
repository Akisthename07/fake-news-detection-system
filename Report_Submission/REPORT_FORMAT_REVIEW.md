# Report Format Review — AI Based Fake News Detection System

**Generated:** June 2026  
**Template source:** Official MVJCE VTU templates (unchanged structure)  
**Output folder:** `Report_Submission/`

---

## Generated Files

| File | Description |
|------|-------------|
| `01_Title_Page_FILLED.docx` | Official title page — content only replaced |
| `02_Certificate_TOC_FILLED.docx` | Certificate, Declaration, Acknowledgement, Abstract, TOC, Acronyms, List of Figures |
| `03_Chapters_FILLED.docx` | Chapters 1–6, Conclusions, Future Scope, References, Viva |
| `FINAL_AI_Based_Fake_News_Detection_Report.docx` | **Merged submission-ready document** |

**Regenerate anytime:**
```bash
python fill_college_template.py
```

---

## What Was Preserved (NOT changed)

- Title page layout and center alignment
- Certificate / Declaration / Acknowledgement page structure
- Font styles (Normal, Heading 1–4, List Paragraph)
- Margins (Title: 1"; Certificate: custom; Chapters: 1" sides)
- Chapter numbering format (CHAPTER 1 / INTRODUCTION duplicate headers)
- Section numbering (1.1, 1.2 … 6.16)
- TOC tab-aligned dot-leader format
- Table structures (signatures, student names, acronyms)
- Page numbering placeholders (roman i–iv, then chapter pages)

## What Was Replaced (content only)

| Location | New content |
|----------|-------------|
| Title `"Title"` | AI Based Fake News Detection System |
| Guide department | Department of Artificial Intelligence and Machine Learning (AIML) |
| Bottom department | DEPARTMENT OF ARTIFICIAL INTELLIGENCE AND MACHINE LEARNING |
| Certificate / Declaration title | AI Based Fake News Detection System |
| Abstract (5 paragraphs) | Fake news detection project summary |
| Keywords (3 lines) | TF-IDF, Flask, Gemini, etc. |
| Acronym table | 12 project acronyms |
| TOC subsection titles | Mapped from morphing-wing → fake-news sections |
| List of Figures | 31 figure entries with insertion markers |
| All chapter body text | Full project content |

---

## Manual Steps Before Submission

### 1. Student details (required)
- [ ] Fill student names and USNs in **Title Page** table (6 rows)
- [ ] Fill student names in **Declaration** signature table
- [ ] Fill student names in **Certificate** paragraph
- [ ] Add signatures and dates on Certificate / Declaration pages

### 2. Guide details (required)
- [ ] Fill project Co-Ordinator name in Acknowledgement (paragraph 35)
- [ ] Verify guide name: Prof. Sathya Narayanan N
- [ ] Verify department: AIML

### 3. Insert figures and screenshots
Replace every `[INSERT … HERE]` marker in the document:

#### Architecture diagrams (create in Draw.io / PowerPoint)
| Fig | Location | Content |
|-----|----------|---------|
| 1.1 | Ch.1 §1.1 | System architecture (Browser → Flask → services → APIs) |
| 1.5 | Ch.1 §1.5 | Three-tier architecture |
| 4.1 | Ch.4 §4.2 | Methodology flowchart |
| 4.5 | Ch.4 §4.6 | API integration diagram |

#### Code screenshots (VS Code, line numbers visible)
| Fig | File | Lines |
|-----|------|-------|
| 4.3 | `utils/text.py` | 1–21 |
| 4.4 | `train_model.py` | 58–91 |
| 5.2 | `config.py` | 1–39 |
| 5.3 | `utils/text.py` | 1–21 |
| 5.4 | `services/news_service.py` | 21–75 |
| 5.5 | `services/analysis.py` | 24–57 |
| 5.6 | `app.py` | 70–126 |
| 5.1 | Project folder tree | Explorer/VS Code sidebar |

#### Website screenshots (`python app.py` → localhost:5000)
| Fig | Page / Section |
|-----|----------------|
| 4.7 | Home page |
| 5.7 | Analysis Results dashboard |
| 6.5 | Sentiment + Clickbait sections |
| 6.6 | Source Credibility |
| 6.7 | Latest Headlines (GNews) |
| 6.9 | AI Explanation (Gemini) |
| 6.11 | Related Fact Checks |
| 6.12 | /diagnostics page |

#### Training / test result screenshots
| Fig | Source |
|-----|--------|
| 4.6, 6.1, 6.3, 6.4, 6.10 | `model_analysis.png` (crop each subplot) |
| 4.8, 6.8 | Terminal: `python -m pytest tests/ -v` |

### 4. Update page numbers (after inserting figures)
- [ ] Open FINAL document in Microsoft Word
- [ ] Insert → Page Number (match college format)
- [ ] Update TOC page numbers: References → Update Field → Update entire table
- [ ] Update List of Figures page numbers manually or via Word caption system
- [ ] Verify Chapter 1 starts on page 1

---

## Format Review Findings

### Alignment — OK
| Element | Status | Notes |
|---------|--------|-------|
| Title page text | ✅ CENTER preserved | All lines center-aligned |
| Chapter headers | ✅ CENTER preserved | CHAPTER X / INTRODUCTION pattern kept |
| Section headings | ✅ Heading 4 style | Matches template (1.1 Background format) |
| Body text | ✅ JUSTIFY preserved | All chapter paragraphs justified |
| Figure captions | ✅ CENTER preserved | FIG X.X: format matches template |
| TOC entries | ✅ Tab leaders preserved | Original tab spacing maintained |
| Certificate text | ✅ JUSTIFY preserved | |

### Page breaks — ACTION NEEDED
| Issue | Recommendation |
|-------|----------------|
| Chapters run continuously | Insert **page break before each CHAPTER banner** if college requires chapters on new pages |
| Conclusions / References | Page breaks already added before these sections |
| Large figures | After inserting screenshots, add page breaks if figures split across pages awkwardly |
| Certificate page | Keep on separate page (already isolated in front matter) |

**Word command:** Place cursor before "CHAPTER 2" → Layout → Breaks → Page Break

### Figure numbering — REVIEW
| Issue | Status | Action |
|-------|--------|--------|
| Sequential numbering | ⚠️ Gaps exist | Figures jump 1.1→1.2→1.4 (no 1.3) — acceptable if no content for 1.3, or add Fig 1.3 for Motivation diagram |
| Duplicate FIG labels | ✅ OK | Each section has one figure caption |
| List of Figures vs body | ⚠️ Match needed | Ensure all inserted figures match List of Figures entries |
| Page numbers in LoF | ❌ Blank | Fill after final pagination |

### TOC — UPDATE REQUIRED
| TOC entry | Status |
|-----------|--------|
| Chapter titles | ✅ Unchanged (Introduction, Literature Survey, etc.) |
| Subsection titles | ✅ Updated to fake-news content |
| Page numbers | ❌ Still show template values (2, 3, 16, 21…) — **must update in Word** |
| Chapter 5 subsection pages | ⚠️ Template used internal numbers (21–25) — renumber after pagination |

**Critical:** After adding figures and page numbers, right-click TOC → **Update Entire Table**.

---

## Known Items Left as Placeholders

These are intentional — fill manually:
- `Student Name (USN)` — 6 students
- `Prof. ________` — Co-Ordinator name in Acknowledgement
- `Date:` and `Place: Bengaluru` — Declaration
- Signature table cells — all blank
- `[INSERT … HERE]` — all figure/screenshot locations
- List of Figures page numbers — blank tabs

---

## Security Reminder

Do **not** include API keys in any screenshot. Blur `.env` contents if visible.

---

## Final Submission Checklist

- [ ] Student names and USNs filled on all pages
- [ ] Guide and Co-Ordinator names filled
- [ ] All 31 figures inserted at marked locations
- [ ] Page numbers added throughout document
- [ ] TOC updated (Update Entire Table)
- [ ] List of Figures page numbers filled
- [ ] Spell-check run in Word
- [ ] PDF export reviewed for alignment
- [ ] Signatures obtained on Certificate and Declaration
- [ ] File named per college convention (e.g., `USN_ProjectReport.pdf`)

---

*This review document accompanies the generated Word files in `Report_Submission/`.*
