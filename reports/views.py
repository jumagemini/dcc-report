from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from weasyprint import HTML
from .models import DCC, Institution, InstitutionPhoto
from .forms import InstitutionForm, PhotoUploadForm
import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.drawing.spreadsheet_drawing import AnchorMarker, TwoCellAnchor
from io import BytesIO
import base64
import logging
import re

logger = logging.getLogger(__name__)

def sanitize_filename(name):
    # Replace spaces with underscores and remove non-alphanumeric/underscore/hyphen
    name = name.replace(' ', '_')
    return re.sub(r'[^\w\-]', '', name)

def institution_create(request, dcc_id):
    dcc = get_object_or_404(DCC, pk=dcc_id)
    if request.method == 'POST':
        form = InstitutionForm(request.POST)
        photo_form = PhotoUploadForm(request.POST, request.FILES)
        if form.is_valid() and photo_form.is_valid():
            print("Form valid:", form.is_valid())
            print("Photo form valid:", photo_form.is_valid())
            institution = form.save(commit=False)
            institution.dcc = dcc
            institution.save()

            if not form.is_valid():
                print("Form errors:", form.errors)
            if not photo_form.is_valid():
                print("Photo errors:", photo_form.errors)    

            # Mapping of field names to device_type codes
            device_mapping = {
                'before_onu': ('before', 'ONU'),
                'before_ap1': ('before', 'AP1'),
                'before_ap2': ('before', 'AP2'),
                'before_ap3': ('before', 'AP3'),
                'before_out': ('before', 'OUT'),
                'after_onu': ('after', 'ONU'),
                'after_ap1': ('after', 'AP1'),
                'after_ap2': ('after', 'AP2'),
                'after_ap3': ('after', 'AP3'),
                'after_out': ('after', 'OUT'),
            }

            for field_name, (photo_type, device_type) in device_mapping.items():
                image_file = photo_form.cleaned_data.get(field_name)
                if image_file:
                    InstitutionPhoto.objects.update_or_create(
                        institution=institution,
                        photo_type=photo_type,
                        device_type=device_type,
                        defaults={'image': image_file}
                    )
            pdf_url = reverse('institution_pdf_preview', args=[institution.pk])
            #full_pdf_url = request.build_absolute_uri(pdf_url)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Installation for {institution.name} saved.',
                    'pdf_url': pdf_url
                })
            messages.success(request, f'Installation for {institution.name} saved.')
            return redirect('institution_pdf', pk=institution.pk)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                errors = {}
                errors.update(form.errors)
                errors.update(photo_form.errors)
                return JsonResponse({'success': False, 'errors': errors}, status=400)
    else:
        form = InstitutionForm()
        photo_form = PhotoUploadForm()
    return render(request, 'reports/institution_form.html', {
        'form': form,
        'photo_form': photo_form,
        'dcc': dcc
    })

