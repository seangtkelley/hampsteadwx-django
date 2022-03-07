from django.core.management.base import BaseCommand
from api.models import MonthlySummary, AnnualSummary
from api import utils

class Command(BaseCommand):
    help = 'Recalculate all summaries. Helpful if changes/additions are made to calculation code.'

    def handle(self, *args, **options):
        # get all monthly summaries
        all_monthly_summaries = MonthlySummary.objects.all()

        # loop thru and recalc each
        for summary in all_monthly_summaries:
            utils.calc_monthly_summary(summary.date.year, summary.date.year, save_to_db=True)

        # get all annual summaries
        all_annual_summaries = AnnualSummary.objects.all()

        # loop thru and recalc each
        for summary in all_annual_summaries:
            utils.calc_annual_summary(summary.year, save_to_db=True)