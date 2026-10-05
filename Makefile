# Copyright 2026 InsightOS
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Ability 运行时种子仓：AF 二进制 + scaffold + 第三方 Wheel 缓存。
# .venv 本机生成，不要提交。

PYTHON313 ?= $(shell uv python find 3.13 2>/dev/null)
SCAFFOLD_WHEEL := ability_scaffold-1.2.0-py3-none-any.whl

.PHONY: setup check

setup: ## 用仓库里的 scaffold Wheel 生成本机 .venv
	@test -n "$(PYTHON313)" || (echo "找不到 Python 3.13。先执行: uv python install 3.13"; exit 1)
	chmod +x AbilityFramework
	"$(PYTHON313)" -m venv .venv
	.venv/bin/pip install -U pip
	.venv/bin/pip install "$(SCAFFOLD_WHEEL)"
	test -x AbilityFramework
	test -x .venv/bin/ability-scaffold

check: ## 核对刷新脚本需要的文件都在
	test -f AbilityFramework
	test -f ability_scaffold-1.2.0-py3-none-any.whl
	test -f ability_py-0.4.0-py3-none-any.whl
	test -f base-bundles/r1pro-mujoco-0.5.0-dev/bundle.yaml
	test -d base-bundles/r1pro-mujoco-0.5.0-dev/wheels
	test -f base-bundles/r1pro-mujoco-0.5.0-dev/wheels/ability_py-0.4.0-py3-none-any.whl
	test -f base-bundles/r1pro-mujoco-0.5.0-dev/wheels/websockets-17.0.1-cp313-cp313-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl
	test -f base-bundles/r1pro-mujoco-0.5.0-dev/wheels/numpy-2.3.5-cp313-cp313-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl
	test -f base-bundles/r1pro-mujoco-0.5.0-dev/wheels/cmeel_tinyxml2_9-9.0.0-0-py3-none-manylinux_2_28_x86_64.whl
	@echo "ability-runtime 种子文件齐全"
