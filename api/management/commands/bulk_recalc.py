import logging
from django.core.management.base import BaseCommand, CommandError
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
            if options['months'] is not None and options['years'] is None:
                logging.info("Recalculating all monthly summaries...")
                monthly_summaries = MonthlySummary.objects.all()
            elif options['years'] is not None and options['months'] is None:
                logging.info("Recalculating all annual summaries...")
                annual_summaries = AnnualSummary.objects.all()
            else:
                logging.info("Recalculating all summaries...")
                monthly_summaries = MonthlySummary.objects.all()
                annual_summaries = AnnualSummary.objects.all()

        elif options['months'] is not None and len(options['months']) > 0:
            if options['years'] is not None and len(options['years']) > 0:
                logging.info(f"Recalculating monthly summaries for months: {','.join(options['months'])} and years: {','.join(options['years'])}...")
                monthly_summaries = MonthlySummary.objects.filter(date__year__in=options['years'], date__month__in=options['months'])
            else:
                logging.info(f"Recalculating monthly summaries for months: {','.join(options['months'])} and years: all...")
                monthly_summaries = MonthlySummary.objects.filter(date__month__in=options['months'])
        
        elif options['years'] is not None and len(options['years']) > 0:
            logging.info(f"Recalculating annual summaries for years: {','.join(options['years'])}...")
            annual_summaries = AnnualSummary.objects.filter(year__in=options['years'])

        else:
            raise CommandError("Missing or malformed arguments.")


        # loop thru and recalc each
        for summary in monthly_summaries:
            logging.info(f"Recalculating {summary.date.month}/{summary.date.year} monthly summary...")
            utils.calc_monthly_summary(summary.date.year, summary.date.month, save_to_db=True)

        # loop thru and recalc each
        for summary in annual_summaries:
            logging.info(f"Recalculating {summary.year} annual summary...")
            utils.calc_annual_summary(summary.year, save_to_db=True)