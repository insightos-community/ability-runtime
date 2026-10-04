# ability-runtime

Semantic 拆码垛联调用的 **Ability 运行时种子仓**。

把 AbilityFramework 二进制、scaffold / `ability_py` Wheel、以及 `r1pro-mujoco` 第三方 Wheel 缓存放在这里。开发者 clone + `git lfs pull` + `make setup` 之后，不必再找同事要文件，也不必再 `pip download`。

本仓 **不是** 能力源码仓，也 **不是** 打好的活动 Robot Bundle。

- 七类 Ability 源码：`semantic-ability/r1pro-ability`
- 教学 / MockArm：`mcp-playground`（可选，联调不需要）
- 活动 Bundle（Pilot / Ability zip / 本机 `python/venv`）：仍由 `semantic-framework` 的 `refresh_v050_mujoco.py` 现打

## 给谁用

Linux x86_64。Wheel 是 **cp313 manylinux**。macOS / ARM 拉下来也只能当缓存看，不能在本机起受管 Robot。

## 仓库里有什么

```
ability-runtime/
├── AbilityFramework                 # Linux x86_64 静态 ELF
├── ability_scaffold-1.2.0-*.whl     # 打包七类 Ability 用
├── ability_py-0.4.0-*.whl           # Ability Python SDK
├── Makefile                         # make setup 生成本机 .venv
└── base-bundles/r1pro-mujoco-0.5.0-dev/
    ├── bundle.yaml                  # 与 semantic-deployment 类型包一致
    └── wheels/                      # 第三方 + ability_py + websockets
```

`wheels/` 只放刷新脚本不会现打的依赖（numpy / pinocchio / ruckig / Flask 等）。产品 Wheel（Robot SDK、Ability、Skill SDK）不要放，脚本会从旁边的源码仓现打。

`cmeel_urdfdom-4.0.0-2` 需要 `libtinyxml2.so.9`，PyPI 的 `cmeel_tinyxml2` 只有 so.11。种子仓用 `scripts/seal_cmeel_native_closure.py` 把 Debian `libtinyxml2-9` 打成 `cmeel_tinyxml2_9` Wheel，并给 urdfdom 写 `$ORIGIN` RUNPATH。刷新脚本会在 Bundle 入库后跑 `import pinocchio` + 隔离加载门禁，缺 so.9 直接失败。

## 不要放什么

| 东西 | 原因 |
| --- | --- |
| `.venv/` | 路径绑死本机，clone 后 `make setup` 生成 |
| `.output/robot-bundles/` 活动包 | 含本机 Pilot、Ability zip、`python/venv`，要现打 |
| 七类 Ability 源码 / zip | 在 `r1pro-ability` |
| MockArm / phase-1..4 | 教学仓内容，联调用不上 |
| 密钥、`.env`、实例数据 | 各人自己的 |

## 怎么用

放在 `$SEMANTIC` 下，目录名保持 `ability-runtime`：

```bash
export SEMANTIC="$HOME/workspace/semantic"
git clone https://github.com/insightos-community/semantic-ability/ability-runtime.git \
  "$SEMANTIC/ability-runtime"
cd "$SEMANTIC/ability-runtime"
git lfs install
git lfs pull
make setup
```

`make setup` 会：

1. `chmod +x AbilityFramework`
2. 用本机 Python 3.13 建 `.venv`
3. 把仓库里的 `ability_scaffold` Wheel 装进去

之后刷新脚本会自己找：

- vendor：`$SEMANTIC/ability-runtime`（`AbilityFramework` + `.venv/bin/ability-scaffold`）
- Wheel 缓存：`$SEMANTIC/ability-runtime/base-bundles/r1pro-mujoco-0.5.0-dev`

旧脚本如果还只认 `mcp-playground`，可以显式传：

```bash
cd "$SEMANTIC/semantic-framework"
PYTHON313=$(uv python find 3.13)
"$PYTHON313" scripts/refresh_v050_mujoco.py build --activate --python "$PYTHON313" \
  --vendor-root "$SEMANTIC/ability-runtime" \
  --base-bundle "$SEMANTIC/ability-runtime/base-bundles/r1pro-mujoco-0.5.0-dev"
```

## 自检

```bash
make check
test -x AbilityFramework
file AbilityFramework          # 应是 ELF 64-bit x86-64，不是 LFS 指针文本
test -x .venv/bin/ability-scaffold
```

`AbilityFramework` 大约 14MB，`base-bundles/.../wheels` 大约 100MB。如果只有几十个字节，是 LFS 没拉下来，再执行 `git lfs pull`。
