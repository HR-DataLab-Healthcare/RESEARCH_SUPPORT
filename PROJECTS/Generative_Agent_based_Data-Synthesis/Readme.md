<span style="font-size: 13px;">

# *Privacy, Linguistic & Informational Preserving Synthesis of Clinical Data Through Generative Agents*



```mermaid 

flowchart LR
    id1(User-Friendly Synthetic EHR Generation Workflow)
graph TD  
  subgraph "      "
    A[Collect Real EHR Samples] --> B[Pseudonymization of EHR Samples]  
    B --> C[Store in Data Warehouse]  
    C --> D[Compute Resources Setup: Cloud & Local]  
    D --> E[Toolchain Setup: Docker, Flowise, Hugging Face Spaces]  
    E --> F[Multi-Agent Workflow Orchestration]  
    F --> G[Supervisor Agent]  
    F --> H[Worker Agent]  
    G --> I[Prompt Engineering: Clinical Guidelines & Standards]  
    H --> I  
    I --> J[Generative AI Model: GPT-4.1]  
    J --> K[Generate Synthetic EHR]  
    K --> L[Validate Synthetic EHR Realism & Clinical Accuracy]  
    L --> M[Deploy Synthetic EHR Application via Secure API Endpoint]  
  end  
  subgraph Iterative Refinement & Evaluation  
    K --> N[Quantitative Assessment: Entropy, JSD, PMI, BLEU, BERTScore, Classifier Metrics]  
    N --> O[Expert Human Validation]  
    O --> K  
  end
  
  ```  


## 1. Introduction
This repository is a step-by-step guide to the Python code in the accompanying Jupyter Notebook, supplementing the paper "Privacy, Linguistic & Information Preserving Synthesis of Clinical Data Through Generative Agents" (Frontiers in AI).

The overall aim is to process real-world PDF clinical notes, pseudonymize them for privacy, generate realistic synthetic notes based on these examples, and evaluate the quality and similarity of the synthetic data using various benchmarks.

The process is broken down into several stages, leveraging the International Classification of Functioning (ICF) model, KNGF low back pain guidelines, and Azure OpenAI's GPT models for different tasks.

**Prerequisites:**

* Python installed with necessary libraries (openai, fitz, sacrebleu, bert\_score, numpy, glob, os, time, json, math, collections). You might need to install these using pip install \-r requirements.txt if you have a requirements file, or individually:  
  pip install openai PyMuPDF sacrebleu bert-score numpy

* Access to an Azure OpenAI endpoint with deployment(s) for a suitable model (e.g., gpt-4 for conversion, pseudonymization, generation, and qualitative comparison).  
* Your Azure OpenAI configuration details (AZURE\_OPENAI\_ENDPOINT, AZURE\_OPENAI\_API\_KEY, AZURE\_OPENAI\_DEPLOYMENT\_NAME, API\_VERSION) set up correctly (e.g., as environment variables or defined at the beginning of your notebook/script).  
* Original PDF files located in the specified input directory (PDF\_DIRECTORY\_PATH).

## **Stage 1: PDF Text Extraction and Markdown Conversion**

This initial stage focuses on converting the raw PDF documents into a structured text format (Markdown) that is easier to process in subsequent steps.

* **Purpose:** To extract readable text content from PDF files and convert it into a structured Markdown format, preserving headings, lists, and paragraphs where possible, using an AI model.  
* **Key Code Components:**  
  * extract\_text\_from\_pdf(pdf\_path): A function that reads text content from each page of a given PDF file using the PyMuPDF library (fitz).  
  * convert\_text\_to\_markdown(text\_content, pdf\_filename): A function that sends the extracted raw text to Azure OpenAI (using the client object and the specified AZURE\_OPENAI\_DEPLOYMENT\_NAME) with a prompt instructing the model to format the text as Markdown.    
  * save\_single\_markdown\_file(markdown\_content, output\_path): A helper function to save the resulting Markdown content string to an individual file.  
* **Inputs:**  
  * Original PDF files from the directory specified by PDF\_DIRECTORY\_PATH.  
  * Azure OpenAI API configuration and initialized client object.  
* **Outputs:**  
  * Individual Markdown files (\[original\_filename\].md) created within the PDF\_DIRECTORY\_PATH.  
* **Configuration:**  
  * PDF\_DIRECTORY\_PATH: Specifies the file path where the input PDFs are located.  
  * Azure OpenAI endpoint, key, deployment name (using AZURE\_OPENAI\_DEPLOYMENT\_NAME for the Markdown conversion task), and API version.  
  * The convert\_text\_to\_markdown function uses specific system and user prompts to guide the AI's formatting task.

## **Stage 2: Pseudonymization**

To protect patient privacy and create a safe dataset for further use (like example data for generation), this stage identifies and replaces personal identifiers in the Markdown files.

* **Purpose:** To replace privacy-sensitive information, specifically person names (patients, doctors, staff, etc.), with realistic-sounding pseudonyms while strictly preserving the original Markdown structure and content otherwise, using an AI model.  
* **Key Code Components:**  
  * pseudonymize\_markdown(markdown\_content, pdf\_filename): A function that sends the Markdown text (generated in Stage 1\) to Azure OpenAI (using the client object and AZURE\_OPENAI\_DEPLOYMENT\_NAME) with a strict system prompt instructing the model *only* to replace names and retain Markdown formatting.  
  * save\_single\_markdown\_file(markdown\_content, output\_path): Reused helper function to save the pseudonymized Markdown content to a new file.  
* **Inputs:**  
  * Individual Markdown files (\*.md) generated in Stage 1\.  
  * Azure OpenAI API configuration and initialized client object.  
* **Outputs:**  
  * Individual pseudonymized Markdown files (pseudo\_\[original\_filename\].md) created within the PDF\_DIRECTORY\_PATH.  
* **Configuration:**  
  * Azure OpenAI endpoint, key, deployment name (AZURE\_OPENAI\_DEPLOYMENT\_NAME), and API version.  
  * PSEUDO\_SYSTEM\_MESSAGE\_CONTENT: A crucial system prompt that strictly limits the AI's action to name replacement and markdown preservation.  
  * PRIVACY\_CATEGORIES (optional list, mainly for context).

## **Stage 3: Combining Markdown Files (Optional)**

This stage is primarily for creating single files containing the processed data, which can be useful for reviewing the entire dataset or for simple corpus loading, although the subsequent stages load individual files.

* **Purpose:** To concatenate the content of all individual Markdown files (both original converted and pseudonymized) into two single, large Markdown files.  
* **Key Code Components:**  
  * save\_combined\_markdown\_to\_file(combined\_markdown\_content, output\_path, file\_description): A helper function to write the combined string to a specified file.  
* **Inputs:**  
  * Individual Markdown files (\*.md and pseudo\_\*.md) from the PDF\_DIRECTORY\_PATH.  
* **Outputs:**  
  * combined\_epds\_markdown.md (all original converted content) saved in the parent directory of PDF\_DIRECTORY\_PATH.  
  * pseudo\_combined\_epds\_markdown.md (all pseudonymized content) saved in the parent directory of PDF\_DIRECTORY\_PATH.  
* **Configuration:**  
  * OUTPUT\_COMBINED\_MD\_FILE\_PATH, OUTPUT\_COMBINED\_PSEUDO\_MD\_FILE\_PATH: Define the output locations and filenames.

*Note: The main execution block in the initial script handles the looping through files, calling the extraction/conversion/pseudonymization functions, appending content to lists (all\_markdown\_content, all\_pseudonymized\_content), and finally joining and saving the combined content.*

## **Stage 4: Synthetic Data Generation**

Using the pseudonymized real data as examples and guided by detailed prompts, this stage generates entirely new, artificial patient records for low back pain.

* **Purpose:** To create a dataset of synthetic physiotherapeutic EHR records that are realistic, follow clinical guidelines (KNGF low back pain), adhere to the ICF model, and mimic the structure and style of the real, pseudonymized data, but represent entirely new patient cases.  
* **Key Code Components:**  
  * load\_pseudonymized\_examples(directory\_path): Reads content from the individual pseudo\_\*.md files to be included as examples in the AI generation prompt.  
  * generate\_synthetic\_record(client, example\_markdown\_content, record\_number): Constructs a detailed user prompt combining the Worker persona, specific instructions (ICF, KNGF, SOEP format, goal formulation, low back pain focus), and the loaded examples. Sends this to Azure OpenAI (using the client object and AZURE\_OPENAI\_DEPLOYMENT\_NAME) to generate a new, unique record.  
  * save\_synthetic\_record(synthetic\_content, output\_dir, record\_number): Saves the generated synthetic record to an individual file in a new directory.  
* **Inputs:**  
  * Individual pseudonymized Markdown files (pseudo\_\*.md) from the directory specified by PSEUDO\_MD\_DIRECTORY\_PATH (which is set to reuse the original PDF\_DIRECTORY\_PATH in the provided code).  
  * Azure OpenAI API configuration and initialized client object.  
  * Detailed AI prompts defining the structure and clinical requirements for synthetic data (Supervisor and Worker prompts conceptually translated into the system and user messages).  
* **Outputs:**  
  * Individual synthetic Markdown files (synthetic\_patient\_\*.md) created in a new output directory specified by SYNTHETIC\_OUTPUT\_DIR.  
* **Configuration:**  
  * PSEUDO\_MD\_DIRECTORY\_PATH: The source directory for pseudonymized example data.  
  * SYNTHETIC\_OUTPUT\_DIR: The output directory where synthetic data will be saved.  
  * NUM\_SYNTHETIC\_RECORDS\_TO\_GENERATE: Controls how many synthetic files to create.  
  * Azure OpenAI endpoint, key, deployment name (AZURE\_OPENAI\_DEPLOYMENT\_NAME for generation), and API version.  
  * System and user prompts for the generation task. A higher temperature (0.8) is used here to encourage creativity and variation in the generated content.

## **Stage 5: Synthetic Data Evaluation**

This final stage assesses the quality and similarity of the generated synthetic data compared to the pseudonymized real data using a combination of quantitative benchmarks and a qualitative AI-based review.

* **Purpose:** To provide metrics and descriptions that indicate how well the synthetic data captures the linguistic, structural, and clinical characteristics of the real-world pseudonymized data.  
* **Key Code Components:**  
  * load\_file\_content(filepath): Helper function to load content for evaluation.  
  * calculate\_entropy(text, unit): Calculates Shannon's Entropy (character and word level) for the entire corpus of pseudonymized and synthetic texts, measuring linguistic diversity.  
  * calculate\_avg\_bigram\_pmi(text, min\_freq): Calculates the average Pointwise Mutual Information (PMI) for word bigrams above a minimum frequency threshold, serving as a proxy for Mutual Information and measuring word association strength.  
  * calculate\_corpus\_bleu(synthetic\_contents, pseudo\_contents\_list): Calculates the corpus-level BLEU score, measuring n-gram overlap between synthetic texts and the reference set of pseudonymized texts. Requires the sacrebleu library.  
  * calculate\_corpus\_bertscore(synthetic\_contents, pseudo\_contents\_list, lang='nl'): Calculates the BERT Score (Precision, Recall, F1), measuring semantic similarity using contextual embeddings. Requires the bert\_score library.  
  * compare\_docs\_with\_gpt4(client, pseudo\_content, synthetic\_content, pseudo\_filename, synthetic\_filename): Sends pairs of pseudonymized and synthetic texts to Azure OpenAI (using the client object and AZURE\_OPENAI\_DEPLOYMENT\_NAME) with a prompt asking for a qualitative comparison based on structure, style, clinical patterns, and realism, providing a descriptive summary and a rating (Laag/Matig/Hoog).  
  * Code to load *all* contents from both corpora, calculate the quantitative benchmarks, perform pairwise GPT-4 comparisons (randomly pairing synthetic files with pseudonymized ones up to NUM\_COMPARISON\_PAIRS\_TO\_EVALUATE), print all results in a structured report, and optionally save to a JSON file (COMPARISON\_RESULTS\_FILE).  
* **Inputs:**  
  * Individual pseudonymized Markdown files (pseudo\_\*.md) from PSEUDO\_MD\_DIRECTORY\_PATH\_COMPARE.  
  * Individual synthetic Markdown files (synthetic\_patient\_\*.md) from SYNTHETIC\_MD\_DIRECTORY\_PATH.  
  * Azure OpenAI API configuration and initialized client object (specifically for the qualitative GPT-4 comparison part).  
* **Outputs:**  
  * Quantitative benchmark values (Character Entropy, Word Entropy, Average Document Length, Average Bigram PMI, BLEU Score, BERT Score) printed to the console.  
  * Qualitative comparison summaries and ratings from GPT-4 for sampled pairs, printed to the console.  
  * Optional JSON file (COMPARISON\_RESULTS\_FILE) containing all benchmark and pairwise results.  
* **Configuration:**  
  * PSEUDO\_MD\_DIRECTORY\_PATH\_COMPARE: Source directory for pseudonymized files used as references for comparison.  
  * SYNTHETIC\_MD\_DIRECTORY\_PATH: Source directory for synthetic files.  
  * NUM\_COMPARISON\_PAIRS\_TO\_EVALUATE: How many synthetic files to sample for the pairwise GPT-4 comparison.  
  * PMI\_MIN\_BIGRAM\_FREQ: Minimum frequency for a bigram to be included in the Average PMI calculation.  
  * Azure OpenAI endpoint, key, deployment name (AZURE\_OPENAI\_DEPLOYMENT\_NAME for the comparison task), and API version. A lower temperature (0.1) is used for the comparison prompt to encourage deterministic analysis.  
  * The prompt for compare\_docs\_with\_gpt4 explicitly defines the comparison criteria and output format.  
* **Benchmark Metrics Explained:**  
  * **Shannon's Entropy (Character/Word):** Measures linguistic diversity and unpredictability at the character or word level. Higher values indicate more variety.  
  * **Average Document Length (Characters):** A simple measure of the average size or volume of content per document.  
  * **Average Bigram Pointwise Mutual Information (PMI):** A proxy for Mutual Information, measuring the average strength of association between adjacent words. Higher values suggest stronger or more specific word co-occurrence patterns.  
  * **BLEU Score:** Measures surface-level n-gram overlap. A low score is generally desired for synthetic data to show it's not copying phrasing.  
  * **BERT Score (Precision, Recall, F1):** Measures deeper semantic similarity using contextual embeddings. F1 provides a balanced score of how well the synthetic data captures the meaning and concepts of the real data.  
  * **Informational Accuracy:** A standard, generalizable metric is noted as challenging in this context. Aspects of information capture and clinical plausibility are covered qualitatively by the GPT-4 comparison and partially by BERTScore (semantic similarity) and length comparison.  
  * **Qualitative GPT-4 Comparison:** Provides a human-like assessment by an AI model, evaluating structure, style, clinical realism, and adherence to format based on explicit criteria, offering a descriptive summary and a categorical rating (Laag/Matig/Hoog).

This guide provides a structured overview of the code's functionality across the different stages of processing, generating, and evaluating the physiotherapeutic EHR data. Refer to the code cells in the notebook for the specific implementation details of each function and the main execution flow.

</span>