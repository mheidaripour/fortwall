# fortwall

A least-privilege deployment layer for PHP applications, built on top of the
**Saphire** syscall-profiling pipeline. fortwall clusters an application's URLs
by their syscall footprint into a small set of php-fpm pools and enforces a
tailored allow-list per pool (via nginx routing + per-pool seccomp), as an
alternative to Saphire's single global filter — and measures the resulting
attack-surface reduction.

## Repository layout (two layers + a data contract)

```
fortwall/                # this repo
├── saphire/             # VENDORED upstream (see saphire/UPSTREAM.md)
│   ├── stage1/ stage2/ stage3/     # trace -> syscall profile -> seccomp enforce
│   ├── go/ wordpress_exploits/ CVE-2018-12613.py
│   └── run_stage*.sh  switch_to_*.sh
├── artifacts/           # DATA CONTRACT between the two layers
│   ├── stage1_output               # saphire stage1 -> stage2
│   └── stage2_out/                 # saphire stage2 -> fortwall  (stage2_out_*)
└── fortwall/            # THIS PROJECT (was "stage2.5")
    ├── src/fortwall_pool/          # installable package
    ├── tests/                      # pytest suite (incl. byte-for-byte golden tests)
    ├── data/                       # fortwall-local inputs (syscall_table, url_lists)
    ├── experiments/                # evaluation harness (mpool vs saphire pl/npl)
    ├── legacy/                     # original flat scripts, pre-refactor
    └── pyproject.toml  README.md
```

**Why this shape:** fortwall is a *sibling alternative* to Saphire's stage3, not
a later stage — its only dependency on Saphire is the `stage2_out_*` data in
`artifacts/`. Keeping Saphire vendored and pristine (not renumbered) preserves
attribution and the ability to diff/update against upstream. See
[`saphire/UPSTREAM.md`](saphire/UPSTREAM.md).

## Quick start

```bash
cd fortwall                         # the project layer
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q

# analyze a saphire stage2 output (reads ../artifacts/stage2_out/ by default)
.venv/bin/fortwall analyze --app wordpress --clusters 5
```

Run `fortwall` commands from the `fortwall/` layer directory so the relative
`../artifacts` and `data/` paths resolve. See [`fortwall/README.md`](fortwall/README.md)
for the full CLI, package details, and the old→new file mapping.
