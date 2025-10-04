# Curl Logs for Toronto Exploration
Generated 2025-10-04T16:33:20.675702Z

## Locations near Toronto coordinates
```bash
curl -s "http://127.0.0.1:8000/locations?coordinates=-79.3832,43.6532&radius=25000&limit=5"
```
```json
{
  "meta": {
    "found": 0,
    "limit": 5,
    "name": "openaq-api",
    "page": 1,
    "website": "/"
  },
  "results": []
}
```

## Latest PM2.5 samples (limit 500)
```bash
curl -s "http://127.0.0.1:8000/parameters/2/latest?limit=500"
```
Showing first 5 of 500 results:
```json
{
  "meta": {
    "found": 22435,
    "limit": 500,
    "name": "openaq-api",
    "page": 1,
    "website": "/"
  },
  "results": [
    {
      "coordinates": {
        "latitude": 35.21815,
        "longitude": 128.57425
      },
      "datetime": {
        "local": "2025-10-05T01:00:00+09:00",
        "utc": "2025-10-04T16:00:00Z"
      },
      "locationsId": 2622686,
      "sensorsId": 8539597,
      "value": 8.0
    },
    {
      "coordinates": {
        "latitude": 54.88361359025449,
        "longitude": 23.83583450024486
      },
      "datetime": {
        "local": "2025-10-04T18:00:00+03:00",
        "utc": "2025-10-04T15:00:00Z"
      },
      "locationsId": 8152,
      "sensorsId": 23735,
      "value": -1.0
    },
    {
      "coordinates": {
        "latitude": 40.1465,
        "longitude": 117.07089999999998
      },
      "datetime": {
        "local": "2021-08-09T19:00:00+08:00",
        "utc": "2021-08-09T11:00:00Z"
      },
      "locationsId": 43487,
      "sensorsId": 238048,
      "value": 16.0
    },
    {
      "coordinates": {
        "latitude": 37.64553,
        "longitude": -118.96676
      },
      "datetime": {
        "local": "2025-08-09T07:00:00-07:00",
        "utc": "2025-08-09T14:00:00Z"
      },
      "locationsId": 1772963,
      "sensorsId": 7320157,
      "value": 9.0
    },
    {
      "coordinates": {
        "latitude": 53.129418999879455,
        "longitude": 23.108024999656525
      },
      "datetime": {
        "local": "2024-12-09T13:00:00+01:00",
        "utc": "2024-12-09T12:00:00Z"
      },
      "locationsId": 2146563,
      "sensorsId": 7754909,
      "value": 6.0
    }
  ]
}
```

Entries within ~1 degree of downtown Toronto:
```json
[
  {
    "coordinates": {
      "latitude": 43.668502,
      "longitude": -79.760339
    },
    "datetime": {
      "local": "2025-10-04T12:00:00-04:00",
      "utc": "2025-10-04T16:00:00Z"
    },
    "locationsId": 2966040,
    "sensorsId": 10017217,
    "value": 8.400958323478699,
    "distance_deg": 0.3774493032514429
  }
]
```

## Sensor 10017217 raw measurements
```bash
curl -s "http://127.0.0.1:8000/sensors/10017217/measurements?limit=5"
```
```json
{
  "meta": {
    "found": ">5",
    "limit": 5,
    "name": "openaq-api",
    "page": 1,
    "website": "/"
  },
  "results": [
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T10:00:00-04:00",
          "utc": "2024-07-20T14:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T11:00:00-04:00",
          "utc": "2024-07-20T15:00:00Z"
        },
        "expectedCount": 1,
        "expectedInterval": "01:00:00",
        "observedCount": 1,
        "observedInterval": "01:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-20T10:00:00-04:00",
          "utc": "2024-07-20T14:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T11:00:00-04:00",
          "utc": "2024-07-20T15:00:00Z"
        },
        "interval": "01:00:00",
        "label": "raw"
      },
      "summary": null,
      "value": 7.949999928474426
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T11:00:00-04:00",
          "utc": "2024-07-20T15:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T12:00:00-04:00",
          "utc": "2024-07-20T16:00:00Z"
        },
        "expectedCount": 1,
        "expectedInterval": "01:00:00",
        "observedCount": 1,
        "observedInterval": "01:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-20T11:00:00-04:00",
          "utc": "2024-07-20T15:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T12:00:00-04:00",
          "utc": "2024-07-20T16:00:00Z"
        },
        "interval": "01:00:00",
        "label": "raw"
      },
      "summary": null,
      "value": 8.001666688919068
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T12:00:00-04:00",
          "utc": "2024-07-20T16:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T13:00:00-04:00",
          "utc": "2024-07-20T17:00:00Z"
        },
        "expectedCount": 1,
        "expectedInterval": "01:00:00",
        "observedCount": 1,
        "observedInterval": "01:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-20T12:00:00-04:00",
          "utc": "2024-07-20T16:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T13:00:00-04:00",
          "utc": "2024-07-20T17:00:00Z"
        },
        "interval": "01:00:00",
        "label": "raw"
      },
      "summary": null,
      "value": 9.262499968210856
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T13:00:00-04:00",
          "utc": "2024-07-20T17:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T14:00:00-04:00",
          "utc": "2024-07-20T18:00:00Z"
        },
        "expectedCount": 1,
        "expectedInterval": "01:00:00",
        "observedCount": 1,
        "observedInterval": "01:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-20T13:00:00-04:00",
          "utc": "2024-07-20T17:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T14:00:00-04:00",
          "utc": "2024-07-20T18:00:00Z"
        },
        "interval": "01:00:00",
        "label": "raw"
      },
      "summary": null,
      "value": 10.287500023841858
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T14:00:00-04:00",
          "utc": "2024-07-20T18:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T15:00:00-04:00",
          "utc": "2024-07-20T19:00:00Z"
        },
        "expectedCount": 1,
        "expectedInterval": "01:00:00",
        "observedCount": 1,
        "observedInterval": "01:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-20T14:00:00-04:00",
          "utc": "2024-07-20T18:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-20T15:00:00-04:00",
          "utc": "2024-07-20T19:00:00Z"
        },
        "interval": "01:00:00",
        "label": "raw"
      },
      "summary": null,
      "value": 8.483333230018616
    }
  ]
}
```