def generate_dcc_excel(request, dcc_id):
    dcc = get_object_or_404(DCC, pk=dcc_id)
    institutions = dcc.institutions.all().order_by('name')

    wb = openpyxl.Workbook()
    # ===================== SHEET 1: DEVICE SUMMARY =====================
    ws1 = wb.active
    ws1.title = "Device Summary"

    # --- Title Rows (with merged cells) ---
    # Row 2: Project name
    cell = ws1.cell(row=2, column=2, value=f"Project name: {dcc.project_name}")
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal='left')
    ws1.merge_cells(start_row=2, start_column=2, end_row=2, end_column=12)

    # Row 3: DCC name
    cell = ws1.cell(row=3, column=2, value=f"DCC: {dcc.name}")
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal='left')
    ws1.merge_cells(start_row=3, start_column=2, end_row=3, end_column=12)

    # Row 4: "Devices serial numbers"
    cell = ws1.cell(row=4, column=2, value="Devices serial numbers")
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal='left')
    ws1.merge_cells(start_row=4, start_column=2, end_row=4, end_column=12)

    # Row 5: DCC name again
    cell = ws1.cell(row=5, column=2, value=dcc.name)
    cell.font = Font(bold=True, size=12)
    cell.alignment = Alignment(horizontal='left')
    ws1.merge_cells(start_row=5, start_column=2, end_row=5, end_column=12)

    # Row 6: Institution count and group headers
    cell = ws1.cell(row=6, column=2, value=f"{institutions.count()} Institutions.")
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='left')
    ws1.merge_cells(start_row=6, start_column=2, end_row=6, end_column=2)

    cell = ws1.cell(row=6, column=3, value="Indoor Access point")
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='center')
    ws1.merge_cells(start_row=6, start_column=3, end_row=6, end_column=8)

    cell = ws1.cell(row=6, column=9, value="Outdoor AP")
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='center')
    ws1.merge_cells(start_row=6, start_column=9, end_row=6, end_column=10)

    cell = ws1.cell(row=6, column=11, value="4 port ONU")
    cell.font = Font(bold=True)
    cell.alignment = Alignment(horizontal='center')
    ws1.merge_cells(start_row=6, start_column=11, end_row=6, end_column=12)

    # Row 7: Column headers (exactly as in file)
    headers = [
        "",  # A column will have index numbers
        "Name of Institution",
        "Serial Numbers", "Location",
        "Serial Numbers", "Location",
        "Serial Numbers", "Location",
        "Serial Numbers", "Location",
        "Serial Numbers", "Location"
    ]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws1.cell(row=7, column=col_idx, value=header)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center', wrap_text=True)

    # --- Data Rows ---
    start_row = 8
    for idx, inst in enumerate(institutions, start=1):
        row = start_row + idx - 1
        # Index number in column A
        ws1.cell(row=row, column=1, value=idx)
        # Institution name column B
        ws1.cell(row=row, column=2, value=inst.name)

        # Indoor AP1 serial/location (columns C,D) - mandatory
        ws1.cell(row=row, column=3, value=inst.indoor_ap1_serial)
        ws1.cell(row=row, column=4, value=inst.indoor_ap1_location)

        # Indoor AP2 serial/location (columns E,F) - optional, replace empty with 'N/A'
        ap2_serial = inst.indoor_ap2_serial if inst.indoor_ap2_serial else 'N/A'
        ap2_location = inst.indoor_ap2_location if inst.indoor_ap2_location else 'N/A'
        cell_e = ws1.cell(row=row, column=5, value=ap2_serial)
        cell_f = ws1.cell(row=row, column=6, value=ap2_location)
        cell_e.alignment = Alignment(horizontal='center', vertical='center')
        cell_f.alignment = Alignment(horizontal='center', vertical='center')

        # Indoor AP3 serial/location (columns G,H) - optional, replace empty with 'N/A'
        ap3_serial = inst.indoor_ap3_serial if inst.indoor_ap3_serial else 'N/A'
        ap3_location = inst.indoor_ap3_location if inst.indoor_ap3_location else 'N/A'
        cell_g = ws1.cell(row=row, column=7, value=ap3_serial)
        cell_h = ws1.cell(row=row, column=8, value=ap3_location)
        cell_g.alignment = Alignment(horizontal='center', vertical='center')
        cell_h.alignment = Alignment(horizontal='center', vertical='center')

        # Outdoor AP serial/location (columns I,J) - mandatory
        ws1.cell(row=row, column=9, value=inst.outdoor_ap_serial)
        ws1.cell(row=row, column=10, value=inst.outdoor_ap_location)

        # ONU serial/location (columns K,L) - mandatory
        ws1.cell(row=row, column=11, value=inst.onu_serial)
        ws1.cell(row=row, column=12, value=inst.onu_location)

    # --- Column Widths ---
    ws1.column_dimensions['A'].width = 5
    ws1.column_dimensions['B'].width = 45
    for col in ['C','E','G','I','K']:
        ws1.column_dimensions[col].width = 22
    for col in ['D','F','H','J','L']:
        ws1.column_dimensions[col].width = 20

        # ===================== SHEET 2: PHOTOS =====================
    ws2 = wb.create_sheet(title="Installation Photos")

    # Set column widths
    col_widths = {
        'A': 35, 'B': 5, 'C': 30, 'D': 5, 'E': 5,
        'F': 30, 'G': 5, 'H': 5, 'I': 30, 'J': 5,
        'K': 5, 'L': 30, 'M': 30
    }
    for col, width in col_widths.items():
        ws2.column_dimensions[col].width = width

    device_cols = {
        'ONU': 1, 'AP1': 3, 'AP2': 6, 'AP3': 9, 'OUT': 12,
    }

    IMG_WIDTH = 200
    IMG_HEIGHT = 150
    IMAGE_ROW_HEIGHT = 160
    LABEL_ROW_HEIGHT = 25   # height for label rows

    current_row = 1
    for idx, inst in enumerate(institutions, start=1):
        # Institution Name (merged)
        ws2.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=13)
        cell = ws2.cell(row=current_row, column=1, value=f"{idx}. {inst.name.upper()}")
        cell.font = Font(bold=True, size=12)
        cell.alignment = Alignment(horizontal='left')
        current_row += 1

        # Blank row
        current_row += 1

        # BEFORE INSTALLATION header
        ws2.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=13)
        cell = ws2.cell(row=current_row, column=1, value="BEFORE INSTALLATION")
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal='left')
        current_row += 1

        # Image row for BEFORE
        before_image_row = current_row
        ws2.row_dimensions[before_image_row].height = IMAGE_ROW_HEIGHT
        current_row += 1

        # Place before images without offset (anchor to top-left of cell)
        for dev, col_idx in device_cols.items():
            photo = inst.photos.filter(photo_type='before', device_type=dev).first()
            cell_ref = f'{get_column_letter(col_idx)}{before_image_row}'
            if photo:
                img = XLImage(photo.image.path)
                img.width = IMG_WIDTH
                img.height = IMG_HEIGHT
                ws2.add_image(img, cell_ref)
            else:
                cell = ws2.cell(row=before_image_row, column=col_idx, value='N/A')
                cell.font = Font(bold=True, size=11)
                cell.alignment = Alignment(horizontal='center', vertical='center')    

        # Label row for BEFORE
        label_row = current_row
        ws2.row_dimensions[label_row].height = LABEL_ROW_HEIGHT
        current_row += 1

        # Determine installed devices
        has_device = {
            'ONU': bool(inst.onu_serial),
            'AP1': bool(inst.indoor_ap1_serial),
            'AP2': bool(inst.indoor_ap2_serial),
            'AP3': bool(inst.indoor_ap3_serial),
            'OUT': bool(inst.outdoor_ap_serial),
        }

        labels = {}
        if has_device['ONU']:
            labels['ONU'] = f"ONU {inst.onu_location}" if inst.onu_location else "ONU"
        if has_device['AP1']:
            labels['AP1'] = f"INDOOR AP1 {inst.indoor_ap1_location}" if inst.indoor_ap1_location else "INDOOR AP1"
        if has_device['AP2']:
            labels['AP2'] = f"INDOOR AP2 {inst.indoor_ap2_location}" if inst.indoor_ap2_location else "INDOOR AP2"
        if has_device['AP3']:
            labels['AP3'] = f"INDOOR AP3 {inst.indoor_ap3_location}" if inst.indoor_ap3_location else "INDOOR AP3"
        if has_device['OUT']:
            labels['OUT'] = f"OUTDOOR AP1 {inst.outdoor_ap_location}" if inst.outdoor_ap_location else "OUTDOOR AP1"

        # Write BEFORE labels
        if 'ONU' in labels:
            cell = ws2.cell(row=label_row, column=1, value=labels['ONU'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'AP1' in labels:
            ws2.merge_cells(start_row=label_row, start_column=3, end_row=label_row, end_column=4)
            cell = ws2.cell(row=label_row, column=3, value=labels['AP1'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'AP2' in labels:
            ws2.merge_cells(start_row=label_row, start_column=6, end_row=label_row, end_column=7)
            cell = ws2.cell(row=label_row, column=6, value=labels['AP2'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'AP3' in labels:
            ws2.merge_cells(start_row=label_row, start_column=9, end_row=label_row, end_column=10)
            cell = ws2.cell(row=label_row, column=9, value=labels['AP3'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'OUT' in labels:
            ws2.merge_cells(start_row=label_row, start_column=12, end_row=label_row, end_column=13)
            cell = ws2.cell(row=label_row, column=12, value=labels['OUT'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)

        # AFTER INSTALLATION header
        ws2.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=13)
        cell = ws2.cell(row=current_row, column=1, value="AFTER INSTALLATION")
        cell.font = Font(bold=True, size=11)
        cell.alignment = Alignment(horizontal='left')
        current_row += 1

        # Image row for AFTER
        after_image_row = current_row
        ws2.row_dimensions[after_image_row].height = IMAGE_ROW_HEIGHT
        current_row += 1

        # Place after images
        for dev, col_idx in device_cols.items():
            photo = inst.photos.filter(photo_type='after', device_type=dev).first()
            cell_ref = f'{get_column_letter(col_idx)}{after_image_row}'
            if photo:
                img = XLImage(photo.image.path)
                img.width = IMG_WIDTH
                img.height = IMG_HEIGHT
                ws2.add_image(img, cell_ref)
            else:
                cell = ws2.cell(row=after_image_row, column=col_idx, value='N/A')
                cell.font = Font(bold=True, size=11)
                cell.alignment = Alignment(horizontal='center', vertical='center')


        # Label row for AFTER
        label_row = current_row
        ws2.row_dimensions[label_row].height = LABEL_ROW_HEIGHT
        current_row += 1

        # Write AFTER labels (same as BEFORE)
        if 'ONU' in labels:
            cell = ws2.cell(row=label_row, column=1, value=labels['ONU'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'AP1' in labels:
            ws2.merge_cells(start_row=label_row, start_column=3, end_row=label_row, end_column=4)
            cell = ws2.cell(row=label_row, column=3, value=labels['AP1'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'AP2' in labels:
            ws2.merge_cells(start_row=label_row, start_column=6, end_row=label_row, end_column=7)
            cell = ws2.cell(row=label_row, column=6, value=labels['AP2'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'AP3' in labels:
            ws2.merge_cells(start_row=label_row, start_column=9, end_row=label_row, end_column=10)
            cell = ws2.cell(row=label_row, column=9, value=labels['AP3'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)
        if 'OUT' in labels:
            ws2.merge_cells(start_row=label_row, start_column=12, end_row=label_row, end_column=13)
            cell = ws2.cell(row=label_row, column=12, value=labels['OUT'])
            cell.alignment = Alignment(horizontal='center', wrap_text=True)

        # Spacer between institutions
        current_row += 1

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{dcc.name}_report.xlsx"'
    return response

def get_image_base64(filename):
    image_path = settings.BASE_DIR / 'static' / 'images' / filename
    try:
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    except FileNotFoundError:
        logger.error(f"Logo file not found: {image_path}")
        return ""  # return empty string or a placeholder base64

def preview_institution_pdf(request, pk):
    institution = get_object_or_404(Institution, pk=pk)
    print(f"DEBUG: project_no = '{institution.project_no}'")  # check console

    # Build sequential device list
    devices = []
    item_no = 1
    
    # ONU (mandatory)
    devices.append({
        'item_no': item_no,
        'name': 'ONU',
        'serial': institution.onu_serial,
        'quantity': 1,
        'location': institution.onu_location,
    })
    item_no += 1
    
    # Indoor AP1 (mandatory)
    devices.append({
        'item_no': item_no,
        'name': 'INDOOR AP1',
        'serial': institution.indoor_ap1_serial,
        'quantity': 1,
        'location': institution.indoor_ap1_location,
    })
    item_no += 1
    
    # Indoor AP2 (optional)
    if institution.indoor_ap2_serial:
        devices.append({
            'item_no': item_no,
            'name': 'INDOOR AP2',
            'serial': institution.indoor_ap2_serial,
            'quantity': 1,
            'location': institution.indoor_ap2_location,
        })
        item_no += 1
    
    # Indoor AP3 (optional)
    if institution.indoor_ap3_serial:
        devices.append({
            'item_no': item_no,
            'name': 'INDOOR AP3',
            'serial': institution.indoor_ap3_serial,
            'quantity': 1,
            'location': institution.indoor_ap3_location,
        })
        item_no += 1
    
    # Outdoor AP1 (mandatory)
    devices.append({
        'item_no': item_no,
        'name': 'OUTDOOR AP1',
        'serial': institution.outdoor_ap_serial,
        'quantity': 1,
        'location': institution.outdoor_ap_location,
    })

    try:
        context = {
            'institution': institution,
            'devices': devices,
            'logo_left': get_image_base64('kplc.png'),
            'logo_right': get_image_base64('ict.png'),
        }
        html_string = render_to_string('reports/institution_pdf.html', context)
        html = HTML(string=html_string, base_url=request.build_absolute_uri())
        pdf = html.write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        # Create Safe Filename
        dcc_name = sanitize_filename(institution.dcc.name)
        inst_name = sanitize_filename(institution.name)
        filename = f"{dcc_name}_{inst_name}.pdf"

        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except Exception as e:
        logger.exception("PDF generation failed")
        return HttpResponse(f"Error generating PDF: {e}", status=500)

def generate_institution_pdf(request, pk):
    institution = get_object_or_404(Institution, pk=pk)

    # Build sequential device list
    devices = []
    item_no = 1

    # ONU
    devices.append({
        'item_no': item_no,
        'name': 'ONU',
        'serial': institution.onu_serial,
        'quantity': 1,
        'location': institution.onu_location,
    })
    item_no += 1

    # Indoor AP1
    devices.append({
        'item_no': item_no,
        'name': 'INDOOR AP1',
        'serial': institution.indoor_ap1_serial,
        'quantity': 1,
        'location': institution.indoor_ap1_location,
    })
    item_no += 1

    # Indoor AP2 (optional)
    if institution.indoor_ap2_serial:
        devices.append({
            'item_no': item_no,
            'name': 'INDOOR AP2',
            'serial': institution.indoor_ap2_serial,
            'quantity': 1,
            'location': institution.indoor_ap2_location,
        })
        item_no += 1

    # Indoor AP3 (optional)
    if institution.indoor_ap3_serial:
        devices.append({
            'item_no': item_no,
            'name': 'INDOOR AP3',
            'serial': institution.indoor_ap3_serial,
            'quantity': 1,
            'location': institution.indoor_ap3_location,
        })
        item_no += 1

    # Outdoor AP1
    devices.append({
        'item_no': item_no,
        'name': 'OUTDOOR AP1',
        'serial': institution.outdoor_ap_serial,
        'quantity': 1,
        'location': institution.outdoor_ap_location,
    })

    context = {
        'institution': institution,
        'devices': devices,
        'logo_left': get_image_base64('kplc.png'),
        'logo_right': get_image_base64('ict.png'),
    }
    html_string = render_to_string('reports/institution_pdf.html', context)
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')

    dcc_name = sanitize_filename(institution.dcc.name)
    inst_name = sanitize_filename(institution.name)
    filename = f"{dcc_name}_{inst_name}.pdf"
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    return response

