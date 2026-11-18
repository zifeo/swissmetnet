from datetime import datetime
from datetime import timezone
import io
import logging
import time

import pandas as pd
import requests

_STAC = "https://data.geo.admin.ch/api/stac/v1"
_LOCAL_COLLECTION = "ch.meteoschweiz.ogd-local-forecasting"
_ICON_COLLECTION = "ch.meteoschweiz.ogd-forecasting-icon-ch2"
_META_POINT = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/"
    "ogd-local-forecasting_meta_point.csv"
)
_COSMO_CSV = (
    "https://data.geo.admin.ch/ch.meteoschweiz.prognosen/punktprognosen/"
    "COSMO-E-all-stations.csv"
)
_ICON_VARS = ("T_2M", "U_10M", "V_10M", "TD_2M", "TOT_PREC", "DURSUN")
_ICON_STEPS_H = range(0, 121, 6)
_RETRY_STATUS = {408, 429, 500, 502, 503, 504}


def _utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None, microsecond=0)


def _request(method, url, timeout=120, **kwargs):
    headers = {"User-Agent": "swissmetnet"}
    for attempt in range(3):
        try:
            resp = requests.request(
                method, url, headers=headers, timeout=timeout, **kwargs
            )
            if resp.status_code in _RETRY_STATUS and attempt < 2:
                logging.warning(
                    "http %s %s, retry %s",
                    resp.status_code,
                    resp.url.split("?")[0],
                    attempt + 1,
                )
                time.sleep(2**attempt)
                continue
            resp.raise_for_status()
            return resp
        except (requests.Timeout, requests.ConnectionError) as err:
            if attempt >= 2:
                raise
            logging.warning(
                "http %s %s, retry %s",
                type(err).__name__,
                url.split("?")[0],
                attempt + 1,
            )
            time.sleep(2**attempt)


def _get(url, timeout=120):
    return _request("GET", url, timeout=timeout)


def _csv(url, **kwargs):
    return pd.read_csv(io.BytesIO(_get(url).content), **kwargs)


def _stac_pages(**body):
    payload = _request("POST", f"{_STAC}/search", timeout=30, json=body).json()
    seen = set()
    while True:
        yield payload.get("features") or []
        nxt = next(
            (link for link in payload.get("links") or [] if link.get("rel") == "next"),
            None,
        )
        if not nxt:
            return
        cursor = (nxt.get("body") or {}).get("cursor")
        if not cursor or cursor in seen:
            return
        seen.add(cursor)
        payload = _request(
            "POST", f"{_STAC}/search", timeout=30, json={**body, "cursor": cursor}
        ).json()


def _stac_features(**body):
    features = []
    for page in _stac_pages(**body):
        features.extend(page)
    return features


def read_vqha80():
    """
    Automatic weather stations - vqha80
    Doc: https://opendatadocs.meteoswiss.ch/a-data-groundbased/a1-automatic-weather-stations
    Live: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA80.csv
    """
    return _csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA80.csv",
        sep=";",
        na_values="-",
        parse_dates=[1],
    ).assign(
        readAt=_utcnow(),
    )


def read_vqha98():
    """
    Automatic precipitation monitoring stations - vqha98
    Doc: https://opendatadocs.meteoswiss.ch/a-data-groundbased/a2-automatic-precipitation-stations
    Live: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA98.csv
    """
    return _csv(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA98.csv",
        sep=";",
        na_values="-",
        parse_dates=[1],
    ).assign(
        readAt=_utcnow(),
    )


def read_cosmo2e():
    """
    Archived ICON-CH2-EPS station dump still published as COSMO-E-all-stations.csv.
    """
    logging.warning(
        "cosmo2e reads a frozen dump, use local_forecast and icon_ch2e for live forecasts"
    )
    df = _csv(
        _COSMO_CSV,
        sep=";",
        na_values="-999.0",
        parse_dates=[1, 2],
        skiprows=23,
        header=[0, 1, 2],
        index_col=[0, 1, 2],
        date_format="%Y%m%d %H:%M",
    )
    df.columns = df.columns.set_names(["indicator", "unit", "member"])
    df.index = df.index.set_names(["Station", "schedule", "leadtime"])
    df = df.droplevel("unit", axis=1)
    packed = {}
    for indicator in df.columns.get_level_values("indicator").unique():
        values = [
            None if all(pd.isna(v) for v in row) else list(row)
            for row in df.xs(indicator, axis=1, level="indicator").to_numpy()
        ]
        if any(row is not None for row in values):
            packed[indicator] = values
    out = pd.DataFrame(packed, index=df.index).reset_index().rename_axis(columns=None)
    return out.assign(
        Date=out.schedule - pd.to_timedelta(out.leadtime + ":00"),
        readAt=_utcnow(),
    ).drop(columns=["schedule"])


