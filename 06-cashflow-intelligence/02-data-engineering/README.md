# 02-data-engineering

Code that moves data through the `01-data` layers. Scheduling and orchestration of this code belongs in `16-orchestration`; this folder holds only the logic.

| Folder | Script | Reads | Writes |
|---|---|---|---|
| `01-ingestion` | `generate_raw_data.py` | none (synthetic) | `01-data/01-raw` |
| `02-cleaning` | `clean_and_validate.py` | `01-raw` | `01-data/02-staging` |
| `03-transformation` | `reconcile_and_process.py` | `02-staging` | `01-data/03-processed` |
| `06-pipeline-tasks` | `run_phase06_data_pipeline.py` | runs the three above, in order | n/a |

## Run everything

```powershell
python .\02-data-engineering\06-pipeline-tasks\run_phase06_data_pipeline.py
```

Add `--regenerate` to rebuild the synthetic raw data first. Without it, existing raw data is left untouched because raw is immutable.

## Conventions

- Every script resolves its default paths from **its own file location**, so it works from any terminal folder. Explicit `--rawdir` / `--stagingdir` / `--outdir` flags still override.
- The ground-truth issues log is read only inside clearly separated evaluation functions, never in cleaning or matching logic.
- Scripts that evaluate against ground truth write those results to separate files marked test-only.

## Not yet populated

`04-feature-engineering` and `05-validation` are empty for now. Validation rules currently live inside each stage; they can be lifted into `05-validation` once more than one consumer needs them.
