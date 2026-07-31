# Vendored: Saphire

This directory contains a **vendored copy** of the Saphire project, on top of
which `fortwall/` is built. It is included here so the full evaluation pipeline
(stage1 trace → stage2 syscall profile → stage3 seccomp enforcement) is
reproducible alongside fortwall.

## Origin

Saphire — *"Saphire: Sandboxing PHP Applications with Tailored System Call
Allowlists"*, Alexander Bulekov, Rasoul Jahanshahi, Manuel Egele.
USENIX Security Symposium, 2020.

- Upstream repo: https://github.com/BUseclab/saphire (branch `main`)
- Vendored commit: **TODO — pin the exact commit SHA** (repo has 2 commits on
  `main`; record the one you copied, e.g. `git -C saphire log -1` if you cloned it)
- License: **MIT** — Copyright (c) 2021 BUseclab. Redistribution inside this repo
  is permitted provided the notice is retained; see [`./LICENSE`](./LICENSE).
  (Because it's MIT, a vendored copy is fine — no submodule required.)

## Contents (upstream)

- `stage1/` — application tracing (TR_strace, TE_xdebug, static analysis)
- `stage2/` — builds the per-application syscall profile (`stage2_out_*`)
- `stage3/` — PHP seccomp extension that enforces one global allow-list
- `go/`, `wordpress_exploits/`, `CVE-2018-12613.py` — exploit/validation harness
- `run_stage{1,2,3}.sh` — pipeline drivers (they reference `~/stage2`, `~/stage3`
  on the host, not repo-relative paths)
- `switch_to_*.sh` — webroot app-switch helpers

## Local modifications

Track anything changed from pristine upstream here so "theirs vs ours" stays
clear:

- **Upstream (pristine):** `switch_to_wordpress.sh`, `switch_to_phpmyadmin.sh`
- **Added locally (not from upstream):** `switch_to_drupal.sh`,
  `switch_to_joomla.sh`, `switch_to_magento.sh`, `switch_to_moodle.sh`,
  `switch_to_prestashop.sh`
- (add further local edits as you make them)

## Relationship to fortwall

fortwall consumes only Saphire's **stage2 output** (`../artifacts/stage2_out/`)
and replaces stage3 with per-URL php-fpm pooling. Do **not** renumber or rename
Saphire's stages — keeping them pristine is what lets you diff/update against
upstream and attribute correctly.
