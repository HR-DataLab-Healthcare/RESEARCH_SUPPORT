## QoLEAD LLMs-based secure and Reliable WORKFLOW
We zijn een cross-functioneel Agile team. Bestaande uit  datawetenschappers + Tech support. 

In collaboration with [CAPRI](https://www.maastrichtuniversity.nl/research/care-and-public-health-research-institute) we develop and maintain a LLMs-based workflow that allows researchers to process & analyze  text documents reliably and securely.  The code needed to implement the workflow can be downloaded from [Qolead workfow code](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/QoLEAD/code) and is explained below.</br></br>

The here presented code is based on the following references
* [Retrieval-Augmented Generation (RAG) with open-source Hugging Face LLMs using LangChain](https://medium.com/@jiangan0808/retrieval-augmented-generation-rag-with-open-source-hugging-face-llms-using-langchain-bd618371be9d)
* [Advanced RAG: Extracting Complex PDFs containing tables & Text Using LlamaParse](https://aksdesai1998.medium.com/advanced-rag-extracting-complex-pdfs-containing-tables-text-using-llamaparse-48b61693da58)
* [State-of-art retrieval-augmented LLM: bge-large-en-v1.5](https://medium.com/@marketing_novita.ai/state-of-art-retrieval-augmented-llm-bge-large-en-v1-5-4cd5abbcbf0a)
* [PyPDF](https://api.python.langchain.com/en/latest/document_loaders/langchain_community.document_loaders.pdf.PyPDFLoader.html)
* [Question Answering (QA) quickstart](https://python.langchain.com/v0.1/docs/use_cases/question_answering/quickstart/)
* [Vectorstores](https://python.langchain.com/docs/integrations/vectorstores/lancedb/)
* [Vectorstores](https://python.langchain.com/v0.1/docs/modules/data_connection/vectorstores/)
* [Chat Openai](https://python.langchain.com/docs/integrations/chat/azure_chat_openai/)


### RAG explained 
Retrieval-Augmented Generation (RAG) revolutionizes text generation by bridging the gap between factual accuracy and creative language. By dynamically accessing and incorporating relevant information, RAG algorithms can generate text that is not only well-written but also grounded in real-world knowledge.


### Library installation

Add these line to your notebook:
```python
# ===> general Data Science packages 
!pip install -U ipykernel jupyter ipywidgets numpy pandas shutup PyPDF2

# ===> NLP packages needed for LangChain + Huggingface platforms
!pip install -U transformers sentence_transformers langchain_community fais-cpu 
!pip install -U torch torchvision torchaudio 

# When GPU available use: [requires Python 3.9 or later](https://pytorch.org/)
!pip install -U torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

### Library Configuration
List of all imports needed to make the code work

import os
from urllib.request import urlretrieve
import numpy as np
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.llms import HuggingFacePipeline
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
```
</br> 

### Create a map to store and load PDF files locally

```python
import os
# Download documents to local directory (here called LAWTON)
os.makedirs("LAWTON", exist_ok=True)


# load all PDFs that are stored in the local-direcory
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
loader = PyPDFDirectoryLoader("./LAWTON/")
```


### Document preparation
PDF documents must be locally available and split in smaller chunks for a LLM to use them as a knowledge base.

Documents should be:

* Large enough to contain enough tokens to answer a question truthfully.
* Small enough to fit into the LLM prompt: Mistral-7B-v0.1 input tokens limited to 4096 tokens
* Small enough to fit into the embeddings model: BAAI/bge-large-en-v1.5: input tokens limited to 512 tokens (roughly 2000 characters. Note: 1 token ~ 4 characters). Note however, set truncation=True to increase to the maximum number of input tokens allowed.


```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load pdf files in the local directory
loader = PyPDFDirectoryLoader("./LAWTON")

docs_before_split = loader.load()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 900,
    chunk_overlap  = 50,
)
docs_after_split = text_splitter.split_documents(docs_before_split)

docs_after_split[0]
```


### Text Embeddings with Hugging Face models
At the time of writing (nov 2024), 213 text embeddings models for English are available on the Massive Text Embedding Benchmark [MTEB](https://huggingface.co/spaces/mteb/leaderboard). See also [2023 paper on MTEB](https://aclanthology.org/2023.eacl-main.148.pdf). Also [Models trained on Dutch vocabulary](https://huggingface.co/GroNLP/gpt2-small-dutch-embeddings) are available.

The **"Alibaba-NLP/gte-large-en-v1.5"** model is the 18th  on MTEB leaderboard. Key characteristics are:

* Language: English
* Model Size: 434
* Max Sequence Length: 8192
* Dimension: 1024

These numbers indicate that the model can handle long pieces of text (up to 8192 tokens) and produces embeddings with 1024 dimensions. This makes it perfect for tasks like text retrieval, question answering, and more. </br> </br>
The gte-large-en-v1.5 model, developed by the Institute for Intelligent Computing, Alibaba Group, is a powerful tool for natural language processing tasks. It’s a type of Text Embeddings model, which means it’s great at understanding the meaning of text.

To use it locally, the [sentence_transformers](https://api.python.langchain.com/en/latest/embeddings/langchain_community.embeddings.huggingface.HuggingFaceBgeEmbeddings.html#langchain-community-embeddings-huggingface-huggingfacebgeembeddings.) python package needs to be installed. 


```python
import torch
from torch import cuda, bfloat16
from transformers import AutoTokenizer, AutoModel

device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
display(torch.cuda.is_available())

### ===> takes about 60 seconds to complete the process

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
### EMBEDDING models
# https://python.langchain.com/docs/integrations/text_embedding/


model_name = "Alibaba-NLP/gte-large-en-v1.5"

model_kwargs = {'device': 'cuda', # use: 'cuda' for GPU use, else use:  'cpu' 
                'trust_remote_code':True
                } 

encode_kwargs = {'normalize_embeddings': True,
                 'truncate':True # truncate the input to the maximum length the model can handle
                 }  

### Create the embeddings object
huggingface_embeddings = HuggingFaceBgeEmbeddings(
                                                    model_name=model_name,
                                                    model_kwargs=model_kwargs,
                                                    encode_kwargs=encode_kwargs,
)

```
