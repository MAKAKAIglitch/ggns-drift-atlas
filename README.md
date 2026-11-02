# GNSS Drift Atlas

**An open GeoJSON catalogue and local-first map editor for documenting GNSS position anomalies.**

GNSS Drift Atlas is intended to make it easy to review, organise, and exchange geospatial observations in an open format. The public dataset records positions reported by GNSS receivers and separately stores user-drawn review geometries. A record is an observation, not proof of intentional spoofing or of the location of a transmitter.

## Repository layout

```text
.
├── catalog.json                 # Index loaded first by the editor
├── data/
│   └── atlas.geojson             # Public GeoJSON FeatureCollection
├── schema/
│   └── feature.schema.json       # Project feature-property schema
└── editor/                       # Local editor (maintained on the `editor` branch)
```

## Data model

The public dataset is a standard **GeoJSON FeatureCollection** using WGS 84 longitude/latitude coordinates in the order `[longitude, latitude]` (RFC 7946).

Supported project feature types:

- `reported_fix` — a position reported by a GNSS receiver during an observation. It must not be described as a verified physical receiver location.
- `review_zone` — a user-drawn polygon or multipolygon used to organise or review records. It is not, by itself, a measured coverage boundary.

Recommended properties:

| Property | Meaning |
| --- | --- |
| `id` | Stable, unique feature identifier |
| `feature_type` | `reported_fix` or `review_zone` |
| `observed_at` | Observation time in ISO 8601 UTC, when known |
| `verification` | `unverified`, `corroborated`, or `rejected` |
| `confidence` | `low`, `medium`, or `high`; omit when unknown |
| `source_type` | `manual`, `public_report`, or `device_log` |
| `notes` | Short non-personal context |

Unknown values should be omitted rather than guessed. Keep the original observation separate from interpretations added later.

## Public-data hygiene

- Do not add observer home/work locations, personal names, contact details, device serial numbers, account identifiers, or other identifying information.
- Do not add a receiver's independently verified physical location to a public record unless there is a clear, documented reason and appropriate consent. The dataset is designed around the **position reported by the receiver**.
- Do not infer or publish transmitter / installation locations from reported positions.
- Mark new reports `unverified` until independently corroborated. An unusual GNSS position alone does not establish spoofing, jamming, or its source.
- Avoid publishing exact personal movement traces. Consider reducing timestamp precision where exact timing is not needed.

## Using the editor

The local web editor is developed on the separate [`editor` branch](https://github.com/MAKAKAIglitch/ggns-drift-atlas/tree/editor). It reads `catalog.json` first and then loads the GeoJSON files listed there. Public data is fetched from the repository's `main` branch; if the remote repository is not reachable, the editor can use the local checkout as a fallback.

After switching to `editor`, start it with:

```bash
python3 editor/app/server.py
```

Then open <http://127.0.0.1:8765> in a browser. On Windows, use:

```powershell
py editor/app/server.py
```

The editor uses Leaflet and Leaflet-Geoman from pinned CDN releases and OpenStreetMap tiles, so an internet connection is needed for the map libraries and basemap. The Python server itself uses only the Python standard library and listens on loopback (`127.0.0.1`).

## Updating the catalogue

1. Add or update GeoJSON features in `data/atlas.geojson`.
2. Validate the file as RFC 7946 GeoJSON and check every coordinate order.
3. Update `catalog.json` when dataset paths or the dataset version change.
4. Submit changes through a pull request so records can be reviewed before publication.

## Licensing

- Dataset: **CC BY 4.0** — see [`LICENSE-DATA.md`](LICENSE-DATA.md).
- Editor code: **MIT** — see [`editor/LICENSE`](https://github.com/MAKAKAIglitch/ggns-drift-atlas/blob/editor/editor/LICENSE) on the `editor` branch.

## Project status

Early scaffold. The initial GeoJSON collection is intentionally empty; no coordinates are fabricated or preloaded.
