"""Management command to bulk-recalculate monthly and annual summaries."""

from argparse import ArgumentParser
from collections.abc import Sequence
from typing import cast

from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from api import utils
from api.models import AnnualSummary, MonthlySummary


class Command(BaseCommand):
    """Recalculate stored summaries after calculation logic changes."""

    help = "Recalculate summaries. Helpful if changes/additions are made to calculation code."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register command-line arguments."""
        parser.add_argument(
            "-m", "--months", type=int, nargs="*", help="Months to recalculate."
        )
        parser.add_argument(
            "-y",
            "--years",
            type=int,
            nargs="*",
            help="Years to recalculate. Assumes only annual summaries if --months not present.",
        )

        parser.add_argument(
            "--all", action="store_true", help="Recalculate all summaries"
        )

    def handle(self, *_args: object, **options: dict[str, object]) -> None:
        """Run recalculation for the selected summaries.

        Raises:
            CommandError: If no valid year or month selection is provided.
        """
        monthly_summaries, annual_summaries = [], []

        if options["all"]:
            if options["months"] is not None and options["years"] is None:
                self.stdout.write("Recalculating all monthly summaries...")
                monthly_summaries = MonthlySummary.objects.all()
            elif options["years"] is not None and options["months"] is None:
                self.stdout.write("Recalculating all annual summaries...")
                annual_summaries = AnnualSummary.objects.all()
            else:
                self.stdout.write("Recalculating all summaries...")
                monthly_summaries = MonthlySummary.objects.all()
                annual_summaries = AnnualSummary.objects.all()

        elif (
            options["months"] is not None
            and len(cast(Sequence[int], options["months"])) > 0
        ):
            if (
                options["years"] is not None
                and len(cast(Sequence[int], options["years"])) > 0
            ):
                self.stdout.write(
                    "Recalculating monthly summaries for months: "
                    f"{options['months']} and years: {options['years']}..."
                )
                monthly_summaries = MonthlySummary.objects.filter(
                    date__year__in=cast(Sequence[int], options["years"]),
                    date__month__in=cast(Sequence[int], options["months"]),
                )
            else:
                self.stdout.write(
                    "Recalculating monthly summaries for months: "
                    f"{options['months']} and years: all..."
                )
                monthly_summaries = MonthlySummary.objects.filter(
                    date__month__in=cast(Sequence[int], options["months"])
                )

        elif (
            options["years"] is not None
            and len(cast(Sequence[int], options["years"])) > 0
        ):
            self.stdout.write(
                f"Recalculating annual summaries for years: {options['years']}..."
            )
            annual_summaries = AnnualSummary.objects.filter(
                year__in=cast(Sequence[int], options["years"])
            )

        else:
            raise CommandError("Missing or malformed arguments.")

        for summary in tqdm(monthly_summaries):
            utils.calc_monthly_summary(
                summary.date.year, summary.date.month, save_to_db=True
            )

        for summary in tqdm(annual_summaries):
            utils.calc_annual_summary(summary.year, save_to_db=True)
