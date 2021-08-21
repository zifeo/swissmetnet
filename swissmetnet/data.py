from datetime import datetime

import pandas as pd


def read_vqha80():
    """
    Automatic weather stations - vqha80
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/info/VQHA80_en.txt
    """
    return pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA80.csv",
        sep=";",
        na_values="-",
        parse_dates=[1],
    ).assign(
        readAt=datetime.utcnow(),
    )


def read_vqha98():
    """
    Automatic precipitation monitoring stations - vqha98
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/info/VQHA98_en.txt
    """
    return pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA98.csv",
        sep=";",
        na_values="-",
        parse_dates=[1],
    ).assign(
        readAt=datetime.utcnow(),
    )


def read_cosmoe2():
    """
    Numerical forecasts - cosmo2e
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.prognosen/punktprognosen/Legende_COSMO-E_all_stations.txt
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.prognosen/punktprognosen/COSMO-E-all-stations.csv",
        sep=";",
        na_values="-999.0",
        parse_dates=[1, 2],
        skiprows=24,
        header=[0, 1, 2],
        index_col=[0, 1, 2],
    )
    df.columns.set_names(["indicator", "unit", "member"], inplace=True)
    df.index.set_names(["Station", "schedule", "leadtime"], inplace=True)
    df = df.stack([0, 1], dropna=True).dropna(axis=1).reset_index("unit", drop=True)
    df = df[[]].assign(v=df.values.tolist()).v.unstack("indicator").reset_index()
    df.columns.rename(None, inplace=True)
    return df.assign(
        Date=df.schedule - pd.to_timedelta(df.leadtime + ":00"),
        readAt=datetime.utcnow(),
    ).drop(columns=["schedule"])