## Sensor 10017217 daily aggregates
```bash
curl -s "http://127.0.0.1:8000/sensors/10017217/days?limit=7"
```
```json
{
  "meta": {
    "found": ">7",
    "limit": 7,
    "name": "openaq-api",
    "page": 1,
    "website": "/"
  },
  "results": [
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T11:00:00-04:00",
          "utc": "2024-07-20T15:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-21T00:00:00-04:00",
          "utc": "2024-07-21T04:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 14,
        "observedInterval": "14:00:00",
        "percentComplete": 58.0,
        "percentCoverage": 58.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-20T00:00:00-04:00",
          "utc": "2024-07-20T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-21T00:00:00-04:00",
          "utc": "2024-07-21T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 9.956071395533424,
        "max": 17.02916653951009,
        "median": 8.756250043710072,
        "min": 7.674999992052714,
        "q02": 7.74649997552236,
        "q25": 8.318750003973642,
        "q75": 10.031250009934107,
        "q98": 16.355333177248635,
        "sd": 0.036533916672346865
      },
      "value": 9.96
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-21T03:00:00-04:00",
          "utc": "2024-07-21T07:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-21T23:00:00-04:00",
          "utc": "2024-07-22T03:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 19,
        "observedInterval": "19:00:00",
        "percentComplete": 79.0,
        "percentCoverage": 79.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-21T00:00:00-04:00",
          "utc": "2024-07-21T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-22T00:00:00-04:00",
          "utc": "2024-07-22T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 16.569736844614937,
        "max": 33.170832792917885,
        "median": 15.570833444595337,
        "min": 6.27916665871938,
        "q02": 6.87916668732961,
        "q25": 13.162499984105429,
        "q75": 19.652083476384483,
        "q98": 29.230333010355636,
        "sd": 3.0483324280315967
      },
      "value": 16.6
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-22T01:00:00-04:00",
          "utc": "2024-07-22T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-23T00:00:00-04:00",
          "utc": "2024-07-23T04:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 24,
        "observedInterval": "24:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-22T00:00:00-04:00",
          "utc": "2024-07-22T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-23T00:00:00-04:00",
          "utc": "2024-07-23T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 8.78454860755139,
        "max": 20.133333206176758,
        "median": 6.008333285649617,
        "min": 1.6249999900658925,
        "q02": 1.7055000001192093,
        "q25": 2.5395833353201547,
        "q75": 15.323958357175192,
        "q98": 19.475916627248125,
        "sd": 0.7188315072007877
      },
      "value": 8.78
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-23T01:00:00-04:00",
          "utc": "2024-07-23T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-24T00:00:00-04:00",
          "utc": "2024-07-24T04:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 24,
        "observedInterval": "24:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-23T00:00:00-04:00",
          "utc": "2024-07-23T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-24T00:00:00-04:00",
          "utc": "2024-07-24T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 9.905555520620611,
        "max": 22.008333047231037,
        "median": 8.156249980131784,
        "min": 2.924999992052714,
        "q02": 2.942249975601832,
        "q25": 3.873958319425583,
        "q75": 15.847916702429453,
        "q98": 21.77449984550476,
        "sd": null
      },
      "value": 9.91
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-24T01:00:00-04:00",
          "utc": "2024-07-24T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-25T00:00:00-04:00",
          "utc": "2024-07-25T04:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 24,
        "observedInterval": "24:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-24T00:00:00-04:00",
          "utc": "2024-07-24T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-25T00:00:00-04:00",
          "utc": "2024-07-25T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 19.523842553021726,
        "max": 31.2541667620341,
        "median": 22.829166571299233,
        "min": 3.724999984105428,
        "q02": 4.2195000243186955,
        "q25": 7.973958323399225,
        "q75": 25.588541547457375,
        "q98": 31.196666688919066,
        "sd": null
      },
      "value": 19.5
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-25T01:00:00-04:00",
          "utc": "2024-07-25T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-26T00:00:00-04:00",
          "utc": "2024-07-26T04:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 24,
        "observedInterval": "24:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-25T00:00:00-04:00",
          "utc": "2024-07-25T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-26T00:00:00-04:00",
          "utc": "2024-07-26T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 6.109374990893734,
        "max": 30.720833281675976,
        "median": 4.202083309491476,
        "min": 2.1375000377496085,
        "q02": 2.2774166806538902,
        "q25": 3.721875001986821,
        "q75": 6.918750027815501,
        "q98": 21.01866662780442,
        "sd": 0.10606597222134413
      },
      "value": 6.11
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-26T01:00:00-04:00",
          "utc": "2024-07-26T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-27T00:00:00-04:00",
          "utc": "2024-07-27T04:00:00Z"
        },
        "expectedCount": 24,
        "expectedInterval": "24:00:00",
        "observedCount": 24,
        "observedInterval": "24:00:00",
        "percentComplete": 100.0,
        "percentCoverage": 100.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-07-26T00:00:00-04:00",
          "utc": "2024-07-26T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2024-07-27T00:00:00-04:00",
          "utc": "2024-07-27T04:00:00Z"
        },
        "interval": "24:00:00",
        "label": "1day"
      },
      "summary": {
        "avg": 7.737673618727261,
        "max": 16.200000206629436,
        "median": 6.612499992052714,
        "min": 5.791666626930237,
        "q02": 5.808916637897491,
        "q25": 6.033333321412404,
        "q75": 8.088541726271313,
        "q98": 15.843500126202901,
        "sd": null
      },
      "value": 7.74
    }
  ]
}
```

