# 🤖 Workshop: Bouw je eigen GA-assisted Chatbot met Flowise & Hugging Face Spaces  

<img align="right" width="200" height="200" src="https://avatars.githubusercontent.com/u/115706761?s=400&u=7c6cae892816e172b0b7eef99f2d32adb948c6ad&v=4">
  
## 🎯 Over deze workshop  
In deze hands-on workshop leer je hoe je een **chatbot** bouwt met **Flowise AI** en deze veilig en schaalbaar deployt via **Hugging Face Spaces** en **inference endpoints**.    
We combineren praktische AI-ontwikkeling met inzichten over **Docker-gebaseerde architecturen**, **API-beveiliging** en de **Europese AI-act** in de context van onderwijs en onderzoek.  

---

# Willma / SURF AI-Hub Agent

[![Chat with Willma](https://img.shields.io/badge/Chat_with-Willma-blue?style=for-the-badge&logo=openai)](https://samenaandeslag.cyber-secure-te.src.surf-hosted.nl/playground/162c4cf0-3648-47e2-b83c-d739047e27c2)

Click the badge above to launch the AI Agent playground.
  
---  
  
## 📚 Wat je gaat leren  
- Hoe je een **Flowise AgentFlow** ontwerpt en test.  
- Hoe je je chatbot **containeriseert** en deployt via **Hugging Face Spaces**.  
- Het verschil tussen **Spaces** en **Inference Endpoints**.  
- Hoe je **Azure OpenAI** integreert voor krachtige LLM-functionaliteit.  
- Hoe een **Docker-gebaseerde architectuur** zorgt voor veilige, reproduceerbare AI-workflows.  
- Bewust omgaan met AI in onderwijs, inclusief **privacy, transparantie, bias** en **AI-act compliance**.  
  
---  
  
## 🛠️ Gebruikte technologieën  
  
| Technologie | Beschrijving |  
|-------------|--------------|  
| **Flowise AI** | Open-source low-code platform om LLM-applicaties visueel te bouwen en te testen. |  
| **LangChain** | Framework voor het orkestreren van LLM-componenten en integratie met externe tools. |  
| **Azure OpenAI** | GPT-modellen via Microsoft Azure met enterprise-grade beveiliging en schaalbaarheid. |  
| **Node.js** | JavaScript runtime omgeving waarop Flowise server-side draait. |  
| **Docker** | Containerplatform dat zorgt voor consistente en schaalbare deployments van AI-workflows. |  
| **Retrieval Augmented Generation (RAG)** | Techniek om actuele, contextuele antwoorden te genereren op basis van externe kennisbronnen. |  
| **Hugging Face Spaces** | Platform voor het publiceren van AI-modellen en interactieve applicaties met een gebruiksvriendelijke webinterface (bv. Gradio of Streamlit), ideaal voor demos, onderwijs en experimenten. |  
| **Inference Endpoints** | Beheerde, schaalbare en beveiligde API-koppelingen voor het draaien van AI-modellen in productie via REST API-aanroepen, zonder dat gebruikers zelf infrastructuur hoeven te beheren. |  
  
---  
  
## 🖥️ Inference endpoints & Docker in deze workshop  
  
### Hugging Face Spaces  
**Hugging Face Spaces** is een platform om AI-modellen en interactieve applicaties via een webinterface te publiceren.    
Spaces zijn ideaal voor **demo's** en **experimentele toepassingen** met UI's zoals **Gradio** of **Streamlit**, bijvoorbeeld chatbots of beeldgeneratoren.  


<img align="right" width="200" height="200" src="https://github.com/HR-DataLab-Healthcare/RESEARCH_SUPPORT/blob/main/WORKSHOPS/IGO_2025/INFERENCE_ENDPOINTS.png">

  
### Wat zijn inference endpoints?  
Inference endpoints zijn **beheerde API-koppelingen** waarmee AI-modellen **in productie** draaien.    
Ze bieden:  
- **Schaalbare** en **betrouwbare** toegang tot AI-modellen via REST API.  
- Automatisch schalende infrastructuur in de cloud.  
- Geen noodzaak voor eigen serverbeheer.  
  
### Spaces vs. inference endpoints  
- **Spaces** → Interactieve UI voor demo’s en experimenten.  
- **Inference endpoints** → Geoptimaliseerde API voor productie, zonder UI.  
- **Flowise via Docker** → Kan inference endpoints aanroepen voor modelinference zonder lokaal hosten.  
  
### Waarom Docker?  
Met een **Docker-gebaseerde architectuur** zorgen we voor:  
1. **Schaalbare resource-allocatie**    
2. **Consistente prestaties**    
3. **Robuuste toegangscontrole**    
4. **Reproduceerbaarheid**    
  
Praktisch betekent dit dat deelnemers via eenvoudige API-aanvragen (bv. prompts voor synthetische data) hun chatbot kunnen aansturen **zonder** de complexiteit van infrastructuur te zien.  
  
---  
  
## 📦 Workshop stappenplan  
  
### Stap 1: Flowise AgentFlow deployen op Hugging Face Space  
1. Log in op [Hugging Face](https://huggingface.co/).  
2. Maak een nieuwe **Space** aan (SDK: Docker, template: Blank).  
3. Stel omgevingsvariabelen in, zoals `PORT=7860`.  
4. Voeg een `Dockerfile` toe en commit.  
5. Wacht tot de build klaar is en open je Flowise instance.  
  
### Stap 2: AgentFlow importeren in Flowise  
1. Open je Flowise Space in de browser.  
2. Klik op **Add New → Import Chatflow**.  
3. Upload `GA-ASSISTED-SHDG.json` uit dit repository.  
4. Klik op **Save Chatflow**.  
5. Test je chatbot direct in de Flowise UI.  
  
💡 *Tip:* Dit JSON-bestand bevat een vooraf ingestelde **RAG-chatflow** die je kunt aanpassen.  
  
### Stap 3: Azure OpenAI credentials instellen  
1. Maak een Azure-account aan en activeer **Azure OpenAI**.  
2. Maak een nieuwe resource en kopieer **API Key** en **Endpoint URL**.  
3. Deploy een model (bijv. `gpt-35-turbo`) en noteer de **Deployment Name**.  
4. Voeg in Flowise een **Azure OpenAI node** toe en vul de gegevens in.  
5. Sla je chatflow op en test.  
  
💡 *Veiligheidstip:* Gebruik **Variables and Secrets** in Hugging Face voor API-sleutels.  
  
---  
  
## ⚖️ Digitale dilemma’s & AI-act  
  
In het onderwijs moet je rekening houden met:  
- **Privacy & AVG** – Minimaliseer gebruik van persoonsgegevens.  
- **Transparantie** – Informeer gebruikers dat ze met AI communiceren.  
- **Bias & betrouwbaarheid** – Test je chatbot op vooroordelen.  
- **AI-act compliance** – Houd rekening met classificatie en verplichtingen.  
  
---  
  



