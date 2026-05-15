# NepTrain 主动学习工作流配置说明

本目录包含 NepTrain（主动学习训练 NEP 势函数）所需的 `job.yaml` 配置模板文件。  
本文档详细说明配置文件结构、各参数含义、使用流程，以及 NepTrain 与 DP-GEN 的对比。

---

## 目录

1. [主动学习原理](#1-主动学习原理)
2. [NepTrain 与 DP-GEN 的对比](#2-neptrain-与-dp-gen-的对比)
3. [整体工作流程](#3-整体工作流程)
4. [文件结构要求](#4-文件结构要求)
5. [顶层参数详解](#5-顶层参数详解)
6. [nep 段（NEP 训练）](#6-nep-段nep-训练)
7. [dft 段（DFT 标注）](#7-dft-段dft-标注)
8. [gpumd 段（采样模拟）](#8-gpumd-段采样模拟)
9. [select 段（结构筛选）](#9-select-段结构筛选)
10. [limit 段（数据过滤）](#10-limit-段数据过滤)
11. [快速开始](#11-快速开始)

---

## 1. 主动学习原理

### 1.1 什么是主动学习

主动学习（Active Learning）是一种"让模型决定学什么"的策略。与传统的被动学习（人工预先准备所有训练数据）不同，主动学习让机器学习模型在训练过程中主动识别自身的薄弱区域，有针对性地请求新的标注数据。

在原子模拟领域，训练机器学习势函数（MLP）面临的核心矛盾是：
- **DFT 计算昂贵**：一次 DFT 计算可能耗时数小时到数天
- **结构空间巨大**：温度、压力、缺陷、表面等组合产生的构型空间是天文数字
- **盲目采样低效**：随机生成的结构中，大部分对模型改进的贡献极小

主动学习通过"探索→评估→标注→训练"的迭代循环，每轮只计算"最有价值"的结构，以最小的 DFT 计算代价最大化模型精度提升。

### 1.2 NEP 势函数的主动学习流程

NEP（Neuroevolution Potential）是一种基于神经网络的原子间势函数，由 GPUMD 软件包实现，其特点是训练速度极快（GPU 加速）且推理效率高。

NepTrain 的主动学习循环如下：

1. **GPUMD 探索阶段**：使用当前最优的 `nep.txt` 势函数，在不同温度/压力条件下进行分子动力学模拟，让体系自然演化，探索结构空间中的新区域。

2. **结构筛选阶段（Select）**：从 GPUMD 生成的轨迹中，利用描述符空间中的距离度量，识别出与现有训练集差异最大的结构。这些结构代表了势函数"不确定性"最高的区域——即模型最需要学习的地方。

3. **DFT 标注阶段**：将筛选出的代表性结构送入 VASP 等 DFT 软件，计算其精确的能量、原子力和应力张量。这些作为"标准答案"用于后续训练。

4. **NEP 训练阶段**：将新标注的数据合并到训练集中，重新训练（或续训）NEP 势函数，生成精度更高的新 `nep.txt`。

5. **迭代收敛**：重复以上循环。随着训练集不断扩充，势函数对结构空间的覆盖越来越全面，筛选出的新结构越来越少，直到收敛。

### 1.3 为什么有效

- **效率**：每轮只需标注 ~50 个结构（而非数千个），DFT 成本大幅降低
- **质量**：每个被选中的结构都有最大信息量，训练集紧凑且无冗余
- **自适应**：模型自动发现自身盲区，无需人工判断哪些结构重要
- **可控**：通过 `step_times` 渐进增大模拟步数，从保守探索到大胆延伸

---

## 2. NepTrain 与 DP-GEN 的对比

NepTrain 和 DeepMD-kit 的 DP-GEN 都是主动学习框架，但在底层势函数、筛选策略和工作流设计上有显著差异：

| 对比维度 | NepTrain (NEP) | DP-GEN (DeepPot) |
|---------|---------------|-----------------|
| **底层势函数** | NEP（Neuroevolution Potential），基于遗传算法优化的神经网络描述符 | DeepPot-SE / DPA，基于深度神经网络的端到端势函数 |
| **训练硬件** | 单 GPU 即可训练，速度极快（分钟级） | 通常需要多 GPU，训练时间较长（小时级） |
| **MD 引擎** | GPUMD（GPU 原生，性能极高） | LAMMPS + DeePMD-kit 插件 |
| **不确定性评估** | 基于描述符空间距离（结构与训练集的"新颖度"） | 基于模型委员会（同时训练 4 个模型，比较预测偏差） |
| **筛选策略** | 描述符空间中与训练集的最小距离 + 多样性采样 | 模型偏差（model deviation）：`max_devi_f` 力偏差阈值 |
| **DFT 软件** | 目前主要支持 VASP | 支持 VASP、CP2K、Gaussian、ABACUS 等 |
| **配置文件** | 单一 `job.yaml`，结构清晰 | `param.json` + `machine.json`，参数较多 |
| **调度支持** | Slurm + PBS/Torque，支持混合调度（本地训练 + 远端 DFT） | Slurm、PBS、LSF、云平台等 |
| **迭代控制** | `step_times` 列表控制每代模拟步数，直观 | `model_devi_jobs` 列表定义多轮探索条件 |
| **生态成熟度** | 新兴工具，轻量灵活，社区在快速增长 | 成熟生态，文档完善，用户基数大 |
| **典型使用场景** | 中小体系快速迭代、需要高推理效率的生产 MD | 大规模复杂体系、多组分合金、需要极高精度 |

### 核心差异总结

1. **速度 vs 灵活性**：NepTrain 的训练和推理速度远快于 DP-GEN（NEP 训练分钟级 vs DeepPot 小时级），但 DP-GEN 支持的 DFT 后端和调度系统更丰富。

2. **筛选哲学不同**：
   - DP-GEN 依赖"模型委员会"——训练多个模型，用它们的分歧来衡量不确定性。代价是每轮要训练 4 个模型。
   - NepTrain 直接在描述符空间中度量结构的"新颖度"，无需额外训练多个模型，更轻量。

3. **工作流复杂度**：NepTrain 的 `job.yaml` 一个文件搞定所有配置，学习曲线较平缓；DP-GEN 需要分别配置 `param.json` 和 `machine.json`，参数更多但也更灵活。

---

## 3. 整体工作流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                     NepTrain 主动学习迭代循环                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   generation = 1                                                    │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────┐    使用当前 nep.txt，在多个温度下跑 MD                 │
│   │  GPUMD   │    探索结构空间，输出轨迹 dump.xyz                     │
│   └────┬─────┘                                                      │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────┐    从轨迹中筛选与训练集"距离最远"的结构                 │
│   │  Select  │    max_selected 控制每轮选取上限                       │
│   └────┬─────┘                                                      │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────┐    对筛选结构做 VASP 计算                             │
│   │   DFT    │    获取 energy / forces / stress                     │
│   └────┬─────┘                                                      │
│        │                                                            │
│        ▼                                                            │
│   ┌──────────┐    新数据合并到 train.xyz                             │
│   │   NEP    │    重新训练势函数 → 新 nep.txt                        │
│   └────┬─────┘                                                      │
│        │                                                            │
│        ▼                                                            │
│   generation += 1                                                   │
│   回到 GPUMD，使用更长的 step_times                                  │
│                                                                     │
│   收敛条件：筛选出的新结构数 → 0 或达到预设代数                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. 文件结构要求

运行前，工作目录应包含以下文件：

```
activate-laern/
├── job.yaml          # 主配置文件（本文件所描述）
├── train.xyz         # 初始训练数据（extxyz 格式）
├── test.xyz          # 测试集数据
├── nep.in            # NEP 训练参数文件
├── nep.txt           # 初始势函数（可由预训练获得）
├── run.in            # GPUMD 模拟输入文件
├── INCAR             # VASP INCAR 模板
└── structure/        # 模型结构目录（含 .vasp 或 .xyz 文件）
```

> **注意**：`job.yaml` 中的相对路径（如 `./train.xyz`）均相对于运行 `neptrain` 命令时的当前工作目录。

---

## 5. 顶层参数详解

| 参数 | 类型 | 说明 |
|------|------|------|
| `version` | string | 配置文件格式版本号，需与 NepTrain 版本匹配 |
| `dft_job` | int | 每轮提交的 DFT 任务上限数量。控制单轮 DFT 计算规模 |
| `gpumd_split_job` | string | GPUMD 任务拆分策略。`temperature` 表示按温度拆分为独立任务 |
| `work_path` | string | 工作缓存目录，存放中间文件和运行状态 |
| `current_job` | string | 当前需执行的阶段：`nep` / `gpumd` / `select` / `dft` |
| `generation` | int | 当前迭代代数编号，从 1 开始递增 |
| `init_train_xyz` | string | 初始训练数据文件路径 |
| `init_nep_txt` | string | 初始势函数文件路径 |

### 关键说明

- **`current_job`**：如果中途任务失败，可将此字段设为失败阶段，重新提交即可续跑。
- **`generation`**：每完成一整轮循环后自动 +1。手动续跑某一代时修改此值。
- **`gpumd_split_job: temperature`**：`temperature_every_step` 中的每个温度将生成一个独立的 GPUMD 任务，可并行提交。

---

## 6. nep 段（NEP 训练）

此段定义 NEP 势函数训练阶段的参数和计算资源。

### 6.1 核心参数

| 参数 | 说明 |
|------|------|
| `nep_restart` | `true` = 从上一代的 nep.txt 续训；`false` = 从头训练 |
| `nep_restart_step` | 续训时从第几步开始（需与 nep.in 中的总步数配合） |
| `nep_in_path` | nep.in 文件路径，定义描述符参数、截断半径、训练步数等 |
| `test_xyz_path` | 测试集路径，训练过程中评估泛化性能 |

### 6.2 machine（执行环境）

| 参数 | 说明 |
|------|------|
| `context_type: LazyLocal` | 本地执行，不走 SSH |
| `batch_type: Slurm` | 使用 Slurm 调度系统 |
| `local_root` | 本地工作根目录 |

### 6.3 resources（资源配置）

| 参数 | 说明 |
|------|------|
| `number_node` | 请求节点数 |
| `cpu_per_node` | 每节点 CPU 核数 |
| `gpu_per_node` | 每节点 GPU 数（NEP 训练需要 GPU） |
| `queue_name` | NepTrain 内部的逻辑队列名 |
| `group_size` | 批量分组大小 |
| `custom_flags` | 直接写入 sbatch 脚本的调度参数列表 |
| `prepend_script` | 任务执行前的环境初始化命令 |

### 6.4 custom_flags 示例解读

```yaml
custom_flags:
  - '#SBATCH --job-name=NepTrain-NEP'      # 作业名称
  - '#SBATCH --nodes=1'                     # 使用 1 个节点
  - '#SBATCH --ntasks-per-node=16'          # 16 个并行任务
  - '#SBATCH --gres=gpu:1'                  # 申请 1 块 GPU
  - '#SBATCH --mem=88G'                     # 内存上限
  - '#SBATCH --time=1000:00:00'             # 最大运行时间
  - '#SBATCH --partition=debug'             # 使用的分区
```

### 6.5 prepend_script 示例解读

```yaml
prepend_script:
  - source activate gpumdkit    # 激活 conda 环境
  - module purge                # 清除已加载的模块
  - module load gcc/13.1.0      # 加载 GCC 编译器
```

---

## 7. dft 段（DFT 标注）

此段定义对筛选结构进行 DFT 计算的参数。当前配置使用 VASP，通过 SSH 提交到远端 PBS/Torque 集群。

### 7.1 核心参数

| 参数 | 说明 |
|------|------|
| `software` | DFT 软件选择（目前支持 `vasp`） |
| `cpu_core` | VASP 并行核数 |
| `kpoints_use_gamma` | `true` = 使用 Gamma 中心 K 网格 |
| `use_k_stype` | K 点策略类型（`kspacing` 为按间距自动生成） |
| `kspacing` | K 点密度参数（1/Å），值越小 K 点越密，精度越高 |
| `incar_path` | INCAR 模板文件的路径 |

### 7.2 machine（SSH 远端执行）

| 参数 | 说明 |
|------|------|
| `context_type: SSH` | 通过 SSH 将任务提交到远端集群 |
| `batch_type: Torque` | 远端使用 PBS/Torque 调度系统 |
| `local_root` | 本地临时文件目录 |
| `remote_root` | 远端工作根目录 |
| `remote_profile.hostname` | SSH 远端主机地址 |
| `remote_profile.username` | SSH 用户名 |
| `remote_profile.password` | SSH 密码（可留空，使用密钥认证） |
| `remote_profile.port` | SSH 端口 |
| `remote_profile.timeout` | SSH 连接超时时间（秒） |

### 7.3 resources

| 参数 | 说明 |
|------|------|
| `custom_flags` | PBS 作业调度参数（`#PBS` 格式，与 `batch_type: Torque` 对应） |
| `prepend_script` | 远端环境初始化（激活环境、加载 VASP 模块等） |

> **注意**：`custom_flags` 的格式必须与 `batch_type` 一致。Torque 用 `#PBS`，Slurm 用 `#SBATCH`。

---

## 8. gpumd 段（采样模拟）

此段定义 GPUMD 分子动力学模拟的参数，用于探索结构空间。

### 8.1 核心参数

| 参数 | 说明 |
|------|------|
| `step_times` | 各代迭代的模拟步数列表。从少到多逐步增加 |
| `temperature_every_step` | 每代模拟的温度列表（K）。每个温度产生独立任务 |
| `model_path` | 结构模型所在目录（需含 `.vasp` 或 `.xyz` 格式文件） |
| `run_in_path` | GPUMD 的 `run.in` 输入文件路径 |

### 8.2 step_times 策略说明

```yaml
step_times:
  - 10      # 第 1 代：10 步（快速出结构，保守探索）
  - 100     # 第 2 代：100 步
  - 500     # 第 3 代：500 步
  - 1000    # 第 4 代：1000 步（势函数已较成熟，可放心跑长）
```

- 列表长度决定了计划进行的最大代数
- 当 `generation` 超过列表长度时，使用最后一个值
- 前几代步数短是为了避免势函数不成熟时模拟"跑飞"

### 8.3 temperature_every_step 说明

```yaml
temperature_every_step:
  - 50       # 50 K
  - 100      # 100 K
  - 150      # 150 K
  - 200      # 200 K
  - 250      # 250 K
  - 300      # 300 K
```

每个温度生成一个独立的 GPUMD 任务，可并行提交。覆盖的温度范围越广，训练出的势函数适用性越强。

### 8.4 machine 与 resources

与 `nep` 段结构相同，使用本地 Slurm 提交，需要 GPU 资源。

---

## 9. select 段（结构筛选）

此段定义如何从 GPUMD 轨迹中筛选代表性结构。

### 9.1 核心参数

| 参数 | 说明 |
|------|------|
| `max_selected` | 每轮最多筛选的结构数。控制每轮 DFT 计算量上限 |
| `min_distance` | 描述符空间中的最小距离阈值。确保选出的结构之间有足够多样性 |
| `filter` | 筛选过滤强度（0~1），值越大筛选越严格 |

### 9.2 筛选原理

筛选基于 NEP 描述符空间中的距离度量：
1. 计算每个候选结构的描述符向量
2. 计算该向量与训练集中所有已有结构的最小距离
3. 距离越大 → 结构越"新颖" → 越值得标注
4. `min_distance` 确保选出的结构彼此之间也有差异（避免选一堆相似的）
5. `max_selected` 限制每轮 DFT 计算量，防止一次标注过多

### 9.3 machine 与 resources

当前配置为 SSH + Torque（与 `dft` 段使用同一远端集群）。结构筛选主要消耗 CPU，不需要 GPU。

---

## 10. limit 段（数据过滤）

```yaml
limit:
  force: 20    # 力的阈值上限（eV/Å）
```

用于过滤 DFT 计算结果中力过大的异常结构。如果某个原子上的力超过此阈值，该结构会被丢弃，不加入训练集。

| 取值范围 | 影响 |
|---------|------|
| 偏小（< 10） | 过滤激进，可能丢弃有效数据 |
| 适中（10~30） | 推荐范围，过滤明显异常 |
| 偏大（> 30） | 过滤宽松，可能引入质量差的数据 |

---

## 11. 快速开始

### 11.1 准备输入文件

确保以下文件就位：

```bash
ls train.xyz test.xyz nep.in nep.txt run.in structure/
```

- `train.xyz`：初始训练集（extxyz 格式，至少包含几十个结构）
- `test.xyz`：测试集（用于监控训练质量）
- `nep.in`：NEP 训练参数
- `nep.txt`：初始势函数（如果首轮从头训练，设 `nep_restart: false`）
- `run.in`：GPUMD 模拟参数
- `structure/`：包含初始结构的目录

### 11.2 修改 job.yaml

将模板中的占位参数替换为你的实际环境：

```yaml
# 远端集群信息
remote_profile:
  hostname: "your-cluster-ip"    # ← 替换
  username: your-username        # ← 替换
  password: ""                   # 留空使用密钥，或填入密码
  port: 22

# 远端路径
remote_root: /home/username/neptrain-work/   # ← 替换

# INCAR 路径
incar_path: /home/username/INCAR             # ← 替换
```

### 11.3 启动主动学习

```bash
# 启动 NepTrain，它会根据 current_job 和 generation 自动执行对应阶段
neptrain job.yaml
```

### 11.4 监控与续跑

```bash
# 查看当前进度（cache 目录下有状态文件）
ls ./cache/

# 如果某个阶段失败，修改 current_job 为对应阶段后重新提交
# 例如 DFT 阶段失败：
#   current_job: dft
#   generation: 2   （保持不变）
neptrain job.yaml
```

---

> [!CAUTION]
> **重要提醒**：除了修改 `job.yaml` 中的占位参数外，还需要修改 `~/.NepTrain` 配置文件中的软件路径，包括：
> - **POTCAR 路径**：VASP 赝势文件目录
> - **VASP 路径**：VASP 可执行文件路径（如 `vasp_std`、`vasp_gam`）
> - **GPUMD 路径**：GPUMD 可执行文件路径
> - **NEP 路径**：NEP 训练程序路径
>
> 如果这些路径未正确配置，NepTrain 将无法调用对应的软件，导致任务失败。
