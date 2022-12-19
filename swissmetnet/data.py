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


def read_foehn():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-foehn-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-foehn-10min/ch.meteoschweiz.messwerte-foehn-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Foehn index", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_globalstrahlung():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-globalstrahlung-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-globalstrahlung-10min/ch.meteoschweiz.messwerte-globalstrahlung-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Global radiation W/m²", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_luftdruck_700():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-700hpa-flaeche-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-700hpa-flaeche-10min/ch.meteoschweiz.messwerte-luftdruck-700hpa-flaeche-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Pressure gpm", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_luftdruck_850():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-850hpa-flaeche-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-850hpa-flaeche-10min/ch.meteoschweiz.messwerte-luftdruck-850hpa-flaeche-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Pressure gpm", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_luftdruck_qfe():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qfe-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qfe-10min/ch.meteoschweiz.messwerte-luftdruck-qfe-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Pressure hPa", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_luftdruck_qff():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qff-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qff-10min/ch.meteoschweiz.messwerte-luftdruck-qff-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Pressure hPa", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_luftdruck_qnh():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qnh-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qnh-10min/ch.meteoschweiz.messwerte-luftdruck-qnh-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][["Abbr.", "WIGOS-ID", "Pressure hPa", "Measurement date"]]


def read_luftfeuchtigkeit():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftfeuchtigkeit-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftfeuchtigkeit-10min/ch.meteoschweiz.messwerte-luftfeuchtigkeit-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][["Abbr.", "WIGOS-ID", "Humidity %", "Measurement date"]].assign(
        readAt=datetime.utcnow(),
    )


def read_lufttemperatur():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-lufttemperatur-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-lufttemperatur-10min/ch.meteoschweiz.messwerte-lufttemperatur-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Temperature °C", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_niederschlag():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-niederschlag-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-niederschlag-10min/ch.meteoschweiz.messwerte-niederschlag-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Precipitation mm", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_sonnenscheindauer():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-sonnenscheindauer-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-sonnenscheindauer-10min/ch.meteoschweiz.messwerte-sonnenscheindauer-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Sunshine min", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_taupunkt():
    """
    https://data.geo.admin.ch/ch.meteoschweiz.messwerte-taupunkt-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-taupunkt-10min/ch.meteoschweiz.messwerte-taupunkt-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Dew point °C", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_wind_boeenspitze():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-wind-boeenspitze-kmh-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-wind-boeenspitze-kmh-10min/ch.meteoschweiz.messwerte-wind-boeenspitze-kmh-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Gust km/h", "Wind direction °", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )


def read_windgeschwindigkeit():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-windgeschwindigkeit-kmh-10min/
    """
    df = pd.read_csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-windgeschwindigkeit-kmh-10min/ch.meteoschweiz.messwerte-windgeschwindigkeit-kmh-10min_en.csv",
        encoding="ISO-8859-1",
        sep=";",
    )
    return df.iloc[:-3][
        ["Abbr.", "WIGOS-ID", "Wind km/h", "Wind direction °", "Measurement date"]
    ].assign(
        readAt=datetime.utcnow(),
    )
