# Swissmetnet

[![Actions Status](https://github.com/zifeo/swissmetnet/workflows/CI/badge.svg)](https://github.com/zifeo/swissmetnet/actions)

Transform & store weather data from MeteoSwiss to Pandas and Mongo.

## Getting started

Python 3.13+ is required.

```
uv sync
export MONGO_URI="mongodb://user:password@localhost:27017/db?authSource=admin"
uv run swn --data vqha80 vqha98 --storage mongo
uv run --env-file .env swn --data local_forecast --storage s3
uv run --env-file .env swn --data icon_ch2e --storage s3
```

## Docker example

Get the latest released version [here](https://github.com/zifeo/swissmetnet/pkgs/container/swissmetnet).

```
docker run --rm -e MONGO_URI="mongodb://user:password@localhost:27017/db?authSource=admin" ghcr.io/zifeo/swissmetnet:v0.1.2 --data vqha98 --storage mongo
```

## Kubernetes example

```
apiVersion: batch/v1
kind: CronJob
metadata:
  name: smn
spec:
  schedule: "15 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      backoffLimit: 2
      template:
        spec:
          restartPolicy: OnFailure
          containers:
          - name: swissmetnet
            image: ghcr.io/zifeo/swissmetnet:v0.1.2
            imagePullPolicy: IfNotPresent
            args:
            - --data
            - icon_ch2e
            - --storage
            - s3
            env:
            - name: S3_ENDPOINT
              valueFrom:
                secretKeyRef:
                  name: smn-conf
                  key: s3_endpoint
            - name: S3_BUCKET
              valueFrom:
                secretKeyRef:
                  name: smn-conf
                  key: s3_bucket
            - name: S3_ACCESS_KEY
              valueFrom:
                secretKeyRef:
                  name: smn-conf
                  key: s3_access_key
            - name: S3_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: smn-conf
                  key: s3_secret_key
            - name: S3_REGION
              valueFrom:
                secretKeyRef:
                  name: smn-conf
                  key: s3_region
```

## Sources

### Automatic weather stations - vqha80

Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/info/VQHA80_en.txt

https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA80.csv

```json
{
  "_id": {
    "$oid": "610737dde83152fee57fca76"
  },
  "Station/Location": "TAE",
  "Date": {
    "$numberLong": "1627862400000"
  },
  "tre200s0": 12.1,
  "rre150z0": 0,
  "sre000z0": 0,
  "gre000z0": 1,
  "ure200s0": 90.4,
  "tde200s0": 10.6,
  "dkl010z0": 308,
  "fu3010z0": 3.6,
  "fu3010z1": 6.1,
  "prestas0": 953.2,
  "pp0qffs0": 1016.1,
  "pp0qnhs0": 1016.5,
  "ppz850s0": null,
  "ppz700s0": null,
  "dv1towz0": null,
  "fu3towz0": null,
  "fu3towz1": null,
  "ta1tows0": null,
  "uretows0": null,
  "tdetows0": null,
  "readAt": {
    "$numberLong": "1627863005014"
  }
}
```

### Automatic precipitation monitoring stations - vqha98

Doc: https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/info/VQHA98_en.txt

https://data.geo.admin.ch/ch.meteoschweiz.messwerte-aktuell/VQHA98.csv

```json
{
  "_id": {
    "$oid": "610737dde83152fee57fcb15"
  },
  "Station/Location": "AGATT",
  "Date": {
    "$numberLong": "1627862400000"
  },
  "rre150z0": 0,
  "readAt": {
    "$numberLong": "1627863005182"
  }
}
```

### Archived station ensemble - cosmo2e

Kept for the existing Mongo/S3 series. The filename is still COSMO-E-all-stations.csv. The content is a frozen ICON-CH2-EPS dump (last refresh around 2026-05-11).

https://data.geo.admin.ch/ch.meteoschweiz.prognosen/punktprognosen/COSMO-E-all-stations.csv

```json
{
  "_id": {
    "$oid": "610737295bb195733027fed7"
  },
  "Station": "ABO",
  "leadtime": "000:00",
  "DD_10M": [
    31.5, 31.9, 336, 76.6, 17.7, 47.4, 322.3, 304.6, 22.5, 190.9, 30.5, 24,
    29.8, 58.3, 6.7, 20.6, 53.2, 306, 311.3, 21.1, 24.4
  ],
  "FF_10M": [
    1.3, 1.2, 0.4, 0.3, 1.6, 2, 0.6, 0.6, 3.9, 0.6, 1.1, 2.8, 1.1, 1, 1, 0.7,
    0.4, 0.4, 0.3, 0.7, 1.7
  ],
  "RELHUM_2M": [
    76.8, 78.2, 76.9, 78.8, 75.7, 80.3, 77.7, 74.1, 77.5, 77, 81.2, 73.8, 78.9,
    80.7, 80.3, 75, 82.3, 81.6, 75.5, 81.9, 76.9
  ],
  "T_2M": [
    9.1, 9, 8.9, 9, 9.2, 9, 9.2, 9.5, 8.7, 8.8, 9.2, 9.1, 9.2, 9, 9, 9.2, 9.4,
    9.1, 8.7, 9, 8.7
  ],
  "DURSUN": null,
  "TOT_PREC": null,
  "Date": {
    "$numberLong": "1627840800000"
  },
  "readAt": {
    "$numberLong": "1627862824895"
  }
}
```

### Local point forecasts - local_forecast

Live 9-day point forecasts used by the MeteoSwiss app (stations, postal codes, mountain POIs). Updated hourly. Ingests all parameter files of the latest complete STAC issue.

Doc: https://opendatadocs.meteoswiss.ch/e-forecast-data/e4-local-forecast-data

STAC: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-local-forecasting

```json
{
  "point_id": 1,
  "point_type_id": 1,
  "Date": "2026-11-15T07:00:00",
  "tre200h0": 0.4,
  "dkl010h0": 185,
  "fu3010h0": 1.8,
  "fu3010h1": 4.3,
  "rre150h0": 0.0,
  "sre000h0": 0,
  "gre000h0": 3,
  "station_abbr": "ARO",
  "point_name": "Arosa",
  "issueAt": "2026-11-15T07:00:00",
  "readAt": "2026-11-15T07:50:00"
}
```

### ICON-CH2-EPS - icon_ch2e

Native GRIB files copied to S3. No station extraction, no derived fields. Lists `icon_ch2e/{ref}/` once on S3 and only fetches missing GRIBs, so an interrupted CronJob resumes without re-downloading.

Needs `--storage s3` and the `S3_*` env.

Doc: https://opendatadocs.meteoswiss.ch/e-forecast-data/e2-e3-numerical-weather-forecasting-model

STAC: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-forecasting-icon-ch2

```
icon_ch2e/2026-11-15T000000Z/T_2M/P0DT06H00M00S/ctrl.grib2
icon_ch2e/2026-11-15T000000Z/T_2M/P0DT06H00M00S/pert.grib2
```

## License

This code is licensed under [Mozilla Public License](./LICENSE).

MeteoSwiss Open Data may be used without restriction. The source must be cited when reproducing or redistributing ("Source: MeteoSwiss"). Confirm the current [terms of use](https://opendatadocs.meteoswiss.ch) and [legal basis](https://www.meteoswiss.admin.ch/home/about-us/legal-basis.html) before reuse. Dataset pages also live on [opendata.swiss](https://opendata.swiss/).
