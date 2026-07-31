# fortwall-pool (stage 2.5)

Cluster a PHP application's URLs by their **syscall footprint** into a small set
of least-privilege **php-fpm pools**, generate the nginx + php-fpm configuration
to route and sandbox each pool, and measure the resulting attack-surface
reduction against baselines (saphire, sysfilter).

This is a refactor of the original flat script collection into an installable,
tested Python package. **Behavior is preserved** — the config generators
reproduce the previously committed artifacts byte-for-byte (see the golden
tests), and the analysis math is unchanged.

## Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"      # runtime + test deps
```

This exposes the `fortwall` console command.

## CLI

```bash
# Cluster + score a stage2_out file and print the analysis report
fortwall analyze --app phpmyadmin --clusters 5

# Per-URL SP/SN baseline (the former saphire.py)
fortwall baseline --app wordpress

# Generate + deploy a pooling mode (use --dry-run to preview system changes)
fortwall switch --mode mpool --app wordpress -p 7 --dry-run
fortwall switch --mode saphire --app wordpress
fortwall switch --mode default

# Turn analysis stdout into LaTeX / Markdown result tables
fortwall analyze --app phpmyadmin --clusters 5 | fortwall report
```

`--syscall-table` defaults to `data/syscall_table/unistd_64_.h`.
`analyze`/`baseline` default their input to `../artifacts/stage2_out/stage2_out_<app>`
(the saphire->fortwall data contract) unless `--file` is given. `switch` still
reads/writes the on-host path `/home/paper/stage2_out_<app>` for deployment. Run
`fortwall` from the `fortwall/` layer directory so the relative `../artifacts`
and `data/` paths resolve.

## Metrics

* **SP%** — share of all `TOTAL_SYSCALLS` (333) blocked: `(TOTAL - |profile|)/TOTAL`.
* **SN%** — share of the `SN_BASE` (20) sensitive syscalls blocked:
  `(SN_BASE - |profile ∩ sensitive|)/SN_BASE`.

## Package layout

```
src/fortwall_pool/
├── config.py         # all paths + constants (was hardcoded everywhere)
├── syscalls.py       # syscall table + sensitive-syscall classification
├── urlmap.py         # parse stage2_out, categorize, intersection
├── clustering.py     # Jaccard + agglomerative clustering into pools
├── metrics.py        # SP% / SN% math
├── pipeline.py       # single end-to-end pool-planning orchestration
├── generate/         # pure config generation (nginx, php-fpm, stage2_out)
├── deploy/           # side effects: system.py (Deployer, dry-run) + modes.py
├── report.py         # analysis stdout -> LaTeX/Markdown tables
└── cli.py            # unified `fortwall` entrypoint

data/        # inputs: stage2_out/, url_lists/, syscall_table/
generated/   # (gitignored) artifacts produced by `fortwall switch`
backups/     # (gitignored) system config captured before deployment
native/seccomp/  # intrsec-seccomp.c seccomp-bpf enforcement stub
experiments/ # benchmark scripts, logs, result CSVs
legacy/      # original scripts, kept for reference (superseded by src/)
tests/       # pytest suite incl. byte-for-byte golden config tests
```

## Old → new mapping

| Original file            | Now lives in                                             |
|--------------------------|----------------------------------------------------------|
| `intersection.py`        | `urlmap.py` + `generate/` + `deploy/system.py`           |
| `cluster.py`             | `clustering.py`                                           |
| `sen_syscalls.py`        | `syscalls.py` (+ analysis in `pipeline.py`/`cli.py`)     |
| `saphire.py`             | `metrics.py` (`category_metrics`) + `fortwall baseline`  |
| `urlanalyze.py`          | `pipeline.build_pool_plan`                                |
| `switch.py`              | `deploy/modes.py` + `fortwall switch`                    |
| `report.py`              | `report.py` (packaged) + `fortwall report`               |
| `pools_expe.py`          | `experiments/`                                           |

## Testing

```bash
.venv/bin/python -m pytest -q
```

The suite includes **golden tests** that assert the nginx/php-fpm/url-map
renderers reproduce the committed reference artifacts exactly.

## Preserved quirks (intentional, for parity)

Behavior-preserving refactor — one latent quirk in the original is kept and
documented rather than "fixed", so output stays identical:

1. **www.conf `pm.max_children`** is not rewritten (the original condition
   lacked a trailing newline); the per-pool configs do rewrite it.

### Fixed bugs (diverges from the original on purpose)

- **Clustering "Max of sensitive syscalls" (ΔSN)** — the original intersected an
  int set with a string-keyed dict, so ΔSN was always `0.00%`. Now
  `clustering.diagnostics_lines()` uses the sensitive syscall *numbers*, so ΔSN
  reflects how many sensitive syscalls a pool actually adds to a member URL
  (e.g. up to 40–45% on some pools).
- **Report cluster-index misalignment** — the SP/SN lines were 0-based over all
  pools while the ΔSP/ΔSN diagnostics were 1-based over clustered pools only, so
  the corrected ΔSN landed in the wrong table row (and the first clustered
  pool's value was dropped into the hardcoded-zero "Category 1" row).
  `pipeline.build_pool_plan` now numbers the clustered pools starting after the
  dedicated pools (`first_pool_number`), so ΔSP/ΔSN align with SP/SN in the
  report table.
```
