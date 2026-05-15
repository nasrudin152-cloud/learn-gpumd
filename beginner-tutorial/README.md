# beginner-tutorial：从数据筛选到 GPUMD 运行的完整流程

本目录是当前项目的教学版工作流，严格按四个阶段组织：

1. `1-data`：数据来源与说明
2. `2-select`：从十几万帧中筛选约 3000 帧
3. `3-train-nep`：训练 NEP 势
4. `4-gpumd`：使用训练得到的 `nep.txt` 在 GPUMD 中跑模拟

---

## 阶段 1：`1-data`（数据来源）

- 入口文件：`1-data/README.md`
- 数据链接：`https://zenodo.org/records/11544001`
- 对应论文：`Reactant-Induced Dynamic Active Sites on Cu Catalysts during the Water–Gas Shift Reaction`
- 说明：`1-data` 逻辑等同主仓库 `Dataset/`，本教学目录不复制整套大文件

**成功标志**

- 确认数据来源、下载位置，以及本地数据目录与教程目录的关系

---

## 阶段 2：`2-select`（数据筛选）

这一阶段的目标是：把原始大规模数据整理并挑选到约 `3000` 帧，供后续 NEP 训练。

### 关键内容

- `2-select/merge_to_gpumd_xyz.py`：将 DeepMD/DPGEN 风格数据整理为 GPUMD 可用 `xyz`
- `2-select/check_cutoff_from_trainxyz.py`：辅助检查/处理训练数据
- `gpumdkit 203`：`Sample structures by neptrain`，用于从大量结构中抽样挑选代表性数据

### 该阶段任务

1. 先完成格式整理，得到可用的 `xyz` 数据。
2. 使用 `gpumdkit` 的 `203` 功能（`Sample structures by neptrain`）进行筛选。
3. 将十几万帧缩减到约 `3000` 帧。

**成功标志**

- 得到可直接用于训练的精简数据集（如 `selected.xyz` 一类结果）

---

## 阶段 3：`3-train-nep`（训练 NEP）

这一阶段使用筛选后的数据训练势函数。

### 已整理文件

- `3-train-nep/nep.in`：训练参数输入
- `3-train-nep/gpumd.sh`：提交/运行脚本
- `3-train-nep/nep.txt`：训练输出势文件（示例）

### 对照文件（保留）

- `3-train-nep/1.sh`
- `3-train-nep/in.lammps`
- `3-train-nep/1.lmp`
- `3-train-nep/log.lammps`

**成功标志**

- 训练结束后生成可用的 `nep.txt`

---

## 阶段 4：`4-gpumd`（用 GPUMD 跑训练后的势）

这一阶段将训练产物用于分子动力学运行。

### 已整理文件

- `4-gpumd/model.xyz`：运行所需结构文件
- `4-gpumd/run.in`：GPUMD 运行输入
- `4-gpumd/gpumd.sh`：提交/运行脚本
- `4-gpumd/nep.txt`：势文件（建议替换为阶段 3 新训练输出）

### 运行前检查

1. `run.in` 中 `potential ./nep.txt` 路径正确。
2. `model.xyz` 存在且元素体系与 `nep.txt` 一致。
3. 先小步数试跑，再切换到正式步数。

**成功标志**

- `gpumd.out` 无报错，热力学输出与轨迹文件正常生成

---

## 最短执行路线

1. 读 `1-data/README.md`，确认数据来源与本地数据位置。
2. 在 `2-select` 完成格式整理 + `gpumdkit 203`（`Sample structures by neptrain`）筛选。
3. 在 `3-train-nep` 训练并得到新的 `nep.txt`。
4. 将新的 `nep.txt` 放到 `4-gpumd`，配合 `model.xyz` 与 `run.in` 运行 GPUMD。
