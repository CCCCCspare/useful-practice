# HW2：SGLang 在线推理与路由实验

## 1. 实验范围

目标一使用 SGLang 启动 Qwen/Qwen3-0.6B，比较共享前缀与分散前缀负载。目标三现有回放流程使用四个模拟 Replica HTTP 服务，不等同于四个真实 SGLang 推理后端，也不能据此认定已完成 Ray Serve 默认路由的真实对照实验。

本说明依据终端输出及已有实验记录整理。尚未检查 benchmark.py、experiment_runner.py 和 Ray 部署脚本的完整源码；下文回放入口需以实际脚本参数为准。B10/B20 的配置切换方法尚待核实。

## 2. GPU 与软件版本

| 项目 | 实验环境 |
| --- | --- |
| GPU | NVIDIA GeForce RTX 5060 系列，显存 8151 MiB；本次 nvidia-smi 输出中的完整型号被截断 |
| NVIDIA-SMI | 610.43.02 |
| 驱动 KMD | 610.62 |
| CUDA UMD | 13.3 |
| CUDA Toolkit（nvcc） | 13.0，V13.0.88 |
| Python | 3.12.3 |
| SGLang | 0.5.14 |
| sglang-kernel | 0.4.4 |
| PyTorch | 2.11.0 |
| Ray | 2.58.0 |
| FastAPI | 0.141.1 |
| Uvicorn | 0.52.4 |
| NumPy | 2.3.5 |
| pandas | 3.0.5 |
| requests | 2.34.2 |

CUDA UMD 与 nvcc 的版本含义不同，不能将 UMD 13.3 写成已安装的 CUDA Toolkit 版本。PyTorch 自带的 CUDA 运行时版本尚未记录。

## 3. 安装方法

在项目根目录创建环境：

```bash
python3 -m venv .venv-sglang
source .venv-sglang/bin/activate
python -m pip install sglang==0.5.14 'ray[serve]==2.58.0' fastapi==0.141.1 uvicorn==0.52.4 requests==2.34.2 pandas==3.0.5 numpy==2.3.5
```

以上为按已记录版本整理的安装命令，未在全新环境验证依赖解析结果。已有可运行环境无需重新安装。目标一还需要 NVIDIA GPU 环境以及 Qwen/Qwen3-0.6B 模型文件；首次启动可能需要下载模型。

在原有虚拟环境中导出完整依赖快照：

```bash
cd ~/sglang_hw2/HW2-csm
python -m pip freeze > requirements.txt
```

提交包附带该文件后，可在兼容环境中执行：

```bash
python -m pip install -r requirements.txt
```

## 4. 目录约定

原项目根目录为 `~/sglang_hw2/HW2-csm`。现有脚本在各自的 `src/target1` 或 `src/target3` 目录中运行。原始结果位置与提交结果位置不同，不能只移动结果后就假定脚本路径已经同步修改。

| 内容 | 提交位置 |
| --- | --- |
| 本说明 | README.md |
| 实验报告 | report.pdf |
| 依赖快照 | requirements.txt |
| 目标一代码 | src/target1/ |
| 目标三代码及必要配置 | src/target3/ |
| 共享前缀结果 | results/target1/shared_prefix/ |
| 分散前缀结果 | results/target1/dispersed_prefix/ |
| A 结果 | results/target3/A_default/ |
| B 结果 | results/target3/B_candidates/ |
| C 结果 | results/target3/C_affinity/ |
| D 结果 | results/target3/D_improved/ |

目标三固定负载的现有位置：

`src/target3/26fall-HW-data/workloads/hw2/target3-routing-policies/mooncake_prefix_workload_v2_seed2026.jsonl`

复现时需要保留该负载及脚本实际读取的辅助文件，或在说明中提供可用的获取方式。仅保留结果 CSV 不足以回放实验。

## 5. 目标一：脚本、数据与结果说明

