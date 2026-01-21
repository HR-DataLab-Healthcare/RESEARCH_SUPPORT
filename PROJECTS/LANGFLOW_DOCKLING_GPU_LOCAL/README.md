Here is a comprehensive `README.md` file designed for your GitHub repository. It consolidates all the specialized steps we took to fix the Tesseract build errors and optimize the RTX 3090.

---

```markdown
# Langflow + Docling GPU Acceleration (Windows)

This repository provides a step-by-step guide to installing **Langflow** and **Docling** with full **NVIDIA GPU acceleration** on Windows using `micromamba`. This setup bypasses common C++ compilation errors associated with `tesserocr` by utilizing pre-compiled binaries.

## 🚀 System Requirements
- **OS**: Windows 10/11 (Developer Mode enabled)
- **GPU**: NVIDIA RTX Series (Tested on RTX 3090)
- **Conda Manager**: [Micromamba](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
- **OCR Engine**: Tesseract (System-level)

---

## 🛠️ Installation Guide

### 1. Create the Environment
Open PowerShell and create a clean environment with the necessary C++ dependencies for Tesseract.
```bash
micromamba create -n langflow_GPU_env python=3.10 tesserocr -c conda-forge
micromamba activate langflow_GPU_env

```

### 2. Install PyTorch (GPU Version)

Do not use the standard `pip install`. Use the dedicated NVIDIA index to ensure CUDA support.

```bash
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)

```

### 3. Install Langflow & Docling (Manual Bypass)

To avoid the `RuntimeError: Tesseract library not found` error, we install components individually to skip the broken build script.

```bash
# Install Docling without re-triggering the Tesserocr build
pip install docling --no-deps

# Install Langflow core
pip install langflow langflow-base

# Install remaining dependencies
pip install docling-core deepsearch-glm pydantic pywin32==308

```

### 4. Register Windows DLLs

Required for `pywin32` to function correctly in the environment:

```bash
python %MAMBA_ROOT_PREFIX%\envs\langflow_GPU_env\Scripts\pywin32_postinstall.py -install

```

---

## 🧪 Verification Code

Create a Jupyter Notebook and run the following cells to verify the hardware "Triple Threat" (GPU + Tesseract + Docling).

### Hardware Check

```python
import torch
import tesserocr
print(f"GPU Available: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0)}")
print(f"Tesseract: {tesserocr.tesseract_version()}")

```

### High-Performance Docling Test

This configuration is optimized for a **24GB VRAM** GPU like the RTX 3090.

```python
import time
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import ThreadedPdfPipelineOptions
from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice

# Optimized for RTX 3090
pipeline_options = ThreadedPdfPipelineOptions()
pipeline_options.accelerator_options = AcceleratorOptions(
    device=AcceleratorDevice.CUDA,
    num_threads=16 
)
pipeline_options.ocr_batch_size = 64
pipeline_options.layout_batch_size = 64

converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

# Test with a sample PDF
start = time.time()
result = converter.convert("[https://arxiv.org/pdf/2408.09869](https://arxiv.org/pdf/2408.09869)")
print(f"Processed {len(result.pages)} pages in {time.time() - start:.2f}s")

```

---

## 🖥️ Running Langflow

Once verified, launch the UI:

```bash
langflow run

```

**In the UI:** Search for the `Docling` component and ensure the `Device` parameter is set to `cuda` in the advanced settings.

## ⚖️ License

MIT

```

---

### Final Check for your Repository
If you plan on sharing this, I recommend adding a `.gitignore` file that excludes your `chroma_db/` folder and any `.ipynb_checkpoints/`.



**Would you like me to help you create an `environment.yml` file so others can replicate this entire setup with a single command?**

This [Docling GPU tutorial](https://www.youtube.com/watch?v=9gDJ6PhvVck) is helpful because it visually demonstrates the difference in processing speeds when switching from CPU to CUDA, which validates the high-performance settings we've included in your README.

```