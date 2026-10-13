import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Count, Sum
from .models import WarrantyClaim
from .forms import WarrantyClaimForm

@login_required
def index(request):
    if request.user.is_superuser:
        claims = WarrantyClaim.objects.all()
    else:
        claims = WarrantyClaim.objects.filter(user=request.user)
    total = claims.count()
    new_count = claims.filter(status='NEW').count()
    filed_count = claims.filter(status='FILED').count()
    paid_count = claims.filter(status='PAID').count()
    total_amount = claims.aggregate(Sum('claim_amount'))['claim_amount__sum'] or 0
    context = {
        'total_claims': total,
        'new_count': new_count,
        'filed_count': filed_count,
        'paid_count': paid_count,
        'total_amount': total_amount,
    }
    return render(request, 'home/index.html', context)


@login_required
def claim_list(request):
    if request.user.is_superuser:
        claims = WarrantyClaim.objects.all()
    else:
        claims = WarrantyClaim.objects.filter(user=request.user)
    return render(request, 'home/claim_list.html', {'claims': claims})


@login_required
def claim_add(request):
    form = WarrantyClaimForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        claim = form.save(commit=False)
        claim.user = request.user
        claim.save()
        messages.success(request, 'Claim added successfully!')
        return redirect('claim_list')
    return render(request, 'home/claim_form.html', {'form': form, 'title': 'Add Warranty Claim'})


@login_required
def claim_edit(request, pk):
    if request.user.is_superuser:
        claim = get_object_or_404(WarrantyClaim, pk=pk)
    else:
        claim = get_object_or_404(WarrantyClaim, pk=pk, user=request.user)
    form = WarrantyClaimForm(request.POST or None, instance=claim)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Claim updated successfully!')
        return redirect('claim_list')
    return render(request, 'home/claim_form.html', {'form': form, 'title': 'Edit Warranty Claim'})


@login_required
def claim_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete claims.')
        return redirect('claim_list')
    claim = get_object_or_404(WarrantyClaim, pk=pk)
    claim.delete()
    messages.success(request, 'Claim deleted.')
    return redirect('claim_list')


@login_required
def claim_export(request):
    if request.user.is_superuser:
        claims = WarrantyClaim.objects.all()
    else:
        claims = WarrantyClaim.objects.filter(user=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="warranty_claims.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Job #', 'Tech', 'Customer', 'Client Address', 'Equipment Brand',
                     'Unit Model', 'Unit Serial', 'Warranty Type', 'Location',
                     'Part Type', 'Compressor?', 'Diagnosis', 'Date', 'Amount', 'Status',
                     'Vendor', 'Submission Method', 'Confirmation #', 'Submitted Date',
                     'ST Job ID', 'ST Form ID', 'ST Submission ID', 'Notes', 'User'])
    for c in claims:
        writer.writerow([c.id, c.job_number, c.tech_name, c.customer_name, c.client_address,
                         c.equipment_brand, c.unit_model, c.unit_serial, c.warranty_type,
                         c.equipment_location, c.part_type, c.is_compressor, c.diagnosis,
                         c.claim_date, c.claim_amount, c.get_status_display(), c.vendor,
                         c.vendor_submission_method, c.vendor_confirmation_number,
                         c.vendor_submitted_date, c.servicetitan_job_id,
                         c.servicetitan_form_id, c.servicetitan_submission_id,
                         c.notes, c.user.username])
    return response


@login_required
def claim_sync_servicetitan(request):
    if request.method != 'POST':
        messages.error(request, 'Use the Sync button to trigger a sync.')
        return redirect('claim_list')
    try:
        from .integrations.servicetitan import sync_form_submissions
    except ImportError as e:
        messages.error(request, f'Integration module not found: {e}')
        return redirect('claim_list')
    try:
        result = sync_form_submissions(request.user)
    except Exception as e:
        messages.error(request, f'Sync failed: {e}')
        return redirect('claim_list')
    if result['errors']:
        for err in result['errors']:
            messages.warning(request, f'Sync warning: {err}')
    if result['created']:
        messages.success(request, f'{result["created"]} new claim(s) imported from ServiceTitan.')
    if result['skipped']:
        messages.info(request, f'{result["skipped"]} submission(s) skipped.')
    if not result['created'] and not result['skipped']:
        messages.info(request, 'No new submissions found in ServiceTitan.')
    return redirect('claim_list')