### 5.1 实验脚本

| 文件 | 作用（一句话） |
| --- | --- |
| start_server.sh | 启动 SGLang 推理服务器，加载 Qwen3-0.6B 并开启 Radix Cache。 |
| generate_data.py | 生成两组实验输入数据：共享前缀和分散前缀请求。 |
| benchmark.py | 向 SGLang /generate 接口发送32条测试请求，并保存模型返回结果。 |
| warmup.py | 发送共享前缀预热请求，让 KV Cache 提前建立，不计入正式实验结果。 |

### 5.2 数据文件

| 文件 | 作用（一句话） |
| --- | --- |
| shared_requests.json | 保存共享前缀实验的32条请求，每条包含2048 token公共前缀+64 token独立后缀。 |
| dispersed_requests.json | 保存分散前缀实验的32条请求，每条2112 token且首token不同。 |

### 5.3 结果目录

以下目录相对于目标一运行目录 `src/target1/`。

| 目录 | 作用 |
| --- | --- |
| results/shared_prefix | 保存共享前缀实验相关结果文件。 |
| results/dispersed_prefix | 保存分散前缀实验相关结果文件。 |

### 5.4 实验结果文件

| 文件 | 作用（一句话） |
| --- | --- |
| shared_requests_result.json | 保存共享前缀32条请求的推理结果，包括prompt_tokens、cached_tokens、延迟等信息。 |
| dispersed_requests_result.json | 保存分散前缀32条请求的推理结果，用于计算无缓存情况下的指标。 |

## 6. 目标三：启动与回放

### 6.1 启动模拟 Replica

```bash
cd ~/sglang_hw2/HW2-csm/src/target3
bash start_four_replica.sh
```

已确认启动脚本分别执行 `python3 replica_server.py --port`，端口为 9000、9001、9002、9003。该脚本不会自动启动 Ray 集群或真实 SGLang 后端。启动前应确认四个端口未被旧实例占用。

### 6.2 回放 A、C、D

以下命令来自此前实验记录；输出到原有运行目录下的 results/target3，不直接输出到项目根目录的 results/target3：

```bash
cd ~/sglang_hw2/HW2-csm/src/target3
mkdir -p results/target3/{A_default,B_candidates,C_affinity,D_improved}
python3 experiment_runner.py A results/target3/A_default/result.csv
python3 experiment_runner.py C results/target3/C_affinity/result.csv
python3 experiment_runner.py D results/target3/D_improved/result.csv
python3 analyze_results.py
```

不同策略之间应采用相同初始缓存状态和预热规则。当前尚未核实脚本是否自动清空缓存、是否排除预热请求；连续运行上述命令不代表已满足这些公平对照条件。回放前备份原有同名结果文件。

### 6.3 B10 / B20 与 Ray Serve

已有文件列表包含 serve_deployment.py、serve_B_10.py、serve_B_20.py、hybrid_router.py 等。仅根据文件名，无法确认这些文件是否被当前回放流程使用。

B10 与 B20 必须实际采用不同的 max_ongoing_requests 配置。两次执行同一个 `experiment_runner.py B` 命令，仅将输出名改成 B10.csv 和 B20.csv，不能证明运行了两种配置。因此这里暂不提供未经核实的 B10/B20 切换命令或 Ray 集群启动命令。

核实相关源码：

```bash
cd ~/sglang_hw2/HW2-csm
cat src/target3/experiment_runner.py
cat src/target3/serve_deployment.py
cat src/target3/serve_B_10.py
cat src/target3/serve_B_20.py
cat src/target3/hybrid_router.py
```

## 7. 脚本用途

