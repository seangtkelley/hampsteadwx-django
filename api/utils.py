"""Utilities for loading normals, processing CSVs, and calculating summaries.

Trace observations in CSV files are stored using ``TRACE_VAL`` (0.001) when the
source value is ``T``.
"""

from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal, getcontext
from pathlib import Path
from typing import Any, cast

import pandas as pd
from django.db.models import Sum

from boilerplate.settings import BASE_DIR, TRACE_VAL

from . import models


def get_month_name(num: int) -> str:
    """Return the full month name for a month number."""
    return date(1900, num, 1).strftime("%B")


def get_month_abbr(num: int) -> str:
    """Return the lowercase three-letter month abbreviation."""
    return date(1900, num, 1).strftime("%b").lower()


def create_alert(color: str, body: str) -> dict[str, str]:
    """Build a Bootstrap-style alert payload.

    Returns:
        Alert dictionary with color and body keys.
    """
    return {"color": color, "body": body}


def add_alert(
    payload: Mapping[str, object], color: str, body: str
) -> dict[str, object]:
    """Append an alert to a view payload.

    Returns:
        Updated payload containing the new alert.
    """
    alert = create_alert(color, body)
    new_payload: dict[str, object] = dict(payload)
    alerts_raw: object = new_payload.get("alerts", [])
    alerts = list(cast(Iterable[Any], alerts_raw))
    alerts.append(alert)
    new_payload["alerts"] = alerts
    return new_payload


def empty_snowseason(season: str) -> dict[str, object]:
    """Return zeroed snowfall totals for a new snow season.

    Returns:
        Snow season defaults keyed by month abbreviation.
    """
    return {
        "season": season,
        "oct": 0,
        "nov": 0,
        "dec": 0,
        "jan": 0,
        "feb": 0,
        "mar": 0,
        "apr": 0,
        "may": 0,
        "total": 0,
    }


def get_normals(year: int) -> dict[str, list[Decimal]]:
    """Load monthly and annual climate normals for the given year.

    Uses the 1991-2020 normals CSV when ``year >= 2022``; otherwise falls back to
    the legacy HMPN3 normals file. An optional ``month`` parameter and a
    mid-2020 cutoff were previously considered but are no longer used.

    Returns:
        Climate normals keyed by measurement type.
    """
    normals: dict[str, list[Decimal]] = {}
    # Ensure Decimal arithmetic precision is reasonable for averages
    getcontext().prec = 9
    if year >= 2022:
        filepath = (
            BASE_DIR
            / "static"
            / "csv"
            / "normals-monthly-1991-2020-2022-01-23T16-24-36.csv"
        )

        def decimal_converter(x: str) -> Decimal:
            return Decimal(x)

        df = pd.read_csv(
            filepath,
            converters={
                "MLY-TAVG-NORMAL": decimal_converter,
                "MLY-PRCP-NORMAL": decimal_converter,
                "MLY-SNOW-NORMAL": decimal_converter,
            },
        )
        normals["temp"] = list(df["MLY-TAVG-NORMAL"])
        normals["precip"] = list(df["MLY-PRCP-NORMAL"])
        normals["sf"] = list(df["MLY-SNOW-NORMAL"])

        # Annual norms: temp is mean of months; precip/snow are yearly totals
        # (matches HMPN3 convention used for years < 2022).
        if len(normals["temp"]) > 0:
            normals["temp"].append(sum(normals["temp"]) / Decimal(len(normals["temp"])))
        if len(normals["precip"]) > 0:
            normals["precip"].append(sum(normals["precip"]))
        if len(normals["sf"]) > 0:
            normals["sf"].append(sum(normals["sf"]))
    else:
        filepath = BASE_DIR / "static" / "csv" / "HMPN3-Monthly-Climate-Normals.csv"
        with Path(filepath).open() as f:
            lines = f.readlines()
            normals["temp"] = list(map(Decimal, lines[0].split(",")))
            normals["precip"] = list(map(Decimal, lines[1].split(",")))
            normals["sf"] = list(map(Decimal, lines[2].split(",")))

    return normals


