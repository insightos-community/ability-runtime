# ability-runtime

[English](README.md) | [简体中文](README.zh-CN.md)

The **Ability runtime seed repository** for Semantic depalletizing integration work. It holds the build inputs and offline dependency cache for Semantic Robot Bundles; despite the Runtime in its name, this repository is **not a running service**.

It stores the AbilityFramework binary, the scaffold / `ability_py` Wheels, and the `r1pro-mujoco` third-party Wheel cache. After clone + `git lfs pull` + `make setup`, developers no longer need to ask colleagues for files or run `pip download`.

This repo is **not** the Ability source repository, and **not** a ready-made active Robot Bundle.

- Seven Ability source trees: `semantic-ability/r1pro-ability`
- Teaching / MockArm: `mcp-playground` (optional, not needed for integration)
- Active Bundles (Pilot / Ability zip / local `python/venv`): still built on demand by `semantic-framework`'s `refresh_v050_mujoco.py`

## Who It Is For

Linux x86_64. The Wheels are **cp313 manylinux**. On macOS / ARM the checkout is only useful as a cache to inspect; you cannot start a managed Robot locally.

## What Is in the Repository

```
ability-runtime/
├── AbilityFramework                 # Linux x86_64 static ELF
├── ability_scaffold-1.2.0-*.whl     # for packing the seven Abilities
├── ability_py-0.4.0-*.whl           # Ability Python SDK
├── Makefile                         # make setup creates the local .venv
└── base-bundles/r1pro-mujoco-0.5.0-dev/
    ├── bundle.yaml                  # matches the semantic-deployment type package
    └── wheels/                      # third-party + ability_py + websockets
```

`wheels/` only holds dependencies the refresh script does not build on demand (numpy / pinocchio / ruckig / Flask, etc.). Do not add product Wheels (Robot SDK, Ability, Skill SDK); the script builds those from the sibling source repos.

`cmeel_urdfdom-4.0.0-2` needs `libtinyxml2.so.9`, while PyPI's `cmeel_tinyxml2` only ships so.11. The seed repo uses `scripts/seal_cmeel_native_closure.py` to package Debian `libtinyxml2-9` as a `cmeel_tinyxml2_9` Wheel and writes an `$ORIGIN` RUNPATH into urdfdom. After a Bundle is ingested, the refresh script runs `import pinocchio` plus an isolated-load gate; a missing so.9 fails hard.

## What Not to Put Here

| Item | Reason |
| --- | --- |
| `.venv/` | paths are bound to the local machine; `make setup` recreates it after clone |
| active bundles in `.output/robot-bundles/` | contain the local Pilot, Ability zips, and `python/venv`; must be built on demand |
| the seven Ability source trees / zips | live in `r1pro-ability` |
| MockArm / phase-1..4 | teaching-repo content, not used in integration |
| secrets, `.env`, instance data | private to each developer |
| backup `*.lfs-orig` files | not release inputs |

## Preparing the Inputs

Use quick-start steps **2.3, 5.1, 5.2**: download third-party assets, build AbilityFramework / ability-py / ability-scaffold from source, verify, and copy the results into this repository.

When preparing manually, pull only the remaining LFS assets:

```bash
git lfs pull -X "AbilityFramework,**/AbilityFramework,ability_py-*.whl,**/ability_py-*.whl,ability_scaffold-*.whl,**/ability_scaffold-*.whl"
```

Then copy the matching-version binaries and Wheels from those three source builds. The SDK Wheels are needed both at the repository root and inside the selected base bundle's `wheels/`. Public snapshots do not include these three self-produced files; do not run setup before building and copying them.

## How to Use

Place it under `$SEMANTIC`, keeping the directory name `ability-runtime`:

```bash
export SEMANTIC="$HOME/workspace/semantic"
git clone https://github.com/insightos-community/semantic-ability/ability-runtime.git \
  "$SEMANTIC/ability-runtime"
cd "$SEMANTIC/ability-runtime"
git lfs install
git lfs pull
make setup
```

`make setup` will:

1. `chmod +x AbilityFramework`
2. create `.venv` with the local Python 3.13
3. install the repo's `ability_scaffold` Wheel into it

setup requires uv and Python **3.13**, and the generated `.venv/` contains ability-scaffold.

Afterwards the refresh script finds everything on its own:

- vendor: `$SEMANTIC/ability-runtime` (`AbilityFramework` + `.venv/bin/ability-scaffold`)
- Wheel cache: `$SEMANTIC/ability-runtime/base-bundles/r1pro-mujoco-0.5.0-dev`

If an old script still only recognizes `mcp-playground`, pass the paths explicitly:

```bash
cd "$SEMANTIC/semantic-framework"
PYTHON313=$(uv python find 3.13)
"$PYTHON313" scripts/refresh_v050_mujoco.py build --activate --python "$PYTHON313" \
  --vendor-root "$SEMANTIC/ability-runtime" \
  --base-bundle "$SEMANTIC/ability-runtime/base-bundles/r1pro-mujoco-0.5.0-dev"
```

## Self-Check

```bash
make check
test -x AbilityFramework
file AbilityFramework          # should be ELF 64-bit x86-64, not LFS pointer text
test -x .venv/bin/ability-scaffold
```

`make check` only verifies that files exist; quick-start additionally validates the Wheel archives and runs an AbilityFramework version check.

`AbilityFramework` is about 14MB and `base-bundles/.../wheels` about 100MB. If they are only a few dozen bytes, LFS content was not pulled — run `git lfs pull` again.

## Usage and FAQ

The Framework refresh workflow uses these inputs to produce the activated Robot Bundle. The current cache contains Linux x86_64 / CPython 3.13 native Wheels; it is not a cross-platform dependency set.

- "invalid wheel" is usually caused by LFS pointers or a forgotten copy of the source-build outputs.
- Missing shared libraries may indicate an ABI mismatch; keep the dependencies locked by the Bundle and do not blindly upgrade individual Wheels.
- Third-party Wheels keep their embedded licenses and ship with [supplementary upstream license notices](third-party-licenses/README.md).

[Detailed seed reference](README.reference.md) · [Input checks](Makefile)

## License

Copyright 2026 InsightOS. First-party code is licensed under [Apache-2.0](LICENSE); for third-party components and assets see [NOTICE](NOTICE) and the [license scope](LICENSE_SCOPE.md).

## Build Reproduction on Three Platforms

See the [glibc, musl, and macOS build notes](README.build.md): pinned source versions, actual script entry points, tool requirements, local and CI instructions, artifact locations, and platform verification scope.