| 脚本 | 用途与核实情况 |
| --- | --- |
| src/target1/start_server.sh | 启动 SGLang 推理服务器，加载 Qwen3-0.6B 并开启 Radix Cache。 |
| src/target1/generate_data.py | 生成两组实验输入数据：共享前缀和分散前缀请求。 |
| src/target1/benchmark.py | 向 SGLang /generate 接口发送32条测试请求，并保存模型返回结果。 |
| src/target1/warmup.py | 发送共享前缀预热请求，让 KV Cache 提前建立，不计入正式实验结果。 |
| src/target3/replica_server.py | 根据已有记录：模拟 Replica 及缓存命中行为 |
| src/target3/start_four_replica.sh | 已确认：启动四个独立 HTTP 服务进程 |
| src/target3/experiment_runner.py | 根据已有记录：回放负载并执行 A/B/C/D 策略，具体实现待核实 |
| src/target3/analyze_results.py | 根据已有记录：统计目标三结果，实际读取路径与指标待核实 |
| src/target3/serve_deployment.py | 已确认文件存在；Ray Serve 部署内容待核实 |
| src/target3/serve_B_10.py、serve_B_20.py | 已确认文件存在；B 配置及启动方式待核实 |
| src/target3/hybrid_router.py | 已确认文件存在；与最终 D 回放的调用关系待核实 |
| src/target3/prefix_affinity_router.py、prefix_router.py、prefix_router_v2.py、prefix_replica.py | 前缀路由相关文件；最终使用版本待核实 |
| src/target3/workload_runner.py、test_client.py | 已确认文件存在；负载与测试入口用途待源码核实 |

提交时应保留实际调用的路由代码、部署文件及其导入依赖，不能仅凭文件名将它们视为可删除的测试文件。

## 8. 结果目录与报告表格对应关系

报告表号尚未提供，以下按表格中的实验行对应。

| 报告表格中的实验行 | 提交结果路径 | 对应负载 |
| --- | --- | --- |
| 目标一：共享前缀 | results/target1/shared_prefix/shared_requests_result.json | 同目录 shared_requests.json |
| 目标一：分散前缀 | results/target1/dispersed_prefix/dispersed_requests_result.json | 同目录 dispersed_requests.json |
| 目标三：A | results/target3/A_default/result.csv | 固定目标三 workload |
| 目标三：B10 | results/target3/B_candidates/B10.csv | 固定目标三 workload |
| 目标三：B20 | results/target3/B_candidates/B20.csv | 固定目标三 workload |
| 目标三：C | results/target3/C_affinity/result.csv | 固定目标三 workload |
| 目标三：D | results/target3/D_improved/result.csv | 固定目标三 workload |

目标三报告可设置成功率、吞吐量、模拟缓存命中率、实际 Prefill token、TTFT p95、端到端延迟 p95、Replica 请求分布等列；仅填写有原始记录支持的指标。

- 模拟缓存命中率不能称为真实 SGLang KV 缓存命中率。
- 模拟服务延迟不能称为真实模型推理延迟。
- 当前模拟流程的实际 Prefill token 与真实 TTFT 填 N/A，并注明“未连接真实 SGLang 推理后端”。
- 吞吐量需要测量请求数和对应时间区间；缺少时间依据时填 N/A。
- B10/B20 的配置差异及 A 与 Ray Serve 默认策略的关系，在核实前不得写成已经验证。

## 9. 汇总原始结果到提交位置

下面命令从项目根目录执行，仅复制结果，不修改脚本内的路径。执行前确认原始结果确实存在；同名目标文件会被覆盖。

```bash
cd ~/sglang_hw2/HW2-csm
mkdir -p results/target1/shared_prefix results/target1/dispersed_prefix
mkdir -p results/target3
cp -r src/target1/results/shared_prefix/. results/target1/shared_prefix/
cp -r src/target1/results/dispersed_prefix/. results/target1/dispersed_prefix/
cp -r src/target3/results/target3/. results/target3/
find results -type f
```

最近一次终端输出显示，项目根目录的 results/target3 四个子目录为空。应以复制后的实际文件为准，不能将空目录当作已完成的实验结果。
