# 2-select：数据整理与筛选（十几万帧 -> 约 3000 帧）

本目录负责两件事：

1. 将 DeepMD/DPGEN 风格数据整理为 GPUMD 可用的 `xyz`
2. 使用 `gpumdkit 203`（`Sample structures by neptrain`）进行结构抽样筛选

## 目录内文件

- `merge_to_gpumd_xyz.py`：合并与格式转换脚本
- `nep89.txt`：现有势文件（可用于相关测试）

## 步骤 1：把 `Dataset` 整理成 `xyz`

执行目录：`/home/marunlin/gpumd/surface-reconstruction/beginner-tutorial/2-select`

```bash
python3 merge_to_gpumd_xyz.py /home/marunlin/gpumd/surface-reconstruction/Dataset \
  --train train.xyz \
  --test test.xyz \
  --all all.xyz
```

如果需要同时输出 virial（前提是源数据有 `virial.npy`）：

```bash
python3 merge_to_gpumd_xyz.py /home/marunlin/gpumd/surface-reconstruction/Dataset \
  --train train.xyz \
  --test test.xyz \
  --all all.xyz \
  --with-virial
```

### 这一步检查点

- 终端出现 `Done.`、`train frames = ...`、`test frames = ...`
- 目录下生成 `train.xyz`、`test.xyz`（和可选 `all.xyz`）

## 步骤 2：使用 `gpumdkit 203` 做抽样

在 `gpumdkit` 中使用功能：

- `203` -> `Sample structures by neptrain`

目标是从十几万帧中抽样到约 `3000` 帧，形成后续 `3-train-nep` 训练集。

> 本目录不强制固定 `gpumdkit` 命令写法，以本地安装方式和界面为准。

### 这一步检查点

- 得到规模约 `3000` 帧的筛选结果集
- 筛选结果可被后续 NEP 训练读取（通常为 `xyz`）

## 常见问题

- 报错 `No valid dataset dirs found`：检查输入路径是否指向 `Dataset`
- 帧数异常少：检查 `Dataset` 下是否有完整 `set.000`、`type.raw`、`type_map.raw`
