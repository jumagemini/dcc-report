from io import BytesIO
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ROW_HEIGHT_RULE
from docx.oxml import parse_xml
from docx.oxml.ns import qn, nsdecls
from .models import DCC

def set_table_cant_split(table, cant_split=True):
    """Prevent a table from being broken across pages."""
    tbl = table._tbl
    tblPr = tbl.tblPr
    if tblPr is None:
        tblPr = parse_xml(f'<w:tblPr {nsdecls("w")}></w:tblPr>')
        tbl.insert(0, tblPr)
    for cs in tblPr.findall(qn('w:cantSplit')):
        tblPr.remove(cs)
    if cant_split:
        cant_split_elem = parse_xml(f'<w:cantSplit {nsdecls("w")} w:val="true"/>')
        tblPr.append(cant_split_elem)

def add_institution_block(cell, inst):
    # Clear default paragraph
    cell.paragraphs[0].clear()

    devices = []
    if inst.indoor_ap1_serial:
        devices.append(('INDOOR AP1', inst.indoor_ap1_location))
    if inst.indoor_ap2_serial:
        devices.append(('INDOOR AP2', inst.indoor_ap2_location))
    if inst.indoor_ap3_serial:
        devices.append(('INDOOR AP3', inst.indoor_ap3_location))
    if inst.outdoor_ap_serial:
        devices.append(('OUTDOOR AP1', inst.outdoor_ap_location))

    if not devices:
        p = cell.add_paragraph()
        run = p.add_run(inst.name.upper())
        run.bold = True
        run.font.size = Pt(10)
        return

    inner_table = cell.add_table(rows=1+len(devices), cols=2)
    set_table_cant_split(inner_table, True)
    inner_table.style = 'Table Grid'

    for row in inner_table.rows:
        row.height = Inches(0.35)

    # Institution name row (merged)
    hdr_cells = inner_table.rows[0].cells
    merged = hdr_cells[0].merge(hdr_cells[1])
    merged.text = inst.name.upper()
    for paragraph in merged.paragraphs:
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        for run in paragraph.runs:
            run.bold = True
            run.font.size = Pt(11)

    for idx, (dev_name, location) in enumerate(devices, start=1):
        row_cells = inner_table.rows[idx].cells
        row_cells[0].text = dev_name
        row_cells[1].text = location
        for paragraph in row_cells[0].paragraphs:
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            for run in paragraph.runs:
                run.bold = True
                run.font.size = Pt(10)
        for paragraph in row_cells[1].paragraphs:
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            for run in paragraph.runs:
                run.font.size = Pt(10)

    # No spacer paragraph added

def generate_dcc_stickers_docx(dcc):
    doc = Document()
    for section in doc.sections:
        section.top_margin = Cm(1)
        section.bottom_margin = Cm(1)
        section.left_margin = Cm(1)
        section.right_margin = Cm(1)

    institutions = list(dcc.institutions.all().order_by('name'))
    chunk_size = 8
    for i in range(0, len(institutions), chunk_size):
        chunk = institutions[i:i+chunk_size]
        if i > 0:
            doc.add_page_break()

        master = doc.add_table(rows=4, cols=2)
        master.autofit = True
        set_table_cant_split(master, True)

        # Shrink master table spacing
        for row in master.rows:
            row.height = Inches(0.01)
            row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_before = Pt(0)
                    paragraph.paragraph_format.space_after = Pt(0)
                # Remove cell margins
                tc = cell._tc
                tcPr = tc.get_or_add_tcPr()
                for el in tcPr.findall(qn('w:tcMar')):
                    tcPr.remove(el)

        for row_idx in range(4):
            for col_idx in range(2):
                inst_idx = row_idx * 2 + col_idx
                if inst_idx < len(chunk):
                    cell = master.cell(row_idx, col_idx)
                    add_institution_block(cell, chunk[inst_idx])

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer