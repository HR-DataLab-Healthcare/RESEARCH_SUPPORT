## HR-DataLab Healthcare

We are a cross-functional Agile team. Consisting of data scientists + Tech support.
Our team exists of 5 members that itertively define, build, test, and deploy tool-chain workflows for *Healtcare Data Science Use Cases*.
Here we present a Gen-AI approach that allows Healthcare specilatists to perfom innovative research with custom-made Large Language Models workflows. 



## Building  user-centered intelligent multi-agent systems for information retrieval 

The integration of generative AI in healthcare is rapidly transforming the industry, enabling medical professionals to leverage advanced AI capabilities without extensive coding expertise. Today, rapid prototyping tools offer intuitive user interfaces along with custom-made components that allow to solve complex medical tasks, including automated clinical documentation, diagnostic support, and large-scale data analysis.


| Type | Tools | Key Features    | Target Audience |
|------|-------|-----------------|-----------------|
| Multi-Agent Frameworks | AutoGen, CrewAI, LangGraph | • Complex AI agent systems<br>• Collaborative workflows<br>• Stateful interactions | Developers, AI Engineers |
| Low-Code/No-Code Solutions | Flowise, n8n | • Visual interfaces<br>• Drag-and-drop functionality<br>• Workflow automation<br>• LLM integration | Beginners, Non-Developers, Rapid Prototypers, System Integrators, Healthcare Professionals (for Flowise) |
| LLM Application Frameworks | Hugging Face, Ollama, LangChain, Ollama | • External data source integration<br>• Specialized indexing and querying<br>• Versatile LLM application development | Developers, AI Engineers, Data Scientists |
| Comprehensive Platforms | Vertex AI | • End-to-end machine learning platform<br>• Model building, deployment, and scaling<br>• Data labeling and training tools | Machine Learning Engineers, Data Scientists, Medical Professionals (for healthcare applications) |
| Development Environments | Replit | • Browser-based IDE<br>• LLM API experimentation<br>• Collaborative coding<br>• Rapid prototyping | Developers, Beginners, AI Enthusiasts |

<br> 
The tools as described above represent a spectrum of approaches to AI development, ranging from code-centric frameworks for building complex multi-agent systems to visual, low-code/no-code platforms for rapid prototyping and workflow creation. The diverse range of tools reflects the evolving ecosystem of AI development, catering to both experienced developers and those seeking accessible, user-friendly solutions.

<br> 
By reducing technical barriers, rapid prototyping tools like "Flowise" allow healthcare professionals to focus on their domain expertise rather than solving complex coding problems. This paves the way for more accessible and widespread adoption of Generative AI in healthcare research.

<br> 

## Deploing Gen-AI for secure and reliable information retrieval

To construct a secure, containerized LLM workflow ecosystem, you need a layered approach combining orchestration and specialized LLM toolchains along with Retrieval-Augmented Generation. RAG represents a paradigm shift in generative AI by combining retrieval mechanisms with generation capabilities to produce reliable, context-aware outputs across various domains. Below is shown a generic framework based on Data Science best practices.


<img align="left" width="450" height="250" src="image.png">
At its core (Warehousing + Compute layers), Docker can provide the containerization foundation, while tools like Flowise or Autogen can be used to orchestrate the entire workflow (Software Architecure level). For open-source LLM deployments in particular, the Hugging Face Transformers platform offers an LLM Repository combined with Inference Endpoints (Deployment level). 

<br> 
<br> 
<br> 
<br> <br>

When using an Inference Endpoint, the huggingface platform creates a specialized version of the model that's ready to be used, either based on the model you choose or a custom-made package you provide such as Flowise or AutoGen. 

<br> 

<img align="left" width="450" height="250" src="image-1.png">
 It is kept separate from the original model files, which is crucial for ensuring security by preventing unauthorized access or tampering, and reliability by maintaining consistent performance without unexpected changes or breaks. 
Thus endpoints represent a managed infrastructure solution that allows users to deploy and run machine learning models in a secure and scalable environment, allowing users to focus on deploying and using their models without worrying about the technical details of hosting and maintenance 

https://huggingface.co/docs/inference-endpoints/en/index.

<br>
<br>
<br>

# Clinical Reasoning for Nurse Specialists

We developed a multi-agent LLMs-based Hugging-face space Chatbot
that allows researchers to process and analyze text documents reliably and securely. 

```C
The information retrieval workflow is designed with 
a highly experienced and knowledgeable nurse as the end user. 

The nurses task is to provide a sound clinical reasoning report 
based on an patient-nurse dialogue transcript.

The clinical reasoning must be based upon NANDA International (NANDA-I) Taxonomy II
By utilizing its structured framework of 
13 domains, 47 classes, and over 267 nursing diagnosis labels, 
the taxonomy enables systematic organization and interpretation 
of patient data derived from nurse-patient dialogues. 
```

<br>

Shown below is part of the output as produced by the implemented information retrieval workflow 
and the goals of the nurse using this system. <br> <br> 

![alt text](image-5.png)





=================================================

## Clinical Reasoning Workflow Using NANDA International Taxonomy II

A [demo video](https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/blob/main/PROJECTS/Harnessing%20the%20Power%20of%20Gen-AI%20in%20Research/VIDEO/) that includes each functional component  
as described below: <br> <br>  



```C
1. Recruiter Character Test

- **Purpose**: Assesses initial information retrieval characteristics
- **Relevance**: Ensures effective interpretation and action on clinical data


2. Azure OpenAI Embedding

- **Purpose**: Embeds input data into structured format
- **Relevance**: Captures context and nuances of patient-nurse dialogues


3. PDF Tool

- **Purpose**: Processes PDF files, particularly patient-nurse dialogue transcripts
- **Relevance**: Extracts crucial patient information for NANDA-I interpretation


4. Memory Vector Store

- **Purpose**: Stores embeddings as a repository for contextual data
- **Relevance**: Enables quick retrieval of relevant patient information


5. Retriever Tool

- **Purpose**: Retrieves data from memory vector store based on embeddings
- **Relevance**: Accesses specific information from past dialogues for clinical reasoning


6. Worker

- **Purpose**: Processes aggregated information (transcripts + provided NANDA document) to formulate insights or reports
- **Relevance**: Utilizes the provided knowledge to produce clinically sound reports based on NANDA-I taxonomy


7. Supervisor

- **Purpose**: Monitors process for quality and protocol adherence
- **Relevance**: Validates clinical reasoning and ensures alignment with NANDA-I standards


8. SQLite Agent Memory

- **Purpose**: Stores and retrieves data efficiently during workflow
- **Relevance**: Enables quick access to relevant context from previous dialogues turns

```

The entire workflow is designed to support the experienced nurse in synthesizing key insights from patient interactions efficiently. By utilizing NANDA International's structured approach, the nurse can categorize patient information accurately, leading to better clinical reasoning and patient outcomes. Each component ensures that the nurse has the tools necessary to interpret, analyze, and apply patient data effectively while adhering to established nursing diagnoses standards.

#
#




