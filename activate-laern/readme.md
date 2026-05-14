# `job.yaml` 参数说明（NEPtrain 工作流）

本文档用于解释 `activate-laern/job.yaml` 的配置含义与使用方法。  
建议你先看“原理与流程”，再按章节对照修改自己的参数。

---

## 1. NEPtrain 的原理与整体流程

`neptrain` 的核心思想是**主动学习（active learning）+ 迭代训练**：

1. 用当前的 `nep.txt` 势函数先做一批 GPUMD 模拟，探索结构空间。  
2. 从模拟结果中筛选“高不确定性/代表性”结构（`select` 阶段）。  
3. 对这些结构做 DFT 标注（`dft` 阶段）。  
4. 将新增标注数据加入训练集，重新训练 NEP（`nep` 阶段）。  
5. 重复以上循环，直到势函数精度满足要求。

所以这个 `job.yaml` 本质上是在定义：

- 每个阶段用什么机器（`machine`）
- 每个阶段如何提交作业（`resources`）
- 阶段之间如何衔接（顶层流程参数）

---

## 2. 顶层参数说明

- `version`
  - 配置文件版本号。

- `dft_job`
  - 每轮提交的 DFT 任务数量上限（或批量大小）。

- `gpumd_split_job`
  - GPUMD 任务切分方式，例如按温度切分（`temperature`）。

- `work_path`
  - 工作缓存目录。

- `current_job`
  - 当前要执行/续跑的阶段（例如 `nep`）。

- `generation`
  - 当前迭代代数编号。

- `init_train_xyz`
  - 初始训练数据文件路径。

- `init_nep_txt`
  - 初始势函数文件路径（冷启动或续跑时使用）。

---

## 3. `nep` 段（NEP 训练阶段）

### 核心参数

- `nep_restart`
  - 是否从已有训练状态继续。

- `nep_restart_step`
  - 续跑起始步数（配合 restart 使用）。

- `nep_in_path`
  - `nep.in` 输入文件路径。

- `test_xyz_path`
  - 训练过程使用的测试集路径。

### `machine`

- `context_type: LazyLocal`
  - 本地上下文模式（任务在本地可见路径执行）。

- `batch_type: Slurm`
  - 调度系统类型。当前已配置为 Slurm。

- `local_root`
  - 本地工作根目录。

### `resources`

- `number_node` / `cpu_per_node` / `gpu_per_node`
  - 资源请求规模。

- `queue_name`
  - 逻辑队列名（工具内部字段）。

- `group_size`
  - 批量分组大小。

- `custom_flags`
  - 直接写入作业脚本的调度器参数（当前为 `#SBATCH ...`）。

- `prepend_script`
  - 在主命令前执行的环境准备脚本。
  - 你当前配置中主要做了：
    - 激活环境：`source activate gpumdkit`
    - 清理模块：`module purge`
    - 加载编译器：`module load gcc/13.1.0`

---

## 4. `dft` 段（DFT 标注阶段）

### 核心参数

- `software: vasp`
  - DFT 软件类型。

- `cpu_core`
  - DFT 计算使用 CPU 核数设置。

- `kpoints_use_gamma` / `use_k_stype` / `kspacing`
  - K 点相关策略。

- `incar_path`
  - INCAR 模板路径。

### `machine`（远端执行）

- `context_type: SSH`
  - 通过 SSH 在远端机器执行。

- `batch_type: Torque`
  - 该阶段仍使用 PBS/Torque（你当前配置如此）。

- `local_root`
  - 本地目录。

- `remote_root`
  - 远端工作根目录。
  - 例如当前示例：`/home/user/your-path/`

- `remote_profile`
  - SSH 登录参数：
  - `hostname`：远端主机地址
  - `username`：用户名
  - `password`：密码字段
  - `port`：SSH 端口
  - `timeout`：连接超时秒数

### `resources`

- `custom_flags` 目前使用 `#PBS ...`，与 `batch_type: Torque` 一致。

- `prepend_script`
  - 远端任务前置环境命令，例如激活环境、加载模块、加载 VASP。

---

## 5. `gpumd` 段（采样/动力学阶段）

### 核心参数

- `step_times`
  - 各轮模拟步数列表。

- `temperature_every_step`
  - 每轮温度列表（与任务拆分策略对应）。

- `model_path`
  - 结构模型目录(需为.vasp和.xyz格式)。

- `run_in_path`
  - GPUMD 输入文件路径。

### `machine` 与 `resources`

- `batch_type: Slurm`，`custom_flags` 使用 `#SBATCH`。
- 字段含义与 `nep` 段一致：资源、队列参数、前置脚本。

---

## 6. `select` 段（结构筛选阶段）

- `max_selected`
  - 每轮最多筛选结构数量。

- `min_distance`
  - 筛选时的最小距离阈值。

- `filter`
  - 筛选过滤强度参数（具体语义以工具版本实现为准）。

`machine` 和 `resources` 与 `dft` 类似，当前是 SSH + Torque/PBS。

---

## 7. `limit` 段

- `force`
  - 力阈值限制参数（常用于过滤异常数据/约束样本范围）。

---

## 8. `prepend_script`、`remote_root` 重点说明

### `prepend_script`

这是每个任务真正执行前最关键的环境引导区。  
常见用途：

- 激活 Conda 环境
- 加载模块（编译器、CUDA、VASP）
- 导出环境变量

如果这里错了，后续程序通常会直接报“命令不存在”或“库缺失”。

### `remote_root`

这是远程作业的工作根路径。  
你现在用的是占位路径 `/your-path/`，实际使用时应改成你集群真实路径。

---

## 9. 最后检查清单（必须替换为你的环境）

在正式提交前，请逐项替换并核对：

1. `hostname` 改为你的真实集群地址。  
2. `username` 改为你的账户名。  
3. `password` 建议保持空，优先使用免密 SSH。  
4. `remote_root` 改为你的真实远端目录。  
5. `incar_path` 改为你的真实 INCAR 文件路径。  
6. `prepend_script` 中环境名、模块名、版本号改为你机器可用值。  
7. `custom_flags` 与你的调度系统一致（Slurm 用 `#SBATCH`，Torque 用 `#PBS`）。

如果这些不替换，配置大概率无法在你的实际环境中直接运行。
