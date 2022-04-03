from django.core.management.base import BaseCommand
from api.models import MonthlySummary, AnnualSummary
from api import utils

class Command(BaseCommand):
    help = 'Recalculate summaries. Helpful if changes/additions are made to calculation code.'

    def add_arguments(self, parser):
        parser.add_argument("-m", "--month", type=int, nargs='+', help="Month to recalculate. Requires --year arg.")
        parser.add_argument("-y", "--year", type=int, nargs='+', help="Year to recalculate. Assumes annual summary if month not present.")

        parser.add_argument('--all', action='store_true', help='Recalculate all summaries')

    def handle(self, *args, **options):

        if options['all']:
            # get all monthly summaries
            monthly_summaries = MonthlySummary.objects.all()

            # get all annual summaries
            annual_summaries = AnnualSummary.objects.all()

        elif 'month' in options:
            if 'year' not in options:
                pass

            monthly_summaries = MonthlySummary.objects.filter()
            annual_summaries = AnnualSummary.objects.filter()
        
        elif 'year' in options:

            annual_summaries = AnnualSummary.objects.filter()


        # loop thru and recalc each
        for summary in monthly_summaries:
            utils.calc_monthly_summary(summary.date.year, summary.date.year, save_to_db=True)

        # loop thru and recalc each
        for summary in annual_summaries:
            utils.calc_annual_summary(summary.year, save_to_db=True)