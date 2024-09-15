# Swissmetnet

[![Actions Status](https://github.com/zifeo/swissmetnet/workflows/CI/badge.svg)](https://github.com/zifeo/swissmetnet/actions)

Transform & store weather data from MeteoSwiss to Pandas and Mongo.

## Getting started

```
poetry install
export MONGO_URI="mongodb://user@password:localhost:27017/db?authSource=admin"
python -m swissmetnet.main --data cosmo2e
poetry run swn --data vqha80 vqha98
```

## Docker example

Get the latest released version [here](https://github.com/zifeo/swissmetnet/pkgs/container/swissmetnet).

```
docker run --rm -e MONGO_URI="mongodb://user@password:localhost:27017/db?authSource=admin" ghcr.io/zifeo/swissmetnet:v0.1.2 --data vqha98
```

## Kubernetes example

```
apiVersion: batch/v1
kind: CronJob
metadata:
  name: smn
spec:
  schedule: "5 */6 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: swissmetnet
            image: ghcr.io/zifeo/swissmetnet:v0.1.2
            imagePullPolicy: IfNotPresent
            args:
            - --data
            - cosmo2e
            env:
            - name: MONGO_URI
              valueFrom:
                secretKeyRef:
                  name: smn-conf
                  key: mongo_uri
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

### Numerical forecasts - cosmo2e

Doc: https://data.geo.admin.ch/ch.meteoschweiz.prognosen/punktprognosen/Legende_COSMO-E_all_stations.txt

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

## License

This code is licensed under [Mozilla Public License](./LICENSE).

At the time of writing, the processed data may be used under the licensing "Open use. Must provide the source. Use for commercial purposes requires permission of the data owner.". However, check your own usage and exact data license on the opendata.swiss [project](https://opendata.swiss/). You can learn more about MeteoSwiss legal basis on their [website](https://www.meteoswiss.admin.ch/home/about-us/legal-basis.html).
