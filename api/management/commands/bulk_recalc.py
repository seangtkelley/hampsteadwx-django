from django.core.management.base import BaseCommand
from api.models import MonthlySummary, AnnualSummary
from api import utils

class Command(BaseCommand):
    help = 'Recalculate summaries. Helpful if changes/additions are made to calculation code.'

    def add_arguments(self, parser):
        parser.add_argument("-m", "--months", type=int, nargs='*', help="Months to recalculate.")
        parser.add_argument("-y", "--years", type=int, nargs='*', help="Years to recalculate. Assumes only annual summaries if --months not present.")

        parser.add_argument('--all', action='store_true', help='Recalculate all summaries')

    def handle(self, *args, **options):
        monthly_summaries, annual_summaries = [], []

        if options['all']:
            monthly_summaries = MonthlySummary.objects.all()
            annual_summaries = AnnualSummary.objects.all()

        elif 'months' in options:
            if 'years' not in options:
                monthly_summaries = MonthlySummary.objects.filter(date__month__in=options['months'])
                annual_summaries = AnnualSummary.objects.all()
            else:
                monthly_summaries = MonthlySummary.objects.filter(date__year__in=options['years'], date__month__in=options['months'])
                annual_summaries = AnnualSummary.objects.filter(year__in=options['years'])
        
        elif 'years' in options:
            annual_summaries = AnnualSummary.objects.filter(year__in=options['years'])


        # loop thru and recalc each
        for summary in monthly_summaries:
            utils.calc_monthly_summary(summary.date.year, summary.date.year, save_to_db=True)

        # loop thru and recalc each
        for summary in annual_summaries:
            utils.calc_annual_summary(summary.year, save_to_db=True)