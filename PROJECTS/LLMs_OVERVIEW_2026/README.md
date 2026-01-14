# Epoch AI Models Dataset

Epoch AI's database tracks over 3,200 notable machine learning models from 1950 to present, providing comprehensive data on training compute, parameters, dataset sizes, and hardware trends.

This resource enables Tech Leads to benchmark infrastructure needs, forecast compute scaling, and align AI development strategies with industry frontiers.


<img src="compute-trend-post-2010.png" style="height:400px;margin-right:200px"/>

## Usefulness for Tech Leads

- **Infrastructure Planning**: Training compute has grown 4.4x/year since 2010; power needs double annually for frontier models, guiding cluster sizing and energy budgeting.
- **Cost Forecasting**: Largest models cost hundreds of millions, doubling every 8 months; ~50% GPU spend helps prioritize hardware investments.
- **Trend Analysis**: >30 models exceed GPT-4 scale (10^25 FLOP) as of mid-2025; track frontier thresholds evolving with top-10 compute releases.
- **Regulatory Awareness**: Large-scale models (>10^23 FLOP) trigger EU AI Act rules since August 2025, informing compliance roadmaps.
- **Benchmarking**: Compare against state-of-the-art (SOTA) models, highly cited (>1000 citations), or historically significant releases.


## Technical Details

**Dataset Scope**: Covers notable models (SOTA benchmarks, >1M users, >\$1M cost, historical relevance); frontier (top-10 compute at release); large-scale (>10^23 FLOP).

**Key Metrics**:


| Metric | Description | Growth Rate | Confidence Levels |
| :-- | :-- | :-- | :-- |
| Training Compute | FLOP used | 4.4x/year (2010+) | Confident (±3x), Likely (±10x), Speculative (±30x) |
| Parameters | Model size | Tracked via architecture | Per-entry estimation notes |
| Dataset Size | Tokens used | Estimated from publications/hardware | - |
| Hardware | GPUs/TPUs, clusters | Larger clusters dominate since 2018 | - |
| Power Draw | Training energy | 2x/year | Methodology detailed |

**Estimation Methods**: Direct from papers where available; inferred from architecture, hardware/duration otherwise. Updated weekly via automated search + manual review; major models added <2 weeks post-release.
## Quickstart

```python
import pandas as pd

# Load full dataset (CSV, ~November 2025 snapshot; check epoch.ai for latest)
url = "https://epoch.ai/data/all_ai_models.csv"
df = pd.read_csv(url)

# Explore frontier models
frontier = df[df['frontier'] == True]
print(frontier[['name', 'training_compute', 'release_date']].sort_values('training_compute', ascending=False))
```

**Downloads** [epoch.ai/data/ai-models]:

- All Models CSV
- Notable/Frontier/Large-Scale subsets


## Citation \& License

CC-BY: Credit Epoch AI. BibTeX available on site.

```
@misc{EpochAIModels2025,
  title = {Data on AI Models},
  author = {{Epoch AI}},
  year = {2025},
  url = {https://epoch.ai/data/ai-models}
}
```

 ---

#### REFERENCES / USED ONLINE RECOURCES

* https://epoch.ai/data/ai-models

* https://epoch.ai/data

* https://github.com/epoch-research

* https://github.com/epoch-research/ai-research-impact
