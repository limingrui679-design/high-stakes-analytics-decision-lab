# Rebuilding the public-source studies

Cases 16–30 ship the measured observations, source identities, analytical protocol and results. **An ordinary case replay runs offline with Python 3.11–3.14 and its standard library.** Each project includes its own equations or algorithm in `study.py` and the publisher transformation in `extract.py`.

From any project directory:

```sh
python download_data.py
python prepare_data.py
python analyze.py
python build_decision_case.py
```

The first command verifies the included snapshot. The preparation step checks the primary key, row count, field order and hash. Open `outputs/report.md` for measured results and their denominators. A separate decision brief appears when the case evaluates an actionable allocation or explicit policy choice.

## Check original inputs independently

From the repository root, set a cache outside the checkout. Select a project by the directory name printed in its gallery card.

```sh
python examples/real-data-cases/source_tools/replay_extract.py \
  --project programming-hint-design --cache "$PWD/../public-source-cache" --fetch
```

The command downloads the public objects named in the project's source manifest, verifies their SHA-256 digests, runs the recorded extraction and compares the decompressed output byte for byte. For an existing cache, omit `--fetch`. Publisher services sometimes replace files behind a stable URL. A digest mismatch identifies a new source vintage. The bundled extract and its hash preserve the original analytical run. `--freeze` is a separate maintainer operation for adopting reviewed source objects and recalculating their manifest.

Most original extractors use only the standard library. The development environment for full publisher reconstruction used NumPy 2.1.3, pandas 2.2.3, SciPy 1.15.3, pypdf 6.11.0, DuckDB 2.0.1, osmium 4.3.2 and lxml. Chicago licensing and inspection files additionally use base R with `Rscript`; the stored units, quarterly labels and all statistical analysis replay without R. The alternative routing solver uses OR-Tools 9.15.6755 only to find candidate orders. The standard-library analysis subsequently checks each order and every time window independently. Use a 64-bit machine and a cache with room for multi-gigabyte source archives when rebuilding original signal, routing, drive fleet or EDGAR data.

| Case | Publisher evidence used in this analysis | Independent evaluation |
|---|---|---|
| 16 | CDC NHANES demographic and paired blood-pressure examinations | Survey strata and held-out sampling units |
| 17 | PPG-DaLiA and WESAD wrist, motion and chest signals | Frozen risk threshold on held-out people and an external study |
| 18 | Twelve Technion bank call-centre logs | Calendar holdout, observed wait and abandonment, fixed paid time |
| 19 | Original dated US Department of Labor state tables | Preserve both reporting definitions and the next issue date |
| 20 | Archived MBTA GTFS versions on one common service date | Independent label-setting and full connection-scan oracles |
| 21 | English Wikivoyage revision metadata, Wikimedia 2026-10 history dump | Seven-day mature labels and two separate hindsight ceilings |
| 22 | Olist orders, customers, sellers, items and products | Prior-quarter targeting with equal capacity in later quarters |
| 23 | All four Backblaze 2016 drive-statistics archives | Unseen serials and hardware family, daily budget, censored follow-up |
| 24 | Amazon complete routes, packages, observed sequences and travel-time matrices | Equal-move searches, equal-wall-time VRPTW benchmark, held-out depot |
| 25 | City of Chicago inspection and permit records | Historical inspection slots, full-roster bounds and prospective inclusion probabilities |
| 26 | CSEDM organizer's published evaluation and independent Refactory programming submissions | Learner folds and chronological evaluation, auditable trace and two interactive variants |
| 27 | Four issuer NAV and distribution workbooks, Federal Reserve GZ and H.15 series | Lagged allocations, matched Treasury sensitivity and monthly stress labels |
| 28 | EIA-930 reported hourly load and day-ahead forecasts | Shared dates across regions, gross-error replay and known-truth coverage |
| 29 | Accession-level SEC public filing facts and an Apple 10-K footnote | As-of dates, other-issuer holdout, forecast benchmarks and valuation sensitivity |
| 30 | Two Geofabrik OSM extracts and intervening daily changes | Full rebuild per version, version-pinned read and writer crash recovery |

Dataset terms belong to the named providers. `source-manifest.json` identifies each file actually opened, its publisher, observed checksum, and the output fields or findings derived from it.

## Recheck a host-specific benchmark

```sh
python examples/real-data-cases/source_tools/benchmark_systems.py --case transit-timetable-repair --repeats 3
python examples/real-data-cases/source_tools/benchmark_systems.py --case versioned-road-geometry --repeats 3
python examples/real-data-cases/projects/last-mile-departure-slack/benchmark_solver.py --seconds 0.5
```

Benchmark files record the measured run and can be regenerated on another host. CPU scheduling may change wall times and time-limited solver witnesses. In the official offline replay, input identities, algorithmic work, feasibility of every stored witness, regression checks and empirical results remain independently verifiable.
