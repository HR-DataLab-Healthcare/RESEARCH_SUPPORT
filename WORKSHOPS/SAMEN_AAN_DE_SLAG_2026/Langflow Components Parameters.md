<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## Langflow Components Parameters

Langflow nodes like URL Loader, LLM Agent, and OpenAI LLM expose tunable parameters for precision in truth-finding. Temperature controls creativity (0=deterministic, 1=random); model names select backends.[^1][^2][^3][^4]

## URL Loader Settings

| Parameter | Description | Example Values |
| :-- | :-- | :-- |
| URL | Target webpage to fetch | "https://en.wikipedia.org/wiki/World_War_I" (USER_INPUT); blank (NO_INPUT)  |
| Tool Mode | Enables agent tool call vs. direct output | ON (chat-extractable); OFF (context inject)  |
| Format | Output structure  | Text (clean read); HTML (raw); JSON (structured) |
| Loader | Fetch backend  | Default WebLoader; RequestsLoader (custom headers) |

## LLM Agent Settings

| Parameter | Description | Example Values |
| :-- | :-- | :-- |
| System Message | Grounding prompt | "Fetch URL first; answer only from content; no hallucinations" (truth mode); "Summarize freely" (creative) |
| Agent Instructions | Behavior rules ] | "You are a helpful assistant"; "Truthful fact-checker: cite text only"  |
| Tools | Connected loaders  | URL Loader only; +Calculator (math checks) |
| Language Model | Backend LLM  | OpenAI (GPT-4o); Ollama (local Llama3) [^1] |
| Max Iterations | Tool call loops | 3 (efficient); 10 (deep reasoning) |

## Language Model (OpenAI) Settings

| Parameter | Description | Example Values |
| :-- | :-- | :-- |
| Model Name | LLM variant | gpt-4o-mini (fast/cheap); gpt-4-turbo (accurate); o1-preview (reasoning)  |
| Temperature | Randomness (0-2) | 0.0 (factual, repeatable); 0.2 (balanced); 0.8 (creative summaries)  |
| API Key | Auth token  | "sk-..." (Azure OpenAI); env var \$OPENAI_API_KEY |
| Max Tokens | Output limit  | 1000 (concise); 4000 (detailed validation) |
| Top P | Nucleus sampling | 0.9 (diverse); 1.0 (full) |

## Chat Input/Output Settings

| Parameter | Description | Example Values |
| :-- | :-- | :-- |
| Session ID | Chat history  | auto; "wwi-truth-1" (persistent) |
| Placeholder | User prompt hint  | "Ask + URL: Validate trench myth" |
| Temperature Override | Per-chat control | 0.1 (strict fact-check) |

Tune for WWI validation: Set Temperature=0, Model=gpt-4o-mini, URL pre-loaded, System="Validate myths from fetched text only". Test iterations via playground.

<div align="center">⁂</div>

[^1]: paste.txt

[^2]: image.jpg

[^3]: NO_INPUT_FLOW.jpg

[^4]: USER_INPUT_FLOW.jpg