def read_local_forecast():
    """
    Live MeteoSwiss local point forecasts (stations, postal codes, mountain POIs).
    Doc: https://opendatadocs.meteoswiss.ch/e-forecast-data/e4-local-forecast-data
    """
    issue_at, assets = _latest_local_issue()
    keys = ["point_id", "point_type_id", "Date"]
    parts = []
    for href in assets.values():
        part = _csv(href, sep=";", encoding="ISO-8859-1")
        part["Date"] = pd.to_datetime(part["Date"], format="%Y%m%d%H%M")
        parts.append(part.set_index(keys))
    if not parts:
        raise RuntimeError(f"no local forecast parameter files for {issue_at}")
    df = pd.concat(parts, axis=1, join="outer").reset_index()
    meta = _csv(_META_POINT, sep=";", encoding="ISO-8859-1")[
        ["point_id", "point_type_id", "station_abbr", "point_name"]
    ]
    df = df.merge(meta, on=["point_id", "point_type_id"], how="left")
    return df.assign(issueAt=issue_at, readAt=_utcnow())


def _latest_local_issue():
    payload = _get(f"{_STAC}/collections/{_LOCAL_COLLECTION}/items?limit=20").json()
    issues = {}
    for feat in payload.get("features") or []:
        for name, asset in (feat.get("assets") or {}).items():
            parts = name.split(".")
            if len(parts) < 5 or parts[-1] != "csv":
                continue
            stamp, param = parts[2], parts[3]
            try:
                datetime.strptime(stamp, "%Y%m%d%H%M")
            except ValueError:
                continue
            issues.setdefault(stamp, {})[param] = asset["href"]
    if not issues:
        raise RuntimeError("no local forecast assets on STAC")
    expected = max(len(params) for params in issues.values())
    for stamp in sorted(issues, reverse=True):
        if len(issues[stamp]) == expected:
            return datetime.strptime(stamp, "%Y%m%d%H%M"), issues[stamp]
        logging.warning("local_forecast issue %s still publishing", stamp)
    raise RuntimeError("no complete local forecast issue on STAC")


def latest_complete_icon_ref():
    horizon = _iso_horizon(max(_ICON_STEPS_H))
    by_ref = {}
    for variable in _ICON_VARS:
        for feat in _stac_features(
            collections=[_ICON_COLLECTION],
            limit=20,
            **{
                "forecast:variable": variable,
                "forecast:horizon": horizon,
            },
        ):
            props = feat.get("properties") or {}
            ref = props.get("forecast:reference_datetime")
            if not ref or "forecast:perturbed" not in props:
                continue
            if _expired(props.get("expires")):
                continue
            by_ref.setdefault(ref, set()).add(
                (variable, bool(props.get("forecast:perturbed")))
            )
    for ref in sorted(by_ref, reverse=True):
        if len(by_ref[ref]) == len(_ICON_VARS) * 2:
            return ref
        logging.warning("icon_ch2e ref %s still publishing", ref)
    return None


def icon_asset_list(ref):
    need = {
        (variable, perturbed, _iso_horizon(hours))
        for variable in _ICON_VARS
        for perturbed in (False, True)
        for hours in _ICON_STEPS_H
    }
    hrefs = {}
    missing = set()
    for variable in _ICON_VARS:
        want = {key for key in need if key[0] == variable}
        for page in _stac_pages(
            collections=[_ICON_COLLECTION],
            limit=100,
            **{
                "forecast:variable": variable,
                "forecast:reference_datetime": ref,
            },
        ):
            for feat in page:
                props = feat.get("properties") or {}
                if "forecast:perturbed" not in props or _expired(props.get("expires")):
                    continue
                assets = feat.get("assets") or {}
                if not assets:
                    continue
                key = (
                    variable,
                    bool(props.get("forecast:perturbed")),
                    props.get("forecast:horizon"),
                )
                if key in want:
                    hrefs[key] = next(iter(assets.values()))["href"]
            if want <= hrefs.keys():
                break
        missing.update(key for key in want if key not in hrefs)
    if missing:
        raise RuntimeError(
            f"icon_ch2e ref {ref} incomplete, missing {len(missing)} assets"
        )
    stamp = ref.replace(":", "")
    return [
        {
            "variable": variable,
            "perturbed": perturbed,
            "horizon": horizon,
            "href": hrefs[(variable, perturbed, horizon)],
            "key": f"icon_ch2e/{stamp}/{variable}/{horizon}/{'pert' if perturbed else 'ctrl'}.grib2",
        }
        for variable, perturbed, horizon in sorted(hrefs)
    ]


def icon_grib_bytes(asset, ref):
    try:
        return _get(asset["href"], timeout=180).content
    except requests.HTTPError as err:
        status = err.response.status_code if err.response is not None else None
        if status not in {401, 403}:
            raise
        logging.warning("icon_ch2e signed url expired, refreshing %s", asset["key"])
        href = _icon_refresh_href(
            asset["variable"], asset["perturbed"], asset["horizon"], ref
        )
        return _get(href, timeout=180).content


