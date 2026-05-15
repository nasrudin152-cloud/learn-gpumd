# 3-train-nep：训练 NEP 势

本目录用于训练 `Cu-C-O` 体系 NEP 势函数。

## 目录内文件

- `train.xyz`：训练数据
- `nep.in`：训练参数
- `nep.sh`：集群提交脚本（PBS）

## 训练前先检查

1. `train.xyz` 能正常读取，且元素体系与预期目标一致。
2. `nep.in` 中 `type` 与数据一致（当前是 `type 3 Cu C O`）。
3. `nep.sh` 中 `GPUMD_BIN` 路径正确。

## `nep.in` 关键参数

- `version 4`
  - 是什么：NEP 版本。
  - 影响：描述符与模型能力。
  - 新手起步：保持 `4`。

- `type 3 Cu C O`
  - 是什么：元素种类和顺序。
  - 影响：模型识别原子类型。
  - 新手起步：必须与训练数据完全一致。

- `cutoff 6.0 3.5`
  - 是什么：径向/角向截断。
  - 影响：精度与开销。
  - 新手起步：先用当前值；若不稳，再结合 `2-select/check_cutoff_from_trainxyz.py` 调整。

- `n_max 4 4`、`basis_size 8 8`、`l_max 4 2 0`
  - 是什么：描述符展开与基函数设置。
  - 影响：表达能力与计算成本。
  - 新手起步：先不改。

- `neuron 30`
  - 是什么：网络隐藏层宽度。
  - 影响：拟合能力与训练耗时。
  - 新手起步：先用 `30`。

- `lambda_e/lambda_f/lambda_v`
  - 是什么：能量/力/virial 损失权重。
  - 影响：训练关注重点。
  - 新手起步：
    - 有 virial 标注：`lambda_v 0.1`
    - 无 virial 标注：`lambda_v 0.0`

- `batch 1000`、`population 50`、`generation 200000`
  - 是什么：训练规模与轮次。
  - 影响：收敛速度与训练时长。
  - 新手起步：先可用较小 `generation` 快速验证流程，再拉长做正式训练。

## 最小可运行参数组合（先跑通）

若仅需先验证流程，可以在 `nep.in` 临时使用：

- `cutoff 6.0 3.5`
- `batch 500`
- `population 50`
- `generation 20000`
- `lambda_v 0.0`（仅当训练数据无 virial）

流程跑通后，再改回正式参数。

## 如何启动训练

执行目录：`/home/marunlin/gpumd/surface-reconstruction/beginner-tutorial/3-train-nep`

集群提交：

```bash
qsub nep.sh
```

或本地直接运行（确保环境与 `GPUMD_BIN` 正确）：

```bash
bash nep.sh
```

## 成功标志

- 生成 `gpumd.out` 且无报错中断
- 训练结束后得到 `nep.txt`（若未生成，优先检查 `gpumd.out`）

## 常见坑

- `type` 顺序错：会导致训练结果异常
- 训练和运行程序混用：训练用 `nep` 可执行，不是 `gpumd`
- `GPUMD_BIN` 路径失效：先在脚本里改成机器上的真实路径
