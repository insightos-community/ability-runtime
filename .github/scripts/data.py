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

import os, shutil, subprocess, zipfile, json
from pathlib import Path
root=Path.cwd(); out=root/'.output/payload'
asset=os.environ['COMPONENT']=='mujoco-asset'
allowed={'robot','scene','assets','asset-catalog.v1.json'} if asset else {'base-bundles'}
for name in subprocess.check_output(['git','ls-files','-z'],text=True).split('\0'):
 if not name or Path(name).parts[0] not in allowed:continue
 p=root/name
 if p.is_symlink():raise SystemExit('Unexpected symlink')
 if p.suffix=='.whl':
  with zipfile.ZipFile(p) as z:
   if z.testzip():raise SystemExit('Corrupt vendored wheel')
 target=out/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
