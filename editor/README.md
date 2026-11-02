# GNSS Drift Atlas — local editor

A small local-first web map for viewing the public GeoJSON catalogue, drawing review areas, selecting intersecting features, and exporting the result.

## Run

Python 3.10+ is sufficient; no pip packages are required.

```bash
python3 editor/app/server.py
```

Open <http://127.0.0.1:8765>.

Windows:

```powershell
py editor/app/server.py
```

## Data loading

The editor requests `catalog.json` from the public `main` branch of `MAKAKAIglitch/ggns-drift-atlas`, then requests only the dataset files listed in that catalogue. The local checkout is used as a fallback if GitHub cannot be reached. Set `GNSS_DATA_OWNER`, `GNSS_DATA_REPO`, and `GNSS_DATA_BRANCH` before starting the server to point the editor at another public dataset repository.

## Selection and export

Draw one or more polygons, rectangles, or circles with the map toolbar. “Export selection” includes the drawn selection geometries plus source features intersecting any drawn shape. “Export all” exports the loaded source features. Exports are GeoJSON FeatureCollections and are downloaded by the browser; the app does not write to GitHub.

## Dependencies

- Leaflet 1.9.4 (BSD-2-Clause)
- Leaflet-Geoman Free 2.20.0 (MIT)
- Turf.js 7.4.0 (MIT)
- OpenStreetMap standard raster tiles (with visible attribution; subject to the tile usage policy)

CDN assets and the basemap require an internet connection. The Python server binds only to `127.0.0.1` and exposes no write API.