def process_csv(filepath: str | Path) -> tuple[int, int]:
    """Parse a daily observation CSV and upsert daily observation records.

    Returns:
        Year and month parsed from the uploaded CSV.
    """
    # load file
    df = pd.read_csv(filepath, parse_dates=["DATE"])

    # save daily obs
    for _, row in df.iterrows():
        # check if ob exists
        if models.DailyOb.objects.filter(date=row["DATE"].date()).exists():
            ob = cast(
                models.DailyOb,
                models.DailyOb.objects.filter(date=row["DATE"].date()).first(),
            )
            ob.csv_filepath = str(filepath)
            ob.max_temp = Decimal(row["TX"])
            ob.min_temp = Decimal(row["TN"])
            ob.atob_temp = Decimal(row["TA"])

            # 0.001 for trace values
            ob.precip = Decimal(TRACE_VAL) if row["PP"] == "T" else Decimal(row["PP"])
            ob.snowfall = Decimal(TRACE_VAL) if row["SF"] == "T" else Decimal(row["SF"])
            ob.snowdepth = (
                Decimal(TRACE_VAL) if row["SD"] == "T" else Decimal(row["SD"])
            )

            ob.save()
        else:
            ob = models.DailyOb(
                date=row["DATE"].date(),
                csv_filepath=str(filepath),
                max_temp=Decimal(row["TX"]),
                min_temp=Decimal(row["TN"]),
                atob_temp=Decimal(row["TA"]),
                # 0.001 for trace values
                precip=Decimal(TRACE_VAL) if row["PP"] == "T" else Decimal(row["PP"]),
                snowfall=Decimal(TRACE_VAL) if row["SF"] == "T" else Decimal(row["SF"]),
                snowdepth=Decimal(TRACE_VAL)
                if row["SD"] == "T"
                else Decimal(row["SD"]),
            )

            ob.save()

    return df.iloc[0]["DATE"].year, df.iloc[0]["DATE"].month


