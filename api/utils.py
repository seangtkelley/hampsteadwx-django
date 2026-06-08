"""Utilities for loading normals, processing CSVs, and calculating summaries."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import numpy as np
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


def add_alert(payload: dict[str, object], color: str, body: str) -> dict[str, object]:
    """Append an alert to a view payload.

    Returns:
        Updated payload containing the new alert.
    """
    alert = create_alert(color, body)
    if "alerts" in payload:
        payload["alerts"].append(alert)
    else:
        payload["alerts"] = [alert]

    return payload


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


def get_normals(year: int) -> dict[str, list[Decimal | float]]:
    """Load monthly and annual climate normals for the given year.

    Returns:
        Climate normals keyed by measurement type.
    """
    normals: dict[str, list[Decimal | float]] = {}
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

        normals["temp"].append(round(np.mean(normals["temp"]), 1))
        normals["precip"].append(round(np.mean(normals["precip"]), 2))
        normals["sf"].append(round(np.mean(normals["sf"]), 1))
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
    df = pd.read_csv(filepath, parse_dates=["DATE"])

    for _, row in df.iterrows():
        if models.DailyOb.objects.filter(date=row["DATE"].date()).exists():
            ob = models.DailyOb.objects.filter(date=row["DATE"].date()).first()
            ob.csv_filepath = str(filepath)
            ob.max_temp = Decimal(row["TX"])
            ob.min_temp = Decimal(row["TN"])
            ob.atob_temp = Decimal(row["TA"])

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
    obs = models.DailyOb.objects.filter(date__year=year, date__month=month).order_by(
        "date"
    )
    if obs.count() == 0:
        return None

    df = pd.DataFrame.from_records(obs.values())
    df[["max_temp", "min_temp", "atob_temp", "precip", "snowfall", "snowdepth"]] = df[
        ["max_temp", "min_temp", "atob_temp", "precip", "snowfall", "snowdepth"]
    ].apply(pd.to_numeric)

    summary = calc_general_summary(df)

    summary["date"] = df.iloc[0].date
    summary["csv_filepath"] = df.iloc[0].csv_filepath

    normals = get_normals(year)
    summary["avg_temp_dfn"] = summary["avg_temp"] - normals["temp"][month - 1]
    summary["precip_dfn"] = summary["precip"] - normals["precip"][month - 1]
    summary["sf_dfn"] = summary["sf"] - normals["sf"][month - 1]

    precip_todate = (
        models.DailyOb.objects.filter(
            date__year=year, date__month__in=list(range(1, month + 1))
        )
        .exclude(precip=TRACE_VAL)
        .aggregate(Sum("precip"))["precip__sum"]
    )
    summary["precip_todate"] = precip_todate
    summary["precip_todate_dfn"] = precip_todate - sum(normals["precip"][:month])

    if month >= 10:
        summary["sf_todate"] = (
            models.DailyOb.objects.filter(
                date__year=year, date__month__in=list(range(10, month + 1))
            )
            .exclude(snowfall=TRACE_VAL)
            .aggregate(Sum("snowfall"))["snowfall__sum"]
        )

        summary["sf_todate_dfn"] = summary["sf_todate"] - sum(normals["sf"][9:month])

    elif month <= 5:
        prev_year_sf = (
            models.DailyOb.objects.filter(
                date__year=year - 1, date__month__in=[10, 11, 12]
            )
            .exclude(snowfall=TRACE_VAL)
            .aggregate(Sum("snowfall"))["snowfall__sum"]
        )
        summary["sf_todate"] = prev_year_sf if prev_year_sf else 0

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

        if month in [10, 11, 12, 1, 2, 3, 4, 5]:
            if month in [10, 11, 12]:
                season_str = f"{year}-{year + 1}"
            elif month in [1, 2, 3, 4, 5]:
                season_str = f"{year - 1}-{year}"

            if models.SnowSeason.objects.filter(season=season_str).exists():
                snowseason = models.SnowSeason.objects.filter(season=season_str).first()
            else:
                snowseason = models.SnowSeason.objects.create(
                    **empty_snowseason(season_str)
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
    obs = models.DailyOb.objects.filter(date__year=year).order_by("date")
    if obs.count() == 0:
        return None

    df = pd.DataFrame.from_records(obs.values())

    summary = calc_general_summary(df)

    summary["year"] = year

    normals = get_normals(year)
    summary["avg_temp_dfn"] = summary["avg_temp"] - normals["temp"][12]
    summary["precip_dfn"] = summary["precip"] - normals["precip"][12]
    summary["sf_dfn"] = summary["sf"] - normals["sf"][12]

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

    Returns:
        Shared summary fields derived from the observation dataframe.
    """
    return {
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
        "precip": TRACE_VAL
        if Decimal(df.precip.max()) == TRACE_VAL
        else Decimal(sum(df[df.precip != TRACE_VAL].precip)),
        "grtst_precip": Decimal(df.precip.max()),
        "grtst_precip_dates": []
        if df.precip.max() == 0
        else list(df[df.precip == df.precip.max()].date),
        "precip_grtrT": len(df[df.precip >= TRACE_VAL]),
        "precip_grtr01": len(df[df.precip >= 0.01000]),
        "precip_grtr10": len(df[df.precip >= 0.10000]),
        "precip_grtr50": len(df[df.precip >= 0.50000]),
        "precip_grtr100": len(df[df.precip >= 1]),
        "sf": TRACE_VAL
        if Decimal(df.snowfall.max()) == TRACE_VAL
        else Decimal(sum(df[df.snowfall != TRACE_VAL].snowfall)),
        "grtst_sf": Decimal(df.snowfall.max()),
        "grtst_sf_dates": []
        if df.snowfall.max() == 0
        else list(df[df.snowfall == df.snowfall.max()].date),
        "sf_grtrT": len(df[df.snowfall >= TRACE_VAL]),
        "sf_grtr1": len(df[df.snowfall >= 1]),
        "sf_grtr3": len(df[df.snowfall >= 3]),
        "sf_grtr6": len(df[df.snowfall >= 6]),
        "sf_grtr12": len(df[df.snowfall >= 12]),
        "sf_grtr18": len(df[df.snowfall >= 18]),
        "grtst_sd": Decimal(df.snowdepth.max()),
        "grtst_sd_dates": []
        if df.snowdepth.max() == 0
        else list(df[df.snowdepth == df.snowdepth.max()].date),
        "sd_grtrT": len(df[df.snowdepth >= TRACE_VAL]),
        "sd_grtr1": len(df[df.snowdepth >= 1]),
        "sd_grtr3": len(df[df.snowdepth >= 3]),
        "sd_grtr6": len(df[df.snowdepth >= 6]),
        "sd_grtr12": len(df[df.snowdepth >= 12]),
        "sd_grtr18": len(df[df.snowdepth >= 18]),
    }
