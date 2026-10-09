# ability-runtime

[English](README.md) | [简体中文](README.zh-CN.md)

Semantic 拆码垛联调用的 **Ability 运行时种子仓**。它是 Semantic Robot Bundle 的构建输入与离线依赖缓存；虽然名称含 Runtime，本仓库**不是运行中的服务**。

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
| 备份 `*.lfs-orig` | 不属于发布输入 |

## 准备输入

使用 quick-start 的 **2.3、5.1、5.2** 步骤：下载第三方资产，从源码构建 AbilityFramework / ability-py / ability-scaffold，校验后复制到本仓库。

手动准备时，仅拉取剩余 LFS 资产：

```bash
git lfs pull -X "AbilityFramework,**/AbilityFramework,ability_py-*.whl,**/ability_py-*.whl,ability_scaffold-*.whl,**/ability_scaffold-*.whl"
```

随后从上述三个源码构建中复制匹配版本的二进制与 Wheel。SDK Wheel 既需要放在根目录，也需要放入选定 base bundle 的 `wheels/`。公开快照不包含这三类自产文件，完成构建和复制前不要执行 setup。

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

setup 需要 uv 与 Python **3.13**，生成的 `.venv/` 包含 ability-scaffold。

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

`make check` 只检查文件存在；quick-start 还会验证 Wheel 压缩包并执行 AbilityFramework 版本检查。

`AbilityFramework` 大约 14MB，`base-bundles/.../wheels` 大约 100MB。如果只有几十个字节，是 LFS 没拉下来，再执行 `git lfs pull`。

## 使用与常见问题

Framework 刷新工作流使用这些输入生成激活的 Robot Bundle。当前缓存包含 Linux x86_64 / CPython 3.13 原生 Wheel，不是一套跨平台依赖集合。

- “invalid wheel”常见原因是 LFS 指针或遗漏源码产物复制。
- 共享库缺失可能是 ABI 不匹配，应保留 Bundle 锁定的依赖，不要盲目升级单个 Wheel。
- 第三方 Wheel 保留内嵌许可，并提供[补充上游许可声明](third-party-licenses/README.md)。

[详细种子参考](README.reference.md) · [输入检查](Makefile)

## 许可证

Copyright 2026 InsightOS。自有代码采用 [Apache-2.0](LICENSE)；第三方组件与资产请查看 [NOTICE](NOTICE) 和[许可范围](LICENSE_SCOPE.md)。

## 三个平台的构建复现

参见 [glibc、musl 与 macOS 构建说明](README.build.md)：包含已锁定的源码版本、实际脚本入口、工具要求、本地与 CI 指令、产物位置和平台验证范围。