def calc_monthly_summary(year: int, month: int, save_to_db: bool = False) -> object:
    """Calculate a monthly summary from stored daily observations.

    Returns:
        Summary dictionary, database write result, or None when no data exists.
    """
    # get all daily obs from month
    obs = models.DailyOb.objects.filter(date__year=year, date__month=month).order_by(
        "date"
    )
    if obs.count() == 0:
        return None

    # convert to dataframe
    df = pd.DataFrame.from_records(obs.values())
    df[["max_temp", "min_temp", "atob_temp", "precip", "snowfall", "snowdepth"]] = df[
        ["max_temp", "min_temp", "atob_temp", "precip", "snowfall", "snowdepth"]
    ].apply(pd.to_numeric)

    # calc general
    summary = calc_general_summary(df)

    # add meta
    summary["date"] = df.iloc[0].date
    summary["csv_filepath"] = df.iloc[0].csv_filepath

    # add month specific fields
    normals = get_normals(year)
    norm_temp = Decimal(str(normals["temp"][month - 1]))
    norm_precip = Decimal(str(normals["precip"][month - 1]))
    norm_sf = Decimal(str(normals["sf"][month - 1]))
    summary["avg_temp_dfn"] = Decimal(str(summary["avg_temp"])) - norm_temp
    summary["precip_dfn"] = Decimal(str(summary["precip"])) - norm_precip
    summary["sf_dfn"] = Decimal(str(summary["sf"])) - norm_sf

    # precip to date
    precip_todate = (
        models.DailyOb.objects.filter(
            date__year=year, date__month__in=list(range(1, month + 1))
        )
        .exclude(precip=TRACE_VAL)
        .aggregate(Sum("precip"))["precip__sum"]
    )  # sum over all precip except traces
    summary["precip_todate"] = precip_todate
    summary["precip_todate_dfn"] = precip_todate - sum(normals["precip"][:month])

    # snowfall to date
    if month >= 10:
        summary["sf_todate"] = (
            models.DailyOb.objects.filter(
                date__year=year, date__month__in=list(range(10, month + 1))
            )
            .exclude(snowfall=TRACE_VAL)
            .aggregate(Sum("snowfall"))["snowfall__sum"]
        )  # same as above

        summary["sf_todate_dfn"] = summary["sf_todate"] - sum(normals["sf"][9:month])

    elif month <= 5:
        # get last year's snow
        prev_year_sf = (
            models.DailyOb.objects.filter(
                date__year=year - 1, date__month__in=[10, 11, 12]
            )
            .exclude(snowfall=TRACE_VAL)
            .aggregate(Sum("snowfall"))["snowfall__sum"]
        )
        summary["sf_todate"] = (
            prev_year_sf if prev_year_sf else 0
        )  # small check if we don't have prev year snowfall

        # get this year's snow
        summary["sf_todate"] += (
            models.DailyOb.objects.filter(
                date__year=year, date__month__in=list(range(1, month + 1))
            )
            .exclude(snowfall=TRACE_VAL)
            .aggregate(Sum("snowfall"))["snowfall__sum"]
        )

        summary["sf_todate_dfn"] = (
            summary["sf_todate"] - sum(normals["sf"][9:12]) - sum(normals["sf"][:month])
        )
    else:
        summary["sf_todate"] = 0
        summary["sf_todate_dfn"] = 0

    if save_to_db:
        if models.MonthlySummary.objects.filter(date=summary["date"]).exists():
            db_summary = models.MonthlySummary.objects.filter(
                date=summary["date"]
            ).update(**summary)
        else:
            db_summary = models.MonthlySummary.objects.create(**summary)

        # save snow season information
        if month in [10, 11, 12, 1, 2, 3, 4, 5]:
            if month in [10, 11, 12]:
                season_str = f"{year}-{year + 1}"
            elif month in [1, 2, 3, 4, 5]:
                season_str = f"{year - 1}-{year}"

            snowseason, _ = models.SnowSeason.objects.get_or_create(
                season=season_str, defaults=empty_snowseason(season_str)
            )

            setattr(snowseason, get_month_abbr(month), summary["sf"])
            snowseason.total = snowseason.total + summary["sf"]
            snowseason.save()

        return db_summary
    return summary


def calc_annual_summary(year: int, save_to_db: bool = False) -> object:
    """Calculate an annual summary from stored daily observations.

    Returns:
        Summary dictionary, database write result, or None when no data exists.
    """
    # get all daily obs from year
    obs = models.DailyOb.objects.filter(date__year=year).order_by("date")
    if obs.count() == 0:
        return None

    # convert to dataframe
    df = pd.DataFrame.from_records(obs.values())

    # calc general
    summary = calc_general_summary(df)

    # add meta
    summary["year"] = year

    # add annual specific fields
    normals = get_normals(year)
    norm_temp = Decimal(str(normals["temp"][12]))
    norm_precip = Decimal(str(normals["precip"][12]))
    norm_sf = Decimal(str(normals["sf"][12]))
    summary["avg_temp_dfn"] = Decimal(str(summary["avg_temp"])) - norm_temp
    summary["precip_dfn"] = Decimal(str(summary["precip"])) - norm_precip
    summary["sf_dfn"] = Decimal(str(summary["sf"])) - norm_sf

    if save_to_db:
        if models.AnnualSummary.objects.filter(year=year).exists():
            db_summary = models.AnnualSummary.objects.filter(year=year).update(
                **summary
            )
        else:
            db_summary = models.AnnualSummary.objects.create(**summary)

        return db_summary
    return summary


