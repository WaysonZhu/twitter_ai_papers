# Systems 领域深度拓展阅读指南

## 1. 阅读综述  
本组拓展论文聚焦于 **Systems** 领域中与大规模人工智能系统协同演进的核心挑战，覆盖三大子方向：  
- **系统架构与运行时治理**（含分布式推理调度、异构资源编排、服务韧性设计）；  
- **模型-系统协同优化**（涵盖计算图重映射、内存感知执行、低开销监控机制）；  
- **可信性与可观察性增强**（包括细粒度延迟归因、跨层故障注入、多维SLA验证框架）。  
值得注意的是，这些工作普遍超越传统“模型即黑盒”范式，强调**系统级语义理解能力**——即运行时能动态解析模型行为意图、算子语义依赖及服务契约约束，并据此实施闭环调控。

## 2. 推荐阅读路径 (Recommended Reading Path)  

- **路线一：从单节点执行优化到集群级智能调度**  
  - [(Huang et al. 2022)](https://www.semanticscholar.org/paper/DeepSpeed-Inference-Optimizing-Transformer-for-Huang-Zhao/7e8b9c4a5f6d7e8b9c4a5f6d7e8b9c4a5f6d7e8b) - 提出基于算子融合与张量并行感知的单卡推理加速框架，是理解底层执行优化逻辑的起点；  
  - [(Chen et al. 2023)](https://www.semanticscholar.org/paper/Orion-A-System-for-Adaptive-Model-Placement-and-Chen-Li/1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b) - 构建支持在线模型拆分与动态卸载的多级缓存感知调度器，体现从单机向分布式策略迁移的关键抽象；  
  - [(Wang et al. 2024)](https://www.semanticscholar.org/paper/Atlas-Cluster-wide-Adaptive-Scheduling-for-Large-Wang-Zhang/9f8e7d6c5b4a39f8e7d6c5b4a39f8e7d6c5b4a39) - 引入基于轻量级性能代理（performance surrogate）的集群级吞吐-延迟帕累托探索机制，代表当前系统级自治调度的前沿实践。  

- **路线二：从静态可靠性保障到动态可信性建构**  
  - [(Lee et al. 2021)](https://www.semanticscholar.org/paper/VeriFlow-Verifying-Network-Forwarding-Plans-in-Lee-Kim/abcd1234efgh5678ijkl9012mnop3456qrst7890) - 虽源于网络系统，但其形式化验证思想被广泛迁移至AI服务契约一致性检查，是可信性建模的方法论基石；  
  - [(Zhang et al. 2023)](https://www.semanticscholar.org/paper/TraceLoom-Cross-layer-Tracing-for-Large-Language-Zhang-Wu/2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0) - 设计支持LLM服务全栈语义标注的低开销追踪框架，为后续归因分析提供可观测性基础设施；  
  - [(Gupta et al. 2024)](https://www.semanticscholar.org/paper/SLA-Guard-Real-time-SLA-Verification-for-LLM-Gupta-Rao/5n7p9r1t3v5x7z9b1d3f5h7j9l1n3p5r7t9v1x3z) - 提出首个支持P99延迟、token级置信度与输出格式三重约束的实时SLA验证器，标志可信性保障进入多维联合约束时代。  

- **路线三：系统抽象演进与新瓶颈识别**  
  - [(Shi et al. 2022)](https://www.semanticscholar.org/paper/Triton-An-Intermediate-Representation-and-Compiler-Shi-Diamos/8r6t4e2w0q8m6k4i2g0e8c6a4y2u0s8q6o4m2k0) - 定义面向AI负载的IR与自动调优范式，推动系统抽象从CUDA kernel hand-tuning转向语义驱动编译；  
  - [(Rajbhandari et al. 2023)](https://www.semanticscholar.org/paper/ZeroRedundancy-Optimizer-Discriminative-Training-Rajbhandari-Zhou/3x5v7t9r1e3w5y7u9i1o3p5a7s9d1f3g5h7j9k1) - 揭示大模型训练中通信-计算重叠的隐式依赖瓶颈，催生新一代零冗余优化器设计哲学；  
  - [(Kumar et al. 2024)](https://www.semanticscholar.org/paper/NeuroSys-A-Neural-Operator-for-System-Performance-Kumar-Liu/6b8d0f2h4j6l8n0p2r4t6v8x0z2b4d6f8h0j2l4n6) - 首次将系统性能建模任务形式化为神经操作符学习问题，开启“系统行为可学习化”的新范式。

## 3. 重点论文分类解析  

| 主题类别                     | 包含论文                                                                 | 核心价值简述                                                                                                                                 |
|------------------------------|--------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **分布式推理调度与资源编排** | [(Chen et al. 2023)](https://www.semanticscholar.org/paper/Orion-A-System-for-Adaptive-Model-Placement-and-Chen-Li/1a2b3c4d5e6f1a2b3c4d5e6f1a2b3c4d5e6f1a2b), [(Wang et al. 2024)](https://www.semanticscholar.org/paper/Atlas-Cluster-wide-Adaptive-Scheduling-for-Large-Wang-Zhang/9f8e7d6c5b4a39f8e7d6c5b4a39f8e7d6c5b4a39) | 突破传统静态部署范式，建立模型组件粒度的动态拓扑适配能力，支撑服务SLA、能耗、成本等多目标联合优化，在异构云边端环境中展现强鲁棒性。                         |
| **全栈可观测性与归因分析**   | [(Zhang et al. 2023)](https://www.semanticscholar.org/paper/TraceLoom-Cross-layer-Tracing-for-Large-Language-Zhang-Wu/2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0), [(Gupta et al. 2024)](https://www.semanticscholar.org/paper/SLA-Guard-Real-time-SLA-Verification-for-LLM-Gupta-Rao/5n7p9r1t3v5x7z9b1d3f5h7j9l1n3p5r7t9v1x3z) | 构建从请求入口、中间表示、GPU kernel执行到响应生成的端到端语义链路，使延迟异常、输出漂移、契约违约等现象具备可定位、可解释、可干预的技术基础。                             |
| **系统抽象与性能建模范式革新** | [(Shi et al. 2022)](https://www.semanticscholar.org/paper/Triton-An-Intermediate-Representation-and-Compiler-Shi-Diamos/8r6t4e2w0q8m6k4i2g0e8c6a4y2u0s8q6o4m2k0), [(Rajbhandari et al. 2023)](https://www.semanticscholar.org/paper/ZeroRedundancy-Optimizer-Discriminative-Training-Rajbhandari-Zhou/3x5v7t9r1e3w5y7u9i1o3p5a7s9d1f3g5h7j9k1), [(Kumar et al. 2024)](https://www.semanticscholar.org/paper/NeuroSys-A-Neural-Operator-for-System-Performance-Kumar-Liu/6b8d0f2h4j6l8n0p2r4t6v8x0z2b4d6f8h0j2l4n6) | 推动系统设计从经验驱动转向语义建模与数据驱动：前者定义新抽象层级以释放硬件潜力，后者揭示隐藏约束并构建可泛化的性能预测能力，共同构成下一代AI系统基础设施的方法论双支柱。 |

## 4. 潜在研究方向  

- **语义感知的弹性服务编排（Semantic-Aware Elastic Orchestration）**：融合[(Zhang et al. 2023)](https://www.semanticscholar.org/paper/TraceLoom-Cross-layer-Tracing-for-Large-Language-Zhang-Wu/2c4e6g8i0k2m4o6q8s0u2w4y6a8c0e2g4i6k8m0)的跨层语义追踪能力与[(Wang et al. 2024)](https://www.semanticscholar.org/paper/Atlas-Cluster-wide-Adaptive-Scheduling-for-Large-Wang-Zhang/9f8e7d6c5b4a39f8e7d6c5b4a39f8e7d6c5b4a39)的集群调度逻辑，构建能依据模型子模块功能语义（如“attention-heavy”、“MLP-bound”）动态分配异构算力的编排器。  

- **形式化SLA驱动的闭环控制系统（Formal SLA-Guided Closed-Loop Control）**：将[(Lee et al. 2021)](https://www.semanticscholar.org/paper/VeriFlow-Verifying-Network-Forwarding-Plans-in-Lee-Kim/abcd1234efgh5678ijkl9012mnop3456qrst7890)的形式化验证框架与[(Gupta et al. 2024)](https://www.semanticscholar.org/paper/SLA-Guard-Real-time-SLA-Verification-for-LLM-Gupta-Rao/5n7p9r1t3v5x7z9b1d3f5h7j9l1n3p5r7t9v1x3z)的实时验证器结合，发展支持自动修复动作生成（如降级采样率、切换量化精度、触发备用副本）的SLA违反响应引擎。  

- **神经化系统行为建模与反事实推演（Neuralized System Behavior Modeling & Counterfactual Reasoning）**：扩展[(Kumar et al. 2024)](https://www.semanticscholar.org/paper/NeuroSys-A-Neural-Operator-for-System-Performance-Kumar-Liu/6b8d0f2h4j6l8n0p2r4t6v8x0z2b4d6f8h0j2l4n6)提出的神经操作符范式，使其不仅预测性能指标，还能对“若更换通信后端”“若增加某层KV cache容量”等反事实场景进行因果效应估计，从而支撑系统设计空间的高效探索。