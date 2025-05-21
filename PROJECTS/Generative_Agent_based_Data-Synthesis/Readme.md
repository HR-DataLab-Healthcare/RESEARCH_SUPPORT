<span style="font-size: 13px;">

# *Privacy, Linguistic & Informational Preserving Synthesis of Clinical Data Through Generative Agents*


## Introduction

  This repository is a step-by-step guide to the Python code in the accompanying Jupyter Notebook, supplementing the paper "Privacy, Linguistic & Information Preserving Synthesis of Clinical Data Through Generative Agents" (Frontiers in AI).

  The overall aim is to process real-world PDF clinical notes, pseudonymize them for privacy, generate realistic synthetic notes based on these examples, and evaluate the quality and similarity of the synthetic data using various benchmarks.

  The process is broken down into several stages, as shown in the flow diagram below.

### User-Friendly Synthetic EHR Generation Workflow
```mermaid 

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
#
  </details>

  <details>
  <summary><h2><strong>Stage 1: PDF Text Extraction and Markdown Conversion</strong></h2></summary>

  This initial stage is crucial for transforming raw PDF documents into a structured Markdown format. This conversion makes the textual content more amenable to subsequent processing, such as pseudonymization and analysis. The process leverages an AI model for intelligent structuring of the extracted text.

  **Purpose:** To systematically extract all readable text content from a collection of PDF files and then convert this raw text into well-structured Markdown. The conversion aims to preserve or infer document elements like headings, lists, and paragraphs, utilizing the capabilities of an Azure OpenAI GPT-4.1 model.

  **Key Code Components:**

  1.  **`extract_text_from_pdf(pdf_path)`**:
      *   **Library Used:** `PyMuPDF (fitz)`
      *   **Functionality:**
          *   Opens a PDF file specified by `pdf_path`.
          *   Iterates through each page of the PDF.
          *   Extracts plain text from each page using `page.get_text("text")`.
          *   Concatenates the text from all pages, adding a double newline (`\n\n`) as a separator between page contents.
          *   Includes basic error handling to catch and report issues during PDF reading, returning `None` if an error occurs.

  2.  **`convert_text_to_markdown(text_content, pdf_filename)`**:
      *   **Library Used:** `openai` (for Azure OpenAI)
      *   **Functionality:**
          *   Takes the raw `text_content` (extracted from a PDF) and the original `pdf_filename` (for context in prompts) as input.
          *   If `text_content` is empty, it returns `None`.
          *   Constructs a request to the Azure OpenAI API using the initialized `client` object.
          *   **AI Model Invocation:**
              *   Uses the deployment specified by `AZURE_OPENAI_DEPLOYMENT_NAME` (e.g., "GPT4.1").
              *   Sends a chat completion request with:
                  *   A `system_prompt` instructing the AI to act as an assistant specialized in converting raw text to well-structured Markdown, emphasizing retention of meaning, structure, and technical details without adding conversational fluff.
                  *   A `user_prompt` that includes the `text_content` and `pdf_filename`, asking the AI to convert the text to Markdown, paying attention to potential structural elements (headings, lists, paragraphs) and to output *only* the Markdown content.
                  *   `temperature` is set to `0.2` for more deterministic and factual output.
                  *   `max_tokens` is set to `24000` to accommodate potentially large documents.
          *   Extracts the AI-generated Markdown from the API response.
          *   Includes error handling for the API call, printing an error message and returning `None` if the conversion fails.

  3.  **`save_single_markdown_file(markdown_content, output_path)`**:
      *   **Library Used:** `os` (for path manipulation, though file I/O is standard Python)
      *   **Functionality:**
          *   A utility function that takes the generated `markdown_content` string and an `output_path`.
          *   Writes the `markdown_content` to the specified `output_path` using UTF-8 encoding.
          *   Includes basic error handling for file writing operations.

  **Inputs:**

  *   A collection of original PDF files located in the directory specified by the `PDF_DIRECTORY_PATH` variable.
  *   Azure OpenAI Service Configuration:
      *   `AZURE_OPENAI_ENDPOINT`: The endpoint URL for your Azure OpenAI service.
      *   `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key (Note: This is a sensitive credential and should be managed securely, not hardcoded directly for production or shared repositories).
      *   `AZURE_OPENAI_DEPLOYMENT_NAME`: The specific deployment name of your model in Azure OpenAI Studio (e.g., "GPT4.1").
      *   `API_VERSION`: The API version for the Azure OpenAI service (e.g., "2024-12-01-preview").
  *   An initialized `AzureOpenAI` client object, configured with the above credentials.

  **Outputs:**

  *   Individual Markdown files, where each file corresponds to an input PDF.
  *   These Markdown files are named `[original_filename_without_extension].md` (e.g., `report1.pdf` becomes `report1.md`).
  *   The output Markdown files are saved directly within the `PDF_DIRECTORY_PATH`.

  **Configuration Variables Used:**

  *   `PDF_DIRECTORY_PATH`: String specifying the absolute or relative path to the directory containing the input PDF files.
  *   `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `API_VERSION`: As described under "Inputs".
  *   Prompts within `convert_text_to_markdown`:
      *   `system_prompt`: Defines the AI's role and general output requirements.
      *   `user_prompt`: Provides the specific text and instructions for the conversion task.

  **Workflow Summary:**

  The main execution block iterates through each PDF file found in `PDF_DIRECTORY_PATH`. For each PDF:
  1.  Text is extracted using `extract_text_from_pdf`.
  2.  If text extraction is successful, the text is passed to `convert_text_to_markdown`.
  3.  If Markdown conversion is successful, the resulting Markdown content is saved as an individual `.md` file using `save_single_markdown_file`.
  4.  Progress and any errors are logged to the console.
  </details>

#

<details>
  <summary><h2><strong>Stage 2: AI-Powered Pseudonymization of Markdown Content</strong></h2></summary>

  This stage is critical for protecting patient privacy. It processes the Markdown files generated in Stage 1 to identify and replace personal identifiers, specifically names, with realistic-sounding pseudonyms. This creates a safer dataset for subsequent tasks, such as training generative models or sharing example data, while aiming to preserve the original document structure and all other content.

  *   **Purpose:** To automatically replace privacy-sensitive information, focusing on person names (e.g., patients, doctors, staff, family members), with plausible, fabricated pseudonyms. This process is performed using an Azure OpenAI model, with strict instructions to *only* modify names and meticulously preserve the original Markdown formatting and all other textual content.

  *   **Key Code Components:**
      *   **`pseudonymize_markdown(markdown_content, pdf_filename)`**:
          *   **Library Used:** `openai` (for Azure OpenAI).
          *   **Functionality:**
              *   Accepts the `markdown_content` (from Stage 1) and the original `pdf_filename` (for logging/context) as input.
              *   Returns `None` if the input `markdown_content` is empty.
              *   Constructs a `pseudo_user_prompt` that combines the input `markdown_content` with explicit instructions to replace only person names and maintain Markdown integrity.
              *   **AI Model Invocation (Azure OpenAI):**
                  *   Uses the same initialized `client` object and `AZURE_OPENAI_DEPLOYMENT_NAME` (e.g., "GPT4.1") as in Stage 1.
                  *   Sends a chat completion request with:
                      *   The `PSEUDO_SYSTEM_MESSAGE_CONTENT` (see Configuration below) which strictly defines the AI's role and constraints.
                      *   The constructed `pseudo_user_prompt` containing the actual Markdown text and task instructions.
                      *   `temperature` set to `0.2` to encourage deterministic and rule-abiding output.
                      *   `max_tokens` set to `24000` (or a similar appropriate value) to handle the full document.
                  *   Extracts the pseudonymized Markdown text from the AI's response.
                  *   Includes error handling for the API call, printing an error message and returning `None` if pseudonymization fails.
      *   **`save_single_markdown_file(markdown_content, output_path)`**:
          *   This is the same helper function reused from Stage 1.
          *   It saves the pseudonymized Markdown content to a new file, typically prefixed with "pseudo_".

  *   **Inputs:**
      *   Individual Markdown files (`[original_filename].md`) generated in Stage 1, located in `PDF_DIRECTORY_PATH`.
      *   Azure OpenAI Service Configuration:
          *   `AZURE_OPENAI_ENDPOINT`: The endpoint URL for your Azure OpenAI service.
          *   `AZURE_OPENAI_DEPLOYMENT_NAME`: The specific deployment name of your model (e.g., "GPT4.1").
          *   `API_VERSION`: The API version for the Azure OpenAI service.
          *   *(API Key is configured in the environment or client initialization but not detailed here for security).*
      *   An initialized `AzureOpenAI` client object.

  *   **Outputs:**
      *   Individual pseudonymized Markdown files.
      *   Naming convention: `pseudo_[original_filename_without_extension].md` (e.g., `pseudo_report1.md`).
      *   These files are saved within the same `PDF_DIRECTORY_PATH`.

  *   **Configuration Variables Used:**
      *   `PDF_DIRECTORY_PATH`: Path to the directory containing the Markdown files.
      *   Azure OpenAI parameters: `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT_NAME`, `API_VERSION`.
      *   **`PSEUDO_SYSTEM_MESSAGE_CONTENT`**:
          ```
          "Vervang in de aangeleverde tekst uitsluitend de persoonsnamen (zoals patiëntnamen, namen van artsen, medewerkers, familieleden, etc.) door realistische, verzonnen pseudoniemen. Zorg ervoor dat de originele markdown opmaak van de tekst volledig behouden blijft. Geef als antwoord *alleen* de aangepaste tekst terug, zonder enige uitleg of extra commentaar."
          ```
          *(Translation: "In the provided text, replace only personal names (such as patient names, names of doctors, employees, family members, etc.) with realistic, fabricated pseudonyms. Ensure that the original markdown formatting of the text is fully preserved. Return *only* the modified text as the answer, without any explanation or extra commentary.")*
      *   **`PRIVACY_CATEGORIES`** (primarily for contextual understanding and potential future use in prompt refinement, though the current system prompt is highly specific to names):
          ```python
          PRIVACY_CATEGORIES = [
              "Persoonsnamen (patiënt, arts, etc.)",
              "Adressen",
              "Telefoonnummers",
              "E-mailadressen",
              "Geboortedata",
              "Burgerservicenummer (BSN) of andere ID-nummers",
              "Medische klachten, symptomen of diagnoses",
              "Medische behandelingen, medicatie of procedures",
              "Verzekeringsgegevens",
              "Financiële gegevens",
              "Andere direct identificeerbare persoonlijke informatie"
          ]
          ```

  *   **Workflow Summary:**
      The main script iterates through each Markdown file (produced in Stage 1) found in `PDF_DIRECTORY_PATH`. For each Markdown file:
      1.  The content of the Markdown file is read.
      2.  This content is passed to the `pseudonymize_markdown` function.
      3.  If the AI successfully returns pseudonymized content:
          *   The `save_single_markdown_file` function saves this modified content to a new file, prefixed with `pseudo_`.
      4.  Progress and any errors encountered during the API call or file operations are logged to the console.
      5.  The script also collects all pseudonymized content to later create a combined pseudonymized Markdown file.
</details>


<img align="right" width="240" height="240" src="./FIGs/OUPUT_1%2B2.png">

#

  <details>
  <summary><h2><strong>Stage 3: Combining Markdown Files (Optional)</strong></h2></summary>

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
  </details>

#


  <details>
  <summary><h2><strong>Stage 4: Synthetic Data Generation</strong></h2></summary>

Using the pseudonymized real data as examples and guided by detailed prompts, this stage generates entirely new, artificial patient records for low back pain.

### Code Structure and Functionality

1.  **Imports:**
    *   `os`: For interacting with the operating system, primarily for path manipulation and directory checks.
    *   `fitz` (PyMuPDF): Although imported, it's not used in the generation logic itself (likely a remnant from previous PDF processing steps).
    *   `openai.AzureOpenAI`: The core library for interacting with the Azure OpenAI service.
    *   `glob`: Used for finding files matching a specific pattern (e.g., `pseudo_*.md`).

2.  **Configuration:**
    *   **Azure Credentials:** [`AZURE_OPENAI_ENDPOINT`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb), [`AZURE_OPENAI_API_KEY`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb), [`AZURE_OPENAI_DEPLOYMENT_NAME`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb), [`API_VERSION`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) are defined to connect to the Azure service.
    *   **Directory Paths:**
        *   [`PSEUDO_MD_DIRECTORY_PATH`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb): Specifies the location of the pseudonymized Markdown files (`pseudo_*.md`) used as examples.
        *   [`SYNTHETIC_OUTPUT_DIR`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb): Defines the directory where the generated synthetic Markdown files will be saved.
    *   **Generation Control:**
        *   [`NUM_SYNTHETIC_RECORDS_TO_GENERATE`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb): Sets the number of synthetic EPDs to create.

3.  **Azure OpenAI Client Initialization:**
    *   An instance of the [`AzureOpenAI`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) client is created using the specified credentials and API version. This [`client`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) object is used for all subsequent API calls.


4.  **Helper Functions:**
    *   [`load_pseudonymized_examples(directory_path)`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb):
        *   Finds all files matching `pseudo_*.md` in the given `directory_path`.
        *   Reads the content of each found file.
        *   Formats the combined content with clear separators (`--- BEGIN VOORBEELD DOSSIER: ... ---`, `--- EINDE VOORBEELD DOSSIER ---`) to help the AI distinguish individual examples.
        *   Returns a single string containing all example content, or an empty string with a warning if no examples are found.
    *   [`generate_synthetic_record(client, example_markdown_content, record_number)`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb):
        *   **Prompts:** This function defines two key prompts to guide the AI, simulating a Supervisor-Worker interaction:
            *   **`system_prompt` (Supervisor Instructions):** Sets the AI's core **persona** and **overall task**. It instructs the AI to act as an **experienced physiotherapist** generating realistic Dutch EPDs. It establishes the **context** (using anonymized info, expert guidance), **methodology** (applying ICF framework, following KNGF low back pain guidelines), and a crucial **constraint** (produce *only* the requested patient dossier). This acts like a high-level directive from a supervisor.
            *   **`user_prompt` (Worker Instructions):** Provides the **specific, detailed, step-by-step instructions** for the *current* generation task. This acts like the specific work order given to the worker. It details:
                *   **Task Focus:** Generate *one* complete, realistic EPD *only* for low back pain (acute, subacute, or chronic). Explicitly forbids other conditions.
                *   **Required Structure and Content (in order):**
                    1.  **Anamnese Summary:** Specifies content (history, impact, coping, context), style (narrative, professional Dutch), and requirement (classify pain duration).
                    2.  **ICF-based Diagnosis:** Lists all mandatory components (impairments, limitations, restrictions, personal/environmental factors, risk factors, reformulated help request).
                    3.  **Treatment Goals:** Mandates SMART, patient-centered, functional goals (what the patient wants to do), clarifies role of clinical scores (support, not the goal itself), and requires a target date.
                    4.  **Treatment Plan:** Requires description of interventions and rationale, based on KNGF guidelines and goals.
                    5.  **SOEP Progress Notes:** Sets quantity (3-8 notes), format (full SOEP per session), and content requirements (show progression/changes, clinical reasoning).
                    6.  **Language/Style:** Demands professional Dutch, expansion of abbreviations, and realistic tone matching examples.
                *   **Example Guidance:** Injects the `example_markdown_content` as a reference for structure, style, and detail, while explicitly demanding a **new and unique** case.
                *   **Output Specification:** Instructs the AI to generate *only* the dossier content, starting with the anamnese and ending precisely with the word "FINISH". Re-emphasizes adherence to *all* instructions.
        *   **API Call:** Calls the `client.chat.completions.create` method with the system ("Supervisor") and user ("Worker") prompts, the specified model ([`AZURE_OPENAI_DEPLOYMENT_NAME`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb)), a higher `temperature` (0.8) for creativity, and sufficient `max_tokens` (8000).
        *   **Error Handling:** Catches potential API errors and returns the generated text content or `None` on failure.
    *   [`save_synthetic_record(synthetic_content, output_dir, record_number)`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb):
        *   Ensures the specified `output_dir` exists, creating it if necessary.
        *   Constructs a filename like `synthetic_patient_001.md` (using zero-padding for sorting).
        *   Writes the provided `synthetic_content` to the file using UTF-8 encoding.
        *   Handles potential file writing errors.

    *   [`load_pseudonymized_examples(directory_path)`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb):
        *   Finds all files matching `pseudo_*.md` in the given `directory_path`.
        *   Reads the content of each found file.
        *   Formats the combined content with clear separators (`--- BEGIN VOORBEELD DOSSIER: ... ---`, `--- EINDE VOORBEELD DOSSIER ---`) to help the AI distinguish individual examples.
        *   Returns a single string containing all example content, or an empty string with a warning if no examples are found.
    *   [`generate_synthetic_record(client, example_markdown_content, record_number)`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb):
        *   **Prompts:** This function defines two key prompts to guide the AI:
            *   **`system_prompt`**: Sets the AI's persona and overall task. It instructs the AI to act as a physiotherapist generating realistic Dutch EPDs based on anonymized information and expert guidance, specifically using the ICF framework and KNGF guidelines for low back pain, and to only output the requested dossier.
            *   **`user_prompt`**: Provides detailed instructions for generating *one* specific EPD. It specifies:
                *   **Condition Focus:** Generate only for acute, subacute, or chronic low back pain.
                *   **Required Sections (in order):**
                    1.  **Anamnese Summary:** Concise narrative of history, impact, coping, context; professional Dutch; specify duration (acute/subacute/chronic).
                    2.  **ICF-based Diagnosis:** Include impairments, activity limitations, participation restrictions, personal factors, environmental factors, risk/prognostic factors, and a reformulation of the patient's request for help.
                    3.  **Treatment Goals:** SMART, patient-centered, functional goals (what the patient wants to do again); clinical scores (PSK, NRS, ODI) can be used as criteria but aren't the goal itself; specify target date.
                    4.  **Treatment Plan:** Describe interventions (manual therapy, exercise, education, etc.) and rationale, based on KNGF guidelines and goals.
                    5.  **SOEP Progress Notes:** 3 to 8 separate notes (one per session) using the full SOEP format (Subjective, Objective, Evaluation, Plan); show realistic progression/stagnation/adjustments over time.
                    6.  **Language/Style:** Professional, natural Dutch; expand common abbreviations (PSK, LWK); realistic and varied tone matching examples.
                *   **Example Usage:** Explicitly includes the loaded `example_markdown_content` as a reference for structure, style, language, and detail, while demanding a completely new and unique case.
                *   **Output Format:** Generate *only* the dossier content, starting with the anamnese and ending precisely with the word "FINISH". Ensure all requested parts and instructions are followed.
        *   **API Call:** Calls the `client.chat.completions.create` method with the system and user prompts, the specified model ([`AZURE_OPENAI_DEPLOYMENT_NAME`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb)), a higher `temperature` (0.8) for creativity, and sufficient `max_tokens` (8000) for a potentially long record.
        *   **Error Handling:** Catches potential API errors and returns the generated text content or `None` on failure.
    *   [`save_synthetic_record(synthetic_content, output_dir, record_number)`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb):
        *   Ensures the specified `output_dir` exists, creating it if necessary.
        *   Constructs a filename like `synthetic_patient_001.md` (using zero-padding for sorting).
        *   Writes the provided `synthetic_content` to the file using UTF-8 encoding.
        *   Handles potential file writing errors.


5.  **Main Execution Logic (`if __name__ == "__main__":`)**
    *   Prints a starting message.
    *   Checks if the [`PSEUDO_MD_DIRECTORY_PATH`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) exists; exits with an error if not.
    *   Calls [`load_pseudonymized_examples`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) to get the example content. Issues a warning if no examples are loaded but continues execution.
    *   Enters a loop that runs [`NUM_SYNTHETIC_RECORDS_TO_GENERATE`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) times.
    *   Inside the loop, for each record:
        *   Calls [`generate_synthetic_record`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) to get the synthetic content.
        *   If generation is successful:
            *   Performs a basic check to see if the content ends with "FINISH" (as requested in the prompt) and warns if not.
            *   Calls [`save_synthetic_record`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb) to save the content to a file.
        *   If generation fails, it skips saving.
    *   Prints a completion message after the loop finishes.

### Inputs and Outputs

*   **Inputs:**
    *   Pseudonymized Markdown files (`pseudo_*.md`) located in [`PSEUDO_MD_DIRECTORY_PATH`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb).
    *   Azure OpenAI service credentials and configuration.
*   **Outputs:**
    *   Synthetic Markdown files (`synthetic_patient_*.md`) saved in [`SYNTHETIC_OUTPUT_DIR`](d:\OneDrive%20-%20Hogeschool%20Rotterdam\1_CURRENT_CODE\DE_IDENTIFY\EPD_DATA_SYNTHESIZER_GPT4.1_V01.ipynb).
    *   Progress messages printed to the console during execution.
  </details>

#


  <details>
  <summary><h2><strong>Stage 5: Synthetic Data Evaluation</strong></h2></summary>

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
  </details>

#

**REFERENCES**

#




</span>