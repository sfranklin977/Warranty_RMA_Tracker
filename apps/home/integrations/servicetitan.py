
import requests
import logging
from datetime import datetime
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

FORM_FIELD_MAP = {
    "Technician Name": "tech_name",
    "Client Name": "customer_name",
    "Client Address": "client_address",
    "Brand of Equipment": "equipment_brand",
    "Unit Model #": "unit_model",
    "Unit Serial #": "unit_serial",
    "Type of Warranty": "warranty_type",
    "Location": "equipment_location",
    "Type of Part": "part_type",
    "Diagnosis": "diagnosis",
}

WARRANTY_FORM_NAMES = ["Warranty Return Form", "Install Warranty Return Form"]

_token_cache = {"token": None, "expires_at": None}
_job_cache = {}


def _get_access_token():
    now = timezone.now()
    if _token_cache["token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.SERVICETITAN_CLIENT_ID,
        "client_secret": settings.SERVICETITAN_CLIENT_SECRET,
    }

    resp = requests.post(
        settings.SERVICETITAN_AUTH_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = now + timezone.timedelta(seconds=data["expires_in"] - 60)
    return _token_cache["token"]


def _st_headers():
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "ST-App-Key": settings.SERVICETITAN_APP_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _st_get(url_suffix, params=None, timeout=20):
    url = f'{settings.SERVICETITAN_BASE_URL.rstrip("/")}{url_suffix}'
    resp = requests.get(url, headers=_st_headers(), params=params or {}, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_form_submissions():
    tenant = settings.SERVICETITAN_TENANT_ID
    params = {"pageSize": 100}
    results = []
    page = 1
    max_pages = 20
    cutoff = datetime(2026, 1, 1)

    while page <= max_pages:
        params["page"] = page
        data = _st_get(f"/forms/v2/tenant/{tenant}/submissions", params=params, timeout=20)

        for item in data.get("data", []):
            if item.get("formName") not in WARRANTY_FORM_NAMES:
                continue

            submitted = item.get("submittedOn") or item.get("createdOn") or ""
            if submitted:
                try:
                    sub_date = datetime.strptime(submitted[:10], "%Y-%m-%d")
                    if sub_date < cutoff:
                        continue
                except Exception:
                    pass

            results.append(item)

        if not data.get("hasMore"):
            break
        page += 1

    logger.info("Fetched %d warranty submissions (2026+ only)", len(results))
    return results


def get_job_details(job_id):
    if not job_id:
        return None
    if job_id in _job_cache:
        return _job_cache[job_id]

    tenant = settings.SERVICETITAN_TENANT_ID
    try:
        job = _st_get(f"/jpm/v2/tenant/{tenant}/jobs/{job_id}", timeout=10)
        _job_cache[job_id] = job
        return job
    except Exception as e:
        logger.warning("Job %s fetch failed: %s", job_id, e)
        _job_cache[job_id] = None
        return None


def parse_submission_to_claim(submission):
    form_name = submission.get("formName", "")
    if form_name not in WARRANTY_FORM_NAMES:
        return None

    claim_data = {}

    for u in submission.get("units", []):
        name = (u.get("name") or "").strip()
        model_field = FORM_FIELD_MAP.get(name)
        value = u.get("value")
        if model_field and value:
            claim_data[model_field] = str(value).strip()

    job_id = None
    for owner in submission.get("owners", []):
        if owner.get("type") == "Job":
            job_id = owner.get("id")
            break

    claim_data["servicetitan_job_id"] = str(job_id) if job_id else ""

    if job_id:
        job = get_job_details(job_id)
        if job:
            claim_data["job_number"] = job.get("jobNumber", "") or f"ST-{job_id}"
        else:
            claim_data["job_number"] = f"ST-{job_id}"

    claim_data["servicetitan_form_id"] = str(submission.get("formId", "")).strip()
    claim_data["servicetitan_submission_id"] = str(submission.get("id", "")).strip()

    created_str = submission.get("submittedOn") or submission.get("createdOn")
    if created_str:
        try:
            claim_data["claim_date"] = datetime.strptime(created_str[:10], "%Y-%m-%d").date()
        except Exception:
            pass

    return claim_data


def sync_form_submissions(request_user):
    from apps.home.models import WarrantyClaim

    result = {"created": 0, "skipped": 0, "errors": []}

    try:
        submissions = get_form_submissions()
    except Exception as e:
        result["errors"].append(f"API error: {e}")
        return result

    existing_ids = set(
        str(x) for x in WarrantyClaim.objects
        .filter(servicetitan_submission_id__isnull=False)
        .exclude(servicetitan_submission_id="")
        .values_list("servicetitan_submission_id", flat=True)
    )

    seen_ids = set()
    to_create = []

    for sub in submissions:
        try:
            sid = str(sub.get("id", "")).strip()
            if not sid:
                result["skipped"] += 1
                continue

            if sid in existing_ids or sid in seen_ids:
                result["skipped"] += 1
                continue

            claim_data = parse_submission_to_claim(sub)
            if claim_data is None:
                result["skipped"] += 1
                continue

            claim_data["servicetitan_submission_id"] = sid

            claim = WarrantyClaim(**claim_data)
            claim.user = request_user
            claim.status = "NEW"
            claim.servicetitan_synced_at = timezone.now()

            to_create.append(claim)
            seen_ids.add(sid)
            result["created"] += 1

        except Exception as e:
            result["errors"].append(f'Submission {sub.get("id", "?")}: {e}')

    if to_create:
        WarrantyClaim.objects.bulk_create(to_create, batch_size=100, ignore_conflicts=True)

    return result
