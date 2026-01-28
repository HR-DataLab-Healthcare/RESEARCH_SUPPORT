
  
# Privacy-, linguistic-, and information-preserving synthesis of clinical documentation through generative agents    
Source: https://www.frontiersin.org/journals/artificial-intelligence/articles/10.3389/frai.2025.1644084/full 


### USE CASE
Generate synthetic Dutch EHR free-text that preserves clinical meaning and writing style while reducing privacy risk, using a protocolized multi-agent LLM workflow plus automated evaluation against real/anonymized notes.

* Problem: access to high-quality, interoperable clinical documentation is limited by legal/ethical/technical barriers, yet free-text EHR narratives contain clinically valuable information not captured in structured fields.
​

* Proposed solution: a privacy-, linguistic-, and information-preserving synthetic health data generation (SHDG) protocol using multiple role-specific generative agents that collaborate in multi-turn interactions, guided by authentic EHRs as structural/linguistic templates.
​

* Intended value: enable scalable, transparent, reproducible unlocking of clinical documentation for research, innovation, and learning health systems while addressing privacy and quality concerns (hallucination, bias, opacity).

### Data pipeline + Implemented Workflows

Pipeline (DSI stack): FLOW01 converts anonymized clinical notes from PDF→Markdown, FLOW02 performs pseudonymization (GenAI-based NER), FLOW03/03_AGENT_BASED generates synthetic notes (standard prompting vs GA-based), and FLOW04 benchmarks synthetic vs anonymized vs real notes using corpus/document-level metrics (diversity, vocabulary similarity, semantic alignment, classifier-based “machine discernibility”).
​

Orchestration: implemented as a no-code multi-agent workflow in a rapid prototyping platform (Flowise; also cites Langflow/AutoGen as comparable), built from modular components that can be rearranged and shared/deployed as web-accessible inference endpoints.
​

Agent design: a supervisor agent orchestrates work and enforces documentation standards (e.g., ICF domains and Dutch KNGF guideline for low back pain), while worker agents generate specialized content (e.g., different physiotherapy profiles) under role-specific prompts.
​

RAG + memory: the Flowise workflow includes document ingestion with chunking, embedding generation, agent memory stored in SQLite, and retrieval via a vector store to reduce hallucination and keep outputs aligned with guidelines and source templates.
​

Model strategy: the proof-of-concept used GPT‑4.1 via Azure API for supervised reasoning and text generation, and also describes a privacy-first local alternative via Ollama for on-prem model execution.
​
  
---  
  
| Layer | Nutanix (NKP/NCI footprint) | UbiOps footprint | Concrete infra spec (4–6 concurrent DS; 200–600 dossiers / 2000+ notes) |  
| :-- | :-- | :-- | :-- |  
| K8s + VM platform | NKP standardizes K8s lifecycle across environments; integrates with Nutanix infra (NCI) and storage via CSI | N/A | **Nutanix cluster:** 3× nodes (HA), each **2×24-core CPU**, **512 GB RAM**, **2× 48 GB GPUs**, **2× 3.84 TB NVMe**, **2× 25GbE** |  
| LLM inference pool | Run Ollama on NKP worker nodes (GPU) | UbiOps can orchestrate/scaling of GPU workloads “on-demand across GPUs” and load balance API traffic | **GPU pool (total):** 6× 48 GB GPUs (e.g., 3 nodes × 2 GPUs) to serve Qwen2.5-32B AWQ + Qwen2.5-VL-32B AWQ + Mistral‑Small‑24B concurrently |  
| Embeddings service | K8s deployment on NKP | UbiOps deployment as isolated service that scales independently (pipeline objects isolated) | **1× embedding deployment:** 1× **24 GB GPU**, 8–16 vCPU, 64–128 GB RAM (Qwen3-Embedding-8B) |  
| Orchestration / control plane | NKP provides cluster mgmt/observability/security patterns for microservices | UbiOps provides model catalog/versioning, API management, resource prioritization, logging/monitoring, security \& access management | **UbiOps control plane:** 2× app instances **4 vCPU / 8 GB RAM** + **Postgres 4–8 vCPU / 16–32 GB** + **Redis 2–4 vCPU / 8–16 GB** (HA optional) |  
| RAG / vector DB | K8s stateful set + NVMe PV (CSI) | Can be one service in a UbiOps pipeline (or external) | **Vector DB node:** 16 vCPU, 64 GB RAM, **2 TB NVMe** |  
| Workflow apps (Flowise + Langflow) | Run both as containers on NKP | Optional: run them as managed UbiOps deployments behind APIs | **2 replicas each** (Flowise + Langflow): per replica **4 vCPU / 8–16 GB** |  
| Object/file storage (PDF/MD/artifacts) | NKP notes “enterprise data services” + can pair with Nutanix Unified Storage/object storage | UbiOps lets you control where data is processed/stored and exposes workflows via APIs | **S3-compatible object store:** **10 TB usable**, 3–4 nodes (erasure-coded), 10/25GbE uplinks |  
  
---  
  
## Infra choices explained (succinct)  
  
These numbers are sized to match the paper’s end-to-end **DSI stack** (warehousing → compute → container toolchain → workflow orchestration → deployment) and the PoC workflow composition: **ingestion → embeddings → agent memory → vector retrieval (RAG) → multi-agent synthesis → automated benchmarking**.  
  
**Sizing assumptions**  
- 4–6 concurrent technical users (interactive runs + prompt/chunking experiments)  
- 200–600 dossiers / 2000+ notes  
- Local/on-prem inference (privacy-first), so **VRAM is the hard capacity limit**  
  
---  
  
#### Why a 3-node Nutanix cluster (HA baseline)  
- Smallest common topology that supports **N+1 availability** for K8s control/services and storage while tolerating a node failure or rolling upgrades.  
- Aligns with the paper’s emphasis on **reproducible, containerized workflows** deployed consistently across environments.  
  
---  
  
#### Why 6×48GB total GPU for LLM inference  
- The synthesis is **multi-agent** (supervisor + workers). One user interaction often triggers **multiple LLM calls**, so concurrency multiplies quickly.  
- 32B-class models (even quantized) are **VRAM-heavy**; with 4–6 concurrent users you want enough GPUs to avoid a single shared queue dominating latency.  
- Supports running multiple models in parallel (text + vision + alternative baseline) without constant eviction/reload.  
  
---  
  
#### Why a dedicated embeddings GPU  
- The workflow is embedding- and retrieval-centric (continuous **indexing/re-indexing**, chunking changes, experiments).  
- Separating embeddings prevents batch ingestion/index jobs from starving interactive synthesis GPUs.  
- Enables independent scaling and predictable latency for both paths (ingest vs. generate).  
  
---  
  
#### Why Postgres/Redis/object storage (durable shared state)  
Multi-user, multi-service pipelines need persistence beyond local container disks:  
- **Postgres**: sessions, metadata, runs, auditability  
- **Redis/queue/cache**: parallel worker coordination, rate limiting, short-lived state  
- **S3-compatible object storage**: source docs + generated artifacts + repeated evaluation outputs (storage grows due to iterative runs, not just raw input)  
  
---  
  
#### Why “2 replicas” for workflow UIs/services (Flowise/Langflow)  
- These components are primarily **stateless frontends**; run at least two replicas for:  
  - availability during deploys  
  - stable UX under bursts  
- Keep heavy lifting in scalable worker deployments (ingest/index/benchmark) to avoid UI contention.




