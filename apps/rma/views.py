import csv
import io
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from .models import PartsReturn
from .forms import PartsReturnForm, PartsReturnImportForm

TEMPLATE_HEADERS = [
    'Client Name', 'Order NO.', 'Part Amt', 'Part Name', 'Model No.',
    'Serial No.', 'RMA No.', 'Date RMA Requested', 'Date Part Returned',
    'Credit Received', 'RMA Credit Received', 'Replacement Ordered Date',
]

@login_required
def parts_return_list(request):
    if request.user.is_superuser:
        returns = PartsReturn.objects.all()
    else:
        returns = PartsReturn.objects.filter(user=request.user)
    return render(request, 'rma/parts_return_list.html', {'returns': returns})

@login_required
def parts_return_add(request):
    form = PartsReturnForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        rma = form.save(commit=False)
        rma.user = request.user
        rma.save()
        messages.success(request, 'Parts return added successfully!')
        return redirect('parts_return_list')
    return render(request, 'rma/parts_return_form.html', {'form': form, 'title': 'Add Parts Return'})

@login_required
def parts_return_edit(request, pk):
    if request.user.is_superuser:
        rma = get_object_or_404(PartsReturn, pk=pk)
    else:
        rma = get_object_or_404(PartsReturn, pk=pk, user=request.user)
    form = PartsReturnForm(request.POST or None, instance=rma)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Parts return updated successfully!')
        return redirect('parts_return_list')
    return render(request, 'rma/parts_return_form.html', {'form': form, 'title': 'Edit Parts Return'})

@login_required
def parts_return_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete entries.')
        return redirect('parts_return_list')
    rma = get_object_or_404(PartsReturn, pk=pk)
    rma.delete()
    messages.success(request, 'Parts return deleted.')
    return redirect('parts_return_list')

@login_required
def parts_return_export(request):
    if request.user.is_superuser:
        returns = PartsReturn.objects.all()
    else:
        returns = PartsReturn.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="parts_returns.csv"'
    writer = csv.writer(response)
    writer.writerow(TEMPLATE_HEADERS)
    for r in returns:
        writer.writerow([
            r.client_name or '', r.order_no or '', r.part_amt or '', r.part_name or '',
            r.model_no or '', r.serial_no or '', r.rma_no or '',
            r.date_rma_requested.strftime('%m/%d/%Y') if r.date_rma_requested else '',
            r.date_part_returned.strftime('%m/%d/%Y') if r.date_part_returned else '',
            r.credit_received.strftime('%m/%d/%Y') if r.credit_received else '',
            r.rma_credit_received or '', r.replacement_ordered_date.strftime('%m/%d/%Y') if r.replacement_ordered_date else '',
        ])
    return response

@login_required
def parts_return_template(request):
    """Download a blank CSV template"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rma_import_template.csv"'
    writer = csv.writer(response)
    writer.writerow(TEMPLATE_HEADERS)
    return response

@login_required
def parts_return_import(request):
    preview_rows = None
    errors = []
    form = PartsReturnImportForm()

    if request.method == 'POST':
        # Check if this is a confirm step (cached data in session)
        if request.POST.get('confirm') == '1':
            cached = request.session.get('import_preview_data')
            if cached:
                rows = cached
                imported = 0
                for row in rows:
                    try:
                        PartsReturn.objects.create(
                            client_name=row.get('Client Name', '').strip() or None,
                            order_no=row.get('Order NO.', '').strip() or None,
                            part_amt=parse_float(row.get('Part Amt', '')),
                            part_name=row.get('Part Name', '').strip() or None,
                            model_no=row.get('Model No.', '').strip() or None,
                            serial_no=row.get('Serial No.', '').strip() or None,
                            rma_no=row.get('RMA No.', '').strip() or None,
                            date_rma_requested=parse_date(row.get('Date RMA Requested', '')),
                            date_part_returned=parse_date(row.get('Date Part Returned', '')),
                            credit_received=parse_date(row.get('Credit Received', '')),
                            rma_credit_received=parse_float(row.get('RMA Credit Received', '')),
                            replacement_ordered_date=parse_date(row.get('Replacement Ordered Date', '')),
                            status='NEW',
                            user=request.user,
                        )
                        imported += 1
                    except Exception as e:
                        errors.append(f'Row error: {str(e)}')
                # Clear session cache
                del request.session['import_preview_data']
                request.session.modified = True
                if imported:
                    messages.success(request, f'{imported} records imported successfully!')
                return redirect('parts_return_list')
            else:
                errors.append('No preview data found. Please upload the file again.')
        else:
            # Upload/preview step
            form = PartsReturnImportForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                try:
                    decoded = csv_file.read().decode('utf-8-sig')
                    reader = csv.DictReader(io.StringIO(decoded))
                    rows = list(reader)
                    if not rows:
                        errors.append('The CSV file is empty.')
                    else:
                        # Store parsed rows in session for confirm step
                        request.session['import_preview_data'] = rows
                        request.session.modified = True
                        preview_rows = rows[:50]
                except Exception as e:
                    errors.append(f'Error reading CSV: {e}')

    return render(request, 'rma/parts_return_import.html', {
        'form': form,
        'preview_rows': preview_rows,
        'headers': TEMPLATE_HEADERS,
        'errors': errors,
    })

def parse_date(val):
    if not val or not val.strip():
        return None
    val = val.strip()
    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y', '%m/%d/%y']:
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None

def parse_float(val):
    if not val or not val.strip():
        return None
    try:
        return float(val.strip().replace('$', '').replace(',', ''))
    except ValueError:
        return None
