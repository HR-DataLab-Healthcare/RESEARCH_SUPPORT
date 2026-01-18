# LLM Truth-Finding Workshop for WWI Text Validation

This workshop guides naive researchers through using a Langflow-based LLM agent playground to perform fact-checking on the WWI text at [TEXT_ON_WWI.html](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/TEXT_ON_WWI.html). The playground, accessible via [SAMEN_AAN_DE_SLAG_2026](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/index.html), employs a retrieval-augmented agent grounded in fetched web content for truthful validation.

## Flow Explanation

The Langflow in the image depicts a chat-based LLM agent system with grounding for accuracy. Core components include a URL Loader (fetches web content), LLM Agent (processes queries using tools), System Message (enforces tool use and truthfulness), and Chat Input/Output for interaction. Connections route user input through language models and tools to generate grounded responses, preventing hallucinations by mandating URL fetches before answering.

The agent operates in two modes: tool mode (user provides URL in chat, agent extracts and fetches) or context injection (pre-fetched content fed directly). Instructions like "You must use the URL tool to fetch content... Answer only based on fetched content. Do not hallucinate" ensure responses stay factual.

## Component Table

| Component | Function | Usage for Truth-Finding |
| :-- | :-- | :-- |
| URL Loader | Fetches raw text from provided URLs (e.g., Wikipedia) | Input target page like Wikipedia WWI; agent reads it as primary source 
| LLM Agent | Reasons over fetched content using tools; extracts links from chat | Queries like "Is X true per this page?" trigger fetch and validation  |
| System Message | "Always fetch URL first; answer only from content; say 'not in text' if absent" | Forces grounding; blocks external knowledge or fabrication |
| Chat Input | User enters question + URL (e.g., "Validate trench myth https://en.wikipedia.org/wiki/World_War_I")  | Enables dynamic truth missions on WWI misconceptions|
| Language Model | Powers agent (e.g., OpenAI); parses and summarizes grounded data | Outputs verified facts or admissions of absence |

This table educates beginners: paste URL into chat, ask validation questions, get evidence-based replies.

## Workshop Steps

- **Access Playground**: Open [index.html](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/index.html); no install needed.[^2]
- **Load WWI Text**: Copy TEXT_ON_WWI.html content or URL into chat; note embedded myths (e.g., "trenches everywhere", "Spanish Flu from Spain").[^1]
- **Validate Systematically**:
    - Test trench scope: "Did all fronts use trenches only? Fetch https://en.wikipedia.org/wiki/World_War_I".[^1]
    - Check flu origin: "Where did Spanish Flu start per page?" Expect correction to Kansas/France.[^1]
    - Probe generals: "Did generals avoid front lines?" Agent reveals >200 casualties.[^1]
    - Query US role: "Did US instantly win war?" Highlights prior Allied gains.[^1]
- **Interpret Output**: Agent cites fetched text; if "not in content", myth unproven. Repeat with counter-sources.[^1]


## Example Truth Mission

Target myth from TEXT_ON_WWI.html: "War fought entirely in trenches." 

Chat: "Check if WWI was only trenches: https://en.wikipedia.org/wiki/World_War_I". 

Expected: Agent fetches, responds "No, Eastern Front mobile; Middle East fluid" with quotes.

For full misconceptions (gas deaths, donkeys, Italy Central, instant peace), use systematic questions from paste.txt to expose gaps.

## Setup for Local Runs

Clone repo, run Langflow: `pip install langflow; langflow run`. Import flow JSON from image; set API keys. Customize system prompt for WWI: "Validate TEXT_ON_WWI.html myths using Wikipedia fetches only".[^2][^1]