## Sensor 10017217 yearly aggregates
```bash
curl -s "http://127.0.0.1:8000/sensors/10017217/days/yearly?limit=3"
```
```json
{
  "meta": {
    "found": 2,
    "limit": 3,
    "name": "openaq-api",
    "page": 1,
    "website": "/"
  },
  "results": [
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2024-07-20T00:00:00-04:00",
          "utc": "2024-07-20T04:00:00Z"
        },
        "datetimeTo": {
          "local": "2025-01-01T00:00:00-05:00",
          "utc": "2025-01-01T05:00:00Z"
        },
        "expectedCount": 366,
        "expectedInterval": "8784:00:00",
        "observedCount": 165,
        "observedInterval": "3960:00:00",
        "percentComplete": 45.0,
        "percentCoverage": 45.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2024-01-01T00:00:00-05:00",
          "utc": "2024-01-01T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2025-01-01T00:00:00-05:00",
          "utc": "2025-01-01T05:00:00Z"
        },
        "interval": "1year",
        "label": "1 year"
      },
      "summary": {
        "avg": 11.34048442127574,
        "max": 36.851148737801445,
        "median": 8.78454860755139,
        "min": 0.10000000154185627,
        "q02": 0.5257837044344181,
        "q25": 4.289062501655685,
        "q75": 17.281250024421343,
        "q98": 31.36228245390786,
        "sd": 8.585724077067084
      },
      "value": 11.3
    },
    {
      "coordinates": null,
      "coverage": {
        "datetimeFrom": {
          "local": "2025-01-01T00:00:00-05:00",
          "utc": "2025-01-01T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2025-10-04T00:00:00-04:00",
          "utc": "2025-10-04T04:00:00Z"
        },
        "expectedCount": 365,
        "expectedInterval": "8760:00:00",
        "observedCount": 247,
        "observedInterval": "5928:00:00",
        "percentComplete": 68.0,
        "percentCoverage": 68.0
      },
      "flagInfo": {
        "hasFlags": false
      },
      "parameter": {
        "displayName": null,
        "id": 2,
        "name": "pm25",
        "units": "\u00b5g/m\u00b3"
      },
      "period": {
        "datetimeFrom": {
          "local": "2025-01-01T00:00:00-05:00",
          "utc": "2025-01-01T05:00:00Z"
        },
        "datetimeTo": {
          "local": "2026-01-01T00:00:00-05:00",
          "utc": "2026-01-01T05:00:00Z"
        },
        "interval": "1year",
        "label": "1 year"
      },
      "summary": {
        "avg": 11.995047929577648,
        "max": 69.68215906620024,
        "median": 8.108072297583625,
        "min": 0.12244618151129948,
        "q02": 0.39800725174136464,
        "q25": 3.765321499364089,
        "q75": 16.050165807207428,
        "q98": 48.012366402520044,
        "sd": 12.162999020428224
      },
      "value": 12.0
    }
  ]
}
```

