## QoLEAD LLMs-based secure and Reliable WORKFLOW
We zijn een cross-functioneel Agile team. Bestaande uit  datawetenschappers + Tech support. 

In collaboration with [CAPRI](https://www.maastrichtuniversity.nl/research/care-and-public-health-research-institute) we develop and maintain a LLMs-based workflow that allows researchers to process & analyze  text documents reliably and securely.  The code needed to implement the workflow can be downloaded from [Qolead workfow code](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/tree/main/PROJECTS/QoLEAD/code) and is explained below.</br></br>

The here presented code is based on the following references
* [Retrieval-Augmented Generation (RAG) with open-source Hugging Face LLMs using LangChain](https://medium.com/@jiangan0808/retrieval-augmented-generation-rag-with-open-source-hugging-face-llms-using-langchain-bd618371be9d)
* [Advanced RAG: Extracting Complex PDFs containing tables & Text Using LlamaParse](https://aksdesai1998.medium.com/advanced-rag-extracting-complex-pdfs-containing-tables-text-using-llamaparse-48b61693da58)
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
!pip install -U sentence_transformers langchain_community fais-cpu 
```

### Library Configuration
List of all imports to make the code work
```python
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

### Document preparation
PDF documents must be locally available and split in smaller chunks for a LLM to use them as a knowledge base.

Documents should be:

* large enough to contain enough information to answer a question, and
* small enough to fit into the LLM prompt: Mistral-7B-v0.1 input tokens limited to 4096 tokens
* small enough to fit into the embeddings model: BAAI/bge-small-en-v1.5: input tokens limited to 512 tokens (roughly 2000 characters. Note: 1 token ~ 4 characters).


```python
# Load pdf files in the local directory
loader = PyPDFDirectoryLoader("./us_census/")

docs_before_split = loader.load()
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 700,
    chunk_overlap  = 50,
)
docs_after_split = text_splitter.split_documents(docs_before_split)

docs_after_split[0]
```