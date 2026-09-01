"""Django views for public pages and climate summary endpoints."""

import os
from pathlib import Path
from typing import cast

from django.core.files.uploadedfile import UploadedFile
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render

from boilerplate.settings import BASE_DIR

from . import forms, models, utils


def handler404(request: HttpRequest, *_args: object, **_argv: object) -> HttpResponse:
    """Render the custom 404 page.

    Returns:
        Rendered 404 response.
    """
    return render(request, "404.html", status=404)


def handler500(request: HttpRequest, *_args: object, **_argv: object) -> HttpResponse:
    """Render the custom 500 page.

    Returns:
        Rendered 500 response.
    """
    return render(request, "500.html", status=500)


def index(request: HttpRequest) -> HttpResponse:
    """Render the home page.

    Returns:
        Rendered home page response.
    """
    return render(request, "index.html", {"title": "Home"})


def info_view(request: HttpRequest) -> HttpResponse:
    """Render the site information page.

    Returns:
        Rendered info page response.
    """
    return render(request, "info.html", {"title": "Info"})


def normals_view(request: HttpRequest) -> HttpResponse:
    """Render the climate normals page.

    Returns:
        Rendered normals page response.
    """
    return render(request, "normals.html", {"title": "Normals"})


def summaries_monthly_submit(request: HttpRequest) -> HttpResponse:
    """Accept a monthly CSV upload and recalculate summaries.

    Returns:
        Rendered submission page with success or error alerts.
    """
    payload: dict[str, object] = {"title": "Submit Monthly Summary"}

    if request.method == "POST":
        # calc monthly summary
        form = forms.SubmitMonthlyCSV(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data["password"] == os.environ.get("SITE_PASS"):
                # move csv file
                file_obj = cast(UploadedFile, request.FILES["csv_file"])
                filepath = BASE_DIR / "static" / "csv" / str(file_obj.name)
                with Path(filepath).open("wb+") as dest:
                    for chunk in file_obj.chunks():
                        dest.write(chunk)

                # process csv
                try:
                    year, month = utils.process_csv(filepath)
                except Exception as e:
                    payload = utils.add_alert(
                        payload,
                        "danger",
                        f"Error occurred while processing csv: <code>{e!s}</code>",
                    )
                    return render(request, "summaries/monthly/submit.html", payload)

                # calculate and save summaries
                try:
                    utils.calc_monthly_summary(year, month, save_to_db=True)
                    utils.calc_annual_summary(year, save_to_db=True)
                except Exception as e:
                    payload = utils.add_alert(
                        payload,
                        "danger",
                        f"Error occurred while calculating summary: <code>{e!s}</code>",
                    )
                    return render(request, "summaries/monthly/submit.html", payload)

                # prompt redirect
                payload = utils.add_alert(
                    payload,
                    "success",
                    f"{utils.get_month_name(month)} {year} monthly data successfully processed. <a href='/summaries/monthly/{year}/{month}'>View summary <i class='fa fa-external-link'></i></a>",
                )

            else:
                payload = utils.add_alert(payload, "danger", "Incorrect password")

        else:
            payload = utils.add_alert(payload, "danger", "Form data invalid.")

    return render(request, "summaries/monthly/submit.html", payload)


def summaries_monthly_home(request: HttpRequest) -> HttpResponse:
    """Render the monthly summary landing page.

    Returns:
        Rendered monthly summary landing page response.
    """
    return render(
        request, "summaries/monthly/view.html", {"title": "View Monthly Summary"}
    )


def summaries_monthly_view(request: HttpRequest, year: int, month: int) -> HttpResponse:
    """Render or update a monthly summary page.

    Returns:
        Rendered monthly summary page response.
    """
    payload: dict[str, object] = {
        "title": f"{utils.get_month_name(month)} {year} Monthly Summary"
    }

    if request.method == "POST":
        # edit remarks
        form = forms.EditRemarks(request.POST)
        if form.is_valid():
            if form.cleaned_data["password"] == os.environ.get("SITE_PASS"):
                # find summary
                summary = models.MonthlySummary.objects.filter(
                    date__year=year, date__month=month
                ).first()
                if summary is not None:
                    # edit remarks
                    summary.remarks = cast(str, form.cleaned_data["remarks"])
                    summary.save()
                    # display alert
                    payload = utils.add_alert(
                        payload,
                        "success",
                        f"{utils.get_month_name(month)} {year} remarks saved.",
                    )
                else:
                    payload = utils.add_alert(
                        payload,
                        "danger",
                        f"{utils.get_month_name(month)} {year} Summary not found.",
                    )

            else:
                payload = utils.add_alert(payload, "danger", "Incorrect password")

        else:
            payload = utils.add_alert(payload, "danger", "Form data invalid.")

    # get monthly summary
    if models.MonthlySummary.objects.filter(
        date__year=year, date__month=month
    ).exists():
        payload["monthly_summary"] = models.MonthlySummary.objects.filter(
            date__year=year, date__month=month
        ).first()
    else:
        payload = utils.add_alert(
            payload,
            "warning",
            f"{utils.get_month_name(month)} {year} Summary not found.",
        )

    # get daily obs
    payload["daily_obs"] = models.DailyOb.objects.filter(
        date__year=year, date__month=month
    ).order_by("date")

    return render(request, "summaries/monthly/view.html", payload)


def summaries_monthly_text(request: HttpRequest, year: int, month: int) -> HttpResponse:
    """Render the plain-text monthly summary.

    Returns:
        Rendered text summary response.

    Raises:
        Http404: If the monthly summary does not exist.
    """
    payload: dict[str, object] = {
        "title": f"{utils.get_month_name(month)} {year} Monthly Summary"
    }

    # get monthly summary
    if models.MonthlySummary.objects.filter(
        date__year=year, date__month=month
    ).exists():
        # from database
        payload["monthly_summary"] = models.MonthlySummary.objects.filter(
            date__year=year, date__month=month
        ).first()
    else:
        # summary not found
        raise Http404

    # get normals
    normals = utils.get_normals(year)
    payload["AVG_TEMP"] = normals["temp"][month - 1]
    payload["AVG_PRECIP"] = normals["precip"][month - 1]
    payload["AVG_SNFL"] = normals["sf"][month - 1]

    return render(request, "summaries/monthly/text.html", payload)


def summaries_monthly_csv(_request: HttpRequest, year: int, month: int) -> HttpResponse:
    """Download the source CSV for a monthly summary.

    Returns:
        CSV file download response.

    Raises:
        Http404: If the summary or source CSV cannot be found.
    """
    # get summary
    if models.MonthlySummary.objects.filter(
        date__year=year, date__month=month
    ).exists():
        # from database
        summary = models.MonthlySummary.objects.filter(
            date__year=year, date__month=month
        ).first()
    else:
        # calc
        summary = utils.calc_monthly_summary(year, month)

    # Determine CSV path whether `summary` is a model instance or a dict
    csv_path: str | None = None
    if summary is None:
        csv_path = None
    elif isinstance(summary, dict):
        csv_path = cast(
            str | None, cast(dict[str, object], summary).get("csv_filepath")
        )
    else:
        csv_path = getattr(summary, "csv_filepath", None)

    if csv_path and Path(csv_path).exists():
        # read csv and build response
        with Path(csv_path).open("r") as fh:
            response = HttpResponse(fh.read(), content_type="text/csv")
            response["Content-Disposition"] = (
                f"attachment; filename={csv_path.split('/')[-1]}"
            )
            return response

    # csv not found
    raise Http404


def summaries_annual_home(request: HttpRequest) -> HttpResponse:
    """Render the annual summary landing page.

    Returns:
        Rendered annual summary landing page response.
    """
    return render(
        request, "summaries/annual/view.html", {"title": "View Annual Summary"}
    )


def summaries_annual_view(request: HttpRequest, year: int) -> HttpResponse:
    """Render an annual summary page.

    Returns:
        Rendered annual summary page response.
    """
    payload: dict[str, object] = {"title": f"{year} Annual Summary"}

    # get annual summary
    if models.AnnualSummary.objects.filter(year=year).exists():
        payload["annual_summary"] = models.AnnualSummary.objects.filter(
            year=year
        ).first()

        # get monthly summaries
        payload["monthly_summaries"] = models.MonthlySummary.objects.filter(
            date__year=year
        ).order_by("date")
    else:
        payload = utils.add_alert(payload, "warning", f"{year} Summary not found.")

    return render(request, "summaries/annual/view.html", payload)


def summaries_annual_text(request: HttpRequest, year: int) -> HttpResponse:
    """Render the plain-text annual summary.

    Returns:
        Rendered text summary response.

    Raises:
        Http404: If the annual summary does not exist.
    """
    payload: dict[str, object] = {"title": f"{year} Annual Summary"}

    # get annual summary
    if models.AnnualSummary.objects.filter(year=year).exists():
        payload["annual_summary"] = models.AnnualSummary.objects.filter(
            year=year
        ).first()
    else:
        raise Http404

    # get normals
    normals = utils.get_normals(year)
    payload["AVG_TEMP"] = normals["temp"][12]
    payload["AVG_PRECIP"] = normals["precip"][12]
    payload["AVG_SNFL"] = normals["sf"][12]

    return render(request, "summaries/annual/text.html", payload)


def summaries_annual_table(request: HttpRequest, year: int) -> HttpResponse:
    """Render the annual summary comparison table.

    Returns:
        Rendered annual comparison table response.

    Raises:
        Http404: If the annual summary does not exist.
    """
    payload: dict[str, object] = {"title": f"{year} Annual Summary"}

    # get annual summary
    if models.AnnualSummary.objects.filter(year=year).exists():
        # get monthly summaries
        all_summaries: list[object] = list(
            models.MonthlySummary.objects.filter(date__year=year).order_by("date")
        )

        # get annual
        all_summaries.append(models.AnnualSummary.objects.filter(year=year).first())
        payload["all_summaries"] = all_summaries
    else:
        raise Http404

    return render(request, "summaries/annual/table.html", payload)


def summaries_snowseason_view(request: HttpRequest) -> HttpResponse:
    """Render the snow season overview page.

    Returns:
        Rendered snow season overview response.
    """
    payload: dict[str, object] = {"title": "Snow Season"}

    # get snow seasons
    payload["summaries"] = models.SnowSeason.objects.all().order_by("season")

    return render(request, "summaries/snowseason/view.html", payload)


def summaries_snowseason_season(request: HttpRequest, season: str) -> HttpResponse:
    """Render a single snow season detail page.

    Returns:
        Rendered snow season detail response.
    """
    payload: dict[str, object] = {"title": f"{season} Snow Season"}

    # get snow season
    payload["summary"] = models.SnowSeason.objects.filter(season=season).first()

    # loop help
    payload["month_names"] = [
        "October",
        "November",
        "December",
        "January",
        "February",
        "March",
        "April",
        "May",
    ]
    payload["month_abbrs"] = ["oct", "nov", "dec", "jan", "feb", "mar", "apr", "may"]

    return render(request, "summaries/snowseason/season.html", payload)


def summaries_peakfoliage_view(request: HttpRequest) -> HttpResponse:
    """Render the peak foliage dates page.

    Returns:
        Rendered peak foliage page response.
    """
    payload: dict[str, object] = {"title": "Peak Foliage"}

    # get peak foliage dates
    payload["peaks"] = models.PeakFoliage.objects.all().order_by("date")

    return render(request, "summaries/peakfoliage/view.html", payload)


def summaries_sunsetlake_view(request: HttpRequest) -> HttpResponse:
    """Render the Sunset Lake ice-in/ice-out page.

    Returns:
        Rendered Sunset Lake summary response.
    """
    payload: dict[str, object] = {"title": "Sunset Lake Ice In/Ice Out"}

    # get sunset lake summaries
    payload["summaries"] = models.SunsetLakeIceInIceOut.objects.all().order_by("season")

    return render(request, "summaries/sunsetlake/view.html", payload)


def summaries_precip_view(request: HttpRequest) -> HttpResponse:
    """Render the precipitation summary page.

    Returns:
        Rendered precipitation summary response.
    """
    payload: dict[str, object] = {"title": "Precipitation"}

    # get monthly summaries
    payload["summaries"] = models.MonthlySummary.objects.all().order_by("date")

    return render(request, "summaries/precip/view.html", payload)
