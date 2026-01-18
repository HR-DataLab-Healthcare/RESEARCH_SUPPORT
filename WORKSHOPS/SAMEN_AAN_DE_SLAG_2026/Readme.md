# LLM Truth-Finding Workshop for WWI Text Validation

This workshop guides naive researchers through using a Langflow-based LLM agent playground to perform fact-checking on the WWI text at [TEXT_ON_WWI.html](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/TEXT_ON_WWI.html). The playground, accessible via [SAMEN_AAN_DE_SLAG_2026](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/index.html), employs a retrieval-augmented agent grounded in fetched web content for truthful validation.




<img src="USER_INPUT_FLOW.png" style="height:600px;margin-right:800px"/>


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

---

## Workshop 

### Explain why NO_INPUT  flow cannot answers in response to a provided url <br> whereas the USER_INPUT can?


<img src="NO_INPUT_FLOW.png" style="height:526px;margin-right:200px"/>

### NO INPUT

<img src="USER_INPUT_FLOW.png" style="height:400px;margin-right:200px"/>

### USER INPUT

```python
[https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/TEXT_ON_WWI.html](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/TEXT_ON_WWI.html)
<br> <br> whereras <br>
USER_INPUT flow shown previously can
How can this be tested?

**NO_INPUT flow lacks dynamic URL input, preventing it from fetching and responding to user-provided URLs like TEXT_ON_WWI.html, while USER_INPUT flow supports chat-based URL extraction for grounded responses.**

```




### Key Flow Differences

NO_INPUT flow uses a static URL Loader with fixed URL/text input, connected directly to Agent tools but missing Chat Input routing for new URLs.  

USER_INPUT flow adds Chat Input connected to Agent, enabling the LLM to parse URLs from messages (e.g., "Validate https://...") and trigger the URL tool dynamically.

Both share URL Loader (fetches web content), LLM Agent (tools-enabled reasoning), System Message ("must use URL tool"), and Language Model, but NO_INPUT bypasses user-supplied URLs via direct Epth/Chat Input absence.[^2][^3]
<br><br>
### Why NO_INPUT Fails on Provided URL

Static URL Loader requires pre-pasted URL; no path exists for chat-provided links like TEXT_ON_WWI.html to reach the loader.  Agent sees no mechanism to extract/process dynamic URLs, defaulting to "waiting for input" or ignoring without tool call.  USER_INPUT routes chat (with URL) to Agent input, where system prompt forces "extract link, fetch via URL tool, answer from content."[^3][^1][^2]

## Testing Procedure

- **Deploy Flows**: Run Langflow playgrounds for each (local or hosted).
- **Test NO_INPUT**:

1. Chat: Paste TEXT_ON_WWI.html URL + "Summarize myths."
2. Expected: No fetch/response or generic error; static URL unchanged.
- **Test USER_INPUT**:

1. Same chat input.
2. Expected: Agent extracts URL, fetches HTML (e.g., detects trench/gas myths), responds grounded (e.g., "Per text: trenches everywhere—inaccurate per history").
- **Verify**: Check logs for tool calls; USER_INPUT shows URL fetch, NO_INPUT does not. Repeat with Wikipedia WWI for cross-validation.

| Test Case | NO_INPUT Result | USER_INPUT Result |
| :-- | :-- | :-- |
| "Validate TEXT_ON_WWI.html" | Ignores URL; no fetch | Fetches, lists myths (e.g., Italy Central Powers)  |
| "https://en.wikipedia.org/wiki/World_War_I myths?" | Static fail | Dynamic fetch + debunk  |














- **Access Playground**: Open [index.html](https://hr-datalab-healthcare.github.io/RESEARCH_SUPPORT/WORKSHOPS/SAMEN_AAN_DE_SLAG_2026/index.html); no install needed.
- **Load WWI Text**: Copy TEXT_ON_WWI.html content or URL into chat; note embedded myths (e.g., "trenches everywhere", "Spanish Flu from Spain").
- **Validate Systematically**:
    - Test trench scope: "Did all fronts use trenches only? Fetch https://en.wikipedia.org/wiki/World_War_I".
    - Check flu origin: "Where did Spanish Flu start per page?" Expect correction to Kansas/France.
    - Probe generals: "Did generals avoid front lines?" Agent reveals >200 casualties.
    - Query US role: "Did US instantly win war?" Highlights prior Allied gains.
- **Interpret Output**: Agent cites fetched text; if "not in content", myth unproven. Repeat with counter-sources.


## Example Truth Mission

Target myth from TEXT_ON_WWI.html: "War fought entirely in trenches." 

Chat: "Check if WWI was only trenches: https://en.wikipedia.org/wiki/World_War_I". 

Expected: Agent fetches, responds "No, Eastern Front mobile; Middle East fluid" with quotes.

For full misconceptions (gas deaths, donkeys, Italy Central, instant peace), use systematic questions from paste.txt to expose gaps.




