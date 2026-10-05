#!/usr/bin/env python3
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

"""把 Debian tinyxml2 soname 9 打进种子 Wheel，并给 urdfdom 4.0 写 $ORIGIN RUNPATH。

cmeel_urdfdom-4.0.0-2 的 DT_NEEDED 是 libtinyxml2.so.9，PyPI 上的
cmeel_tinyxml2 只有 so.11。不把 so.9 放进 Bundle 闭包，无系统库的机器上
`import pinocchio` / grasp Worker 会秒退。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

WHEEL_NAME = "cmeel_tinyxml2_9-9.0.0-0-py3-none-manylinux_2_28_x86_64.whl"
DIST_NAME = "cmeel_tinyxml2_9"
VERSION = "9.0.0"
URDFDOM_WHEEL = "cmeel_urdfdom-4.0.0-2-py3-none-manylinux_2_28_x86_64.whl"
DEB_NAME = "libtinyxml2-9_9.0.0+dfsg-3.1_amd64.deb"
DEB_URLS = (
    f"https://mirrors.tuna.tsinghua.edu.cn/debian/pool/main/t/tinyxml2/{DEB_NAME}",
    f"https://mirrors.aliyun.com/debian/pool/main/t/tinyxml2/{DEB_NAME}",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def wheels_dir(root: Path | None = None) -> Path:
    base = root or repo_root()
    return base / "base-bundles/r1pro-mujoco-0.5.0-dev/wheels"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def download_deb(dest: Path) -> Path:
    last_error: Exception | None = None
    for url in DEB_URLS:
        try:
            urllib.request.urlretrieve(url, dest)
            return dest
        except Exception as error:  # noqa: BLE001 — 镜像失败就换下一个
            last_error = error
    raise RuntimeError(f"下载 {DEB_NAME} 失败: {last_error}")


def extract_tinyxml2_so9(deb: Path, dest_dir: Path) -> tuple[Path, Path]:
    extract = dest_dir / "deb"
    extract.mkdir()
    subprocess.check_call(["ar", "x", str(deb)], cwd=extract)
    data = next(extract.glob("data.tar.*"))
    subprocess.check_call(["tar", "-xf", str(data), "-C", str(extract)])
    lib = extract / "usr/lib/x86_64-linux-gnu"
    so9 = lib / "libtinyxml2.so.9"
    so900 = lib / "libtinyxml2.so.9.0.0"
    if not so900.is_file():
        raise RuntimeError(f"deb 缺少 libtinyxml2.so.9.0.0: {lib}")
    if so9.is_symlink() or so9.is_file():
        pass
    else:
        raise RuntimeError(f"deb 缺少 libtinyxml2.so.9: {lib}")
    return so9, so900


def write_wheel(so9: Path, so900: Path, dest: Path) -> Path:
    build = dest.parent / f".{dest.name}.build"
    if build.exists():
        shutil.rmtree(build)
    lib = build / "cmeel.prefix/lib"
    lib.mkdir(parents=True)
    # 两个都写成普通文件，避免 zip 丢 symlink、安装后变成悬空链接。
    payload = so900.read_bytes()
    (lib / "libtinyxml2.so.9.0.0").write_bytes(payload)
    (lib / "libtinyxml2.so.9").write_bytes(payload)

    dist = build / f"{DIST_NAME}-{VERSION}.dist-info"
    dist.mkdir()
    (dist / "METADATA").write_text(
        "Metadata-Version: 2.1\n"
        f"Name: {DIST_NAME.replace('_', '-')}\n"
        f"Version: {VERSION}\n"
        "Summary: tinyxml2 soname 9 for cmeel_urdfdom 4.0 (Debian libtinyxml2-9)\n"
        "License: zlib\n",
        encoding="utf-8",
    )
    (dist / "WHEEL").write_text(
        "Wheel-Version: 1.0\n"
        "Generator: semantic-ability-runtime\n"
        "Root-Is-Purelib: false\n"
        "Tag: py3-none-manylinux_2_28_x86_64\n",
        encoding="utf-8",
    )
    (dist / "top_level.txt").write_text("cmeel.prefix\n", encoding="utf-8")

    records: list[str] = []
    for path in sorted(build.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(build).as_posix()
        records.append(f"{rel},sha256={sha256_file(path)},{path.stat().st_size}")
    records.append(f"{DIST_NAME}-{VERSION}.dist-info/RECORD,,")
    (dist / "RECORD").write_text("\n".join(records) + "\n", encoding="utf-8")

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(build.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(build).as_posix())
    shutil.rmtree(build)
    return dest


def pack_tinyxml2_9(directory: Path) -> Path:
    with tempfile.TemporaryDirectory(prefix="tinyxml2-9-") as tmp:
        tmp_path = Path(tmp)
        deb = download_deb(tmp_path / DEB_NAME)
        so9, so900 = extract_tinyxml2_so9(deb, tmp_path)
        return write_wheel(so9, so900, directory / WHEEL_NAME)


def elf_runpath(path: Path) -> str:
    output = subprocess.check_output(["readelf", "-d", str(path)], text=True)
    lines = [
        line
        for line in output.splitlines()
        if "(RPATH)" in line or "(RUNPATH)" in line
    ]
    return "\n".join(lines)


def patch_urdfdom_wheel(wheel: Path) -> bool:
    """给 wheel 内 liburdfdom_*.so* 写 RUNPATH=$ORIGIN。已有则跳过。"""
    with tempfile.TemporaryDirectory(prefix="urdfdom-rpath-") as tmp:
        root = Path(tmp) / "wheel"
        with zipfile.ZipFile(wheel) as archive:
            archive.extractall(root)
        changed = False
        for so in sorted(root.glob("cmeel.prefix/lib/liburdfdom_*.so*")):
            if not so.is_file():
                continue
            current = elf_runpath(so)
            if "$ORIGIN" in current:
                continue
            os.chmod(so, 0o755)
            subprocess.check_call(["patchelf", "--set-rpath", "$ORIGIN", str(so)])
            os.chmod(so, 0o644)
            changed = True
        if not changed:
            return False

        dist_infos = list(root.glob("*.dist-info"))
        if len(dist_infos) != 1:
            raise RuntimeError(f"urdfdom wheel dist-info 异常: {dist_infos}")
        records: list[str] = []
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel.endswith("/RECORD") or rel.endswith(".dist-info/RECORD"):
                continue
            records.append(f"{rel},sha256={sha256_file(path)},{path.stat().st_size}")
        records.append(f"{dist_infos[0].name}/RECORD,,")
        (dist_infos[0] / "RECORD").write_text("\n".join(records) + "\n", encoding="utf-8")

        tmp_wheel = wheel.with_suffix(".whl.tmp")
        with zipfile.ZipFile(tmp_wheel, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(root).as_posix())
        tmp_wheel.replace(wheel)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wheels-dir",
        type=Path,
        default=None,
        help="默认 ability-runtime 种子仓 wheels/",
    )
    args = parser.parse_args()
    directory = args.wheels_dir or wheels_dir()
    if not directory.is_dir():
        print(f"没有 wheels 目录: {directory}", file=sys.stderr)
        return 1
    packed = pack_tinyxml2_9(directory)
    print(f"wrote {packed} ({packed.stat().st_size} bytes)")
    urdfdom = directory / URDFDOM_WHEEL
    if not urdfdom.is_file():
        print(f"缺少 {URDFDOM_WHEEL}，跳过 RUNPATH", file=sys.stderr)
        return 1
    if patch_urdfdom_wheel(urdfdom):
        print(f"patched RUNPATH $ORIGIN in {urdfdom.name}")
    else:
        print(f"{urdfdom.name} 已有 $ORIGIN RUNPATH")
    return 0


if __name__ == "__main__":
    sys.exit(main())