def _expired(expires):
    if not expires:
        return False
    return datetime.fromisoformat(expires.replace("Z", "+00:00")) <= datetime.now(
        timezone.utc
    )


def _icon_refresh_href(variable, perturbed, horizon, ref):
    for feat in _stac_features(
        collections=[_ICON_COLLECTION],
        limit=5,
        **{
            "forecast:variable": variable,
            "forecast:perturbed": perturbed,
            "forecast:horizon": horizon,
            "forecast:reference_datetime": ref,
        },
    ):
        props = feat.get("properties") or {}
        if _expired(props.get("expires")):
            continue
        assets = feat.get("assets") or {}
        if assets:
            return next(iter(assets.values()))["href"]
    raise RuntimeError(
        f"no ICON-CH2 asset {variable} perturbed={perturbed} {horizon} ref {ref}"
    )


def _iso_horizon(hours):
    days, rem = divmod(hours, 24)
    return f"P{days}DT{rem:02d}H00M00S"


def _read_individual(uri: str, *metric_names: str):
    df = (
        _csv(
            uri,
            encoding="ISO-8859-1",
            sep=";",
        )
        .iloc[:-3][["Abbr.", "WIGOS-ID", *metric_names, "Measurement date"]]
        .rename(columns={"Measurement date": "Date"})
    )
    return df.assign(
        Date=pd.to_datetime(df.Date),
        readAt=_utcnow(),
    )


def read_foehn():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-foehn-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-foehn-10min/ch.meteoschweiz.messwerte-foehn-10min_en.csv",
        "Foehn index",
    )


def read_globalstrahlung():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-globalstrahlung-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-globalstrahlung-10min/ch.meteoschweiz.messwerte-globalstrahlung-10min_en.csv",
        "Global radiation W/m²",
    )


def read_luftdruck_700():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-700hpa-flaeche-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-700hpa-flaeche-10min/ch.meteoschweiz.messwerte-luftdruck-700hpa-flaeche-10min_en.csv",
        "Pressure gpm",
    )


def read_luftdruck_850():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-850hpa-flaeche-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-850hpa-flaeche-10min/ch.meteoschweiz.messwerte-luftdruck-850hpa-flaeche-10min_en.csv",
        "Pressure gpm",
    )


def read_luftdruck_qfe():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qfe-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qfe-10min/ch.meteoschweiz.messwerte-luftdruck-qfe-10min_en.csv",
        "Pressure hPa",
    )


def read_luftdruck_qff():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qff-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qff-10min/ch.meteoschweiz.messwerte-luftdruck-qff-10min_en.csv",
        "Pressure hPa",
    )


def read_luftdruck_qnh():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qnh-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftdruck-qnh-10min/ch.meteoschweiz.messwerte-luftdruck-qnh-10min_en.csv",
        "Pressure hPa",
    )


def read_luftfeuchtigkeit():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftfeuchtigkeit-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-luftfeuchtigkeit-10min/ch.meteoschweiz.messwerte-luftfeuchtigkeit-10min_en.csv",
        "Humidity %",
    )


def read_lufttemperatur():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-lufttemperatur-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-lufttemperatur-10min/ch.meteoschweiz.messwerte-lufttemperatur-10min_en.csv",
        "Temperature °C",
    )


def read_niederschlag():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-niederschlag-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-niederschlag-10min/ch.meteoschweiz.messwerte-niederschlag-10min_en.csv",
        "Precipitation mm",
    )


def read_sonnenscheindauer():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-sonnenscheindauer-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-sonnenscheindauer-10min/ch.meteoschweiz.messwerte-sonnenscheindauer-10min_en.csv",
        "Sunshine min",
    )


def read_taupunkt():
    """
    https://data.geo.admin.ch/ch.meteoschweiz.messwerte-taupunkt-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-taupunkt-10min/ch.meteoschweiz.messwerte-taupunkt-10min_en.csv",
        "Dew point °C",
    )


def read_wind_boeenspitze():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-wind-boeenspitze-kmh-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-wind-boeenspitze-kmh-10min/ch.meteoschweiz.messwerte-wind-boeenspitze-kmh-10min_en.csv",
        "Gust km/h",
        "Wind direction °",
    )


def read_windgeschwindigkeit():
    """
    Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-windgeschwindigkeit-kmh-10min/
    """
    return _read_individual(
        "https://data.geo.admin.ch/ch.meteoschweiz.messwerte-windgeschwindigkeit-kmh-10min/ch.meteoschweiz.messwerte-windgeschwindigkeit-kmh-10min_en.csv",
        "Wind km/h",
        "Wind direction °",
    )
