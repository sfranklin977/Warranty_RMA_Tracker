from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.home.integrations.servicetitan import sync_form_submissions


class Command(BaseCommand):
    help = "Sync warranty claims from ServiceTitan"

    def handle(self, *args, **options):
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            self.stderr.write("No superuser found — aborting")
            return

        result = sync_form_submissions(user)

        for err in result.get("errors", []):
            self.stderr.write(f"ERROR: {err}")

        created = result.get("created", 0)
        skipped = result.get("skipped", 0)
        error_count = len(result.get("errors", []))
        self.stdout.write(f"Synced: {created} created, {skipped} skipped, {error_count} errors")
