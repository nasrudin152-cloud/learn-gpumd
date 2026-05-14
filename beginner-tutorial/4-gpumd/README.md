# 4-gpumd：用训练好的势跑模拟

本目录用于“运行阶段”，即把训练得到的 `nep.txt` 放到具体体系里做 GPUMD 或对照计算。

## 子目录说明

- `1-wtihCO-nep/`
  - NEP + 含 CO 体系
  - 文件：`model.xyz`、`run.in`、`nep.txt`

- `2-vacuum-nep/`
  - NEP + 真空体系
  - 文件：`model.xyz`、`run.in`、`nep.txt`、`gpumd.sh`

- `3-whitCO-dp/`
  - DeepMD/LAMMPS 对照（含 CO）
  - 文件：`1.lmp`、`1.sh`、`in.lammps`

- `4-vacuum-dp/`
  - DeepMD/LAMMPS 对照（真空）
  - 文件：`1.lmp`、`1.sh`、`in.lammps`

## 图片说明（你新增的 4 张图）

- `1-wtihCO-nep/1.png`：GPUMD 跑得到的结果图
- `2-vacuum-nep/2.png`：GPUMD 跑得到的结果图
- `3-whitCO-dp/3.jpg`：作者论文中的对应图片
- `4-vacuum-dp/4.jpg`：作者论文中的对应图片

对应关系总结：`1/2` 是 GPUMD 结果，`3/4` 是论文图片。

## 核心要求：`model.xyz`

NEP 路线运行时必须有：

1. `model.xyz`（结构）
2. `run.in`（运行参数）
3. `nep.txt`（势文件）

这三者缺一不可。

## 推荐运行顺序（NEP）

### A. 先跑 `2-vacuum-nep`（已有 `gpumd.sh`）

执行目录：`/home/marunlin/gpumd/surface-reconstruction/beginner-tutorial/4-gpumd/2-vacuum-nep`

1. 将 `3-train-nep` 最新训练得到的 `nep.txt` 复制覆盖本目录 `nep.txt`
2. 检查 `run.in` 中 `potential ./nep.txt` 路径
3. 提交任务：

```bash
qsub gpumd.sh
```

### B. 再跑 `1-wtihCO-nep`

该目录当前无 `gpumd.sh`。做法：

1. 从 `2-vacuum-nep/gpumd.sh` 复制一份到 `1-wtihCO-nep/`
2. 按你的机器修改 `CUDA_VISIBLE_DEVICES` 和 `GPUMD_BIN`
3. 在 `1-wtihCO-nep/` 提交运行

## 运行前检查清单

- `run.in` 里的 `potential ./nep.txt` 是否正确
- `model.xyz` 是否存在
- `model.xyz` 元素体系是否与 `nep.txt` 对应（`Cu C O`）
- 先小步数测试，再做长时间运行

## 成功标志

- `gpumd.out` 无错误退出
- 产出正常的热力学与轨迹结果文件

## DP 对照组用途

`3-whitCO-dp` 和 `4-vacuum-dp` 是对照路线（LAMMPS + DeepMD），用于和 NEP 结果做趋势比较，不影响 NEP 主流程。