def calc_general_summary(df: pd.DataFrame) -> dict[str, object]:
    """Calculate shared summary statistics from a daily observation dataframe.

    See ``GeneralSummary`` for field-name abbreviations (grtr, grtst, hdd, cdd).

    Returns:
        Shared summary fields derived from the observation dataframe.
    """
    return {
        # temp fields
        "max_temp": Decimal(df.max_temp.max()),
        "max_temp_dates": list(df[df.max_temp == df.max_temp.max()].date),
        "max_temp_avg": Decimal(df.max_temp.mean()),
        "max_temp_grtr90_count": len(df[df.max_temp >= 90]),
        "max_temp_less32_count": len(df[df.max_temp <= 32]),
        "min_temp": Decimal(df.min_temp.min()),
        "min_temp_dates": list(df[df.min_temp == df.min_temp.min()].date),
        "min_temp_avg": Decimal(df.min_temp.mean()),
        "min_temp_less32_count": len(df[df.min_temp <= 32]),
        "min_temp_less0_count": len(df[df.min_temp <= 0]),
        "avg_temp": Decimal(df[["max_temp", "min_temp"]].mean(axis=1).mean()),
        "hdd_count": abs(
            round(
                sum(
                    df[(df[["max_temp", "min_temp"]].mean(axis=1)) < 65][
                        ["max_temp", "min_temp"]
                    ].mean(axis=1)
                    - 65
                )
            )
        ),
        "cdd_count": round(
            sum(
                df[(df[["max_temp", "min_temp"]].mean(axis=1)) > 65][
                    ["max_temp", "min_temp"]
                ].mean(axis=1)
                - 65
            )
        ),
        # precip fields
        "precip": TRACE_VAL
        if Decimal(df.precip.max()) == TRACE_VAL
        else Decimal(sum(df[df.precip != TRACE_VAL].precip)),
        "grtst_precip": Decimal(df.precip.max()),
        "grtst_precip_dates": []
        if df.precip.max() == 0
        else list(df[df.precip == df.precip.max()].date),
        "precip_grtrT": len(df[df.precip >= TRACE_VAL]),  # trace (T)
        "precip_grtr01": len(df[df.precip >= 0.01000]),  # 01 = 0.01"
        "precip_grtr10": len(df[df.precip >= 0.10000]),  # 10 = 0.10"
        "precip_grtr50": len(df[df.precip >= 0.50000]),
        "precip_grtr100": len(df[df.precip >= 1]),
        # snowfall and snowdepth fields
        "sf": TRACE_VAL
        if Decimal(df.snowfall.max()) == TRACE_VAL
        else Decimal(sum(df[df.snowfall != TRACE_VAL].snowfall)),
        "grtst_sf": Decimal(df.snowfall.max()),
        "grtst_sf_dates": []
        if df.snowfall.max() == 0
        else list(df[df.snowfall == df.snowfall.max()].date),
        "sf_grtrT": len(df[df.snowfall >= TRACE_VAL]),
        "sf_grtr1": len(df[df.snowfall >= 1]),  # in.
        "sf_grtr3": len(df[df.snowfall >= 3]),
        "sf_grtr6": len(df[df.snowfall >= 6]),
        "sf_grtr12": len(df[df.snowfall >= 12]),
        "sf_grtr18": len(df[df.snowfall >= 18]),
        "grtst_sd": Decimal(df.snowdepth.max()),
        "grtst_sd_dates": []
        if df.snowdepth.max() == 0
        else list(df[df.snowdepth == df.snowdepth.max()].date),
        "sd_grtrT": len(df[df.snowdepth >= TRACE_VAL]),
        "sd_grtr1": len(df[df.snowdepth >= 1]),  # in.
        "sd_grtr3": len(df[df.snowdepth >= 3]),
        "sd_grtr6": len(df[df.snowdepth >= 6]),
        "sd_grtr12": len(df[df.snowdepth >= 12]),
        "sd_grtr18": len(df[df.snowdepth >= 18]),
    }
