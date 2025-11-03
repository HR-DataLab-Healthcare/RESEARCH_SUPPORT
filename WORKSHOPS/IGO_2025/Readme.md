# Bouw je eigen Chatbot & Deploy via Hugging Face Spaces    
### Digitale dilemma’s in de klas – Slimme assistent of AI-act valstrik?  
  
In dit project leer je hoe je zelf een **functionele chatbot** kunt bouwen met **Flowise AI** en deze kunt **deployen op Hugging Face Spaces**.    
We combineren **technische implementatie** (met Retrieval Augmented Generation en Azure OpenAI) met **kritische reflectie** op privacy, ethiek en de Europese AI-act.    
  
---  
  
## 🎯 Doel van deze workshop
- Een werkend **chatbot-prototype** maken dat externe bronnen (zoals PDF's) kan gebruiken.  
- Leren hoe je **Flowise AgentFlows** kunt deployen op Hugging Face Spaces.  
- De integratie van **Azure OpenAI** credentials begrijpen.  
- Bewustwording van **digitale dilemma’s** in het onderwijs, inclusief AI-act compliance.  
  
---  
  
## 🛠️ Technologieën  
  
- **Flowise AI** – Open-source low-code platform voor het bouwen van LLM-applicaties.  
- **LangChain** – Framework voor het orkestreren van LLM-componenten en tool-integraties.  
- **Azure OpenAI** – GPT-modellen via Microsoft Azure met enterprise-grade beveiliging.  
- **Node.js** – JavaScript runtime voor server-side uitvoering van Flowise.  
- **Docker** – Containerplatform voor consistente en schaalbare deployments.  
- **Retrieval Augmented Generation (RAG)** – Techniek om actuele en contextuele antwoorden te genereren op basis van externe kennisbronnen.  
  
###  Docker architectuur & inference endpoints  
We hebben een **Docker-gebaseerde architectuur** geïmplementeerd om **veilige, reproduceerbare workflows** mogelijk te maken, zowel **on-premises** als in **publieke cloudomgevingen**.    
Door containerized workflows te deployen via **API key–beveiligde inference endpoints** zorgen we voor:  
  
1. **Schaalbare resource-allocatie** – De benodigde compute-capaciteit kan automatisch worden opgeschaald of afgeschaald op basis van de vraag.  
2. **Consistente prestaties** – Dankzij identieke containeromgevingen wordt het risico op configuratiefouten geminimaliseerd.  
3. **Robuste toegangscontrole** – Alleen geautoriseerde gebruikers met geldige API-sleutels hebben toegang.  
4. **Reproduceerbaarheid** – Dezelfde workflow kan zonder aanpassingen draaien op verschillende infrastructuren.  
  
**Wat zijn inference endpoints?**    
Inference endpoints zijn gebruiksvriendelijke API-koppelingen waarmee gebruikers eenvoudig **inputs** (bijvoorbeeld prompts voor het genereren van synthetische EHR-data) kunnen aanleveren en **outputs** terugkrijgen.    
Dit maakt het mogelijk om **on-demand** gebruik te maken van aangepaste **GA-assisted workflows** zonder dat eindgebruikers worden blootgesteld aan de onderliggende infrastructuur of de complexiteit van de modellen.  
  
💡 **Voordelen in deze context:**  
- Onderwijsinstellingen kunnen AI-workflows veilig delen zonder gevoelige data te exposen.  
- Docenten en studenten kunnen direct experimenteren met AI-functionaliteiten zonder technische installatie.  
- Schaalbaar en geschikt voor zowel kleine pilotprojecten als grootschalige implementaties.  
  
---  
  
## 📦 Stap 1: Flowise AgentFlow deployen op Hugging Face Space  
  
### 1.1 Nieuwe Hugging Face Space aanmaken  
1. Log in op [Hugging Face](https://huggingface.co/).  
2. Klik op **Create new Space** en geef de Space een naam.  
3. Selecteer **Docker** als Space SDK en kies **Blank** als template.  
4. Kies hardware: **CPU basic ∙ 2 vCPU ∙ 16GB ∙ FREE**.  
5. Klik op **Create Space**.  
  
### 1.2 Omgevingsvariabelen instellen  
1. Ga naar **Settings** → **Variables and Secrets**.  
2. Klik op **New variable**:  
   - Name: `PORT`  
   - Value: `7860`  
3. Klik op **Save**.  
4. *(Optioneel)* Voeg extra secrets toe zoals database-credentials, paden, etc. Zie `.env.example` voor geldige velden.  
  
### 1.3 Dockerfile aanmaken  
Maak een nieuw bestand `Dockerfile` in de **Files** tab met onderstaande inhoud:  
  
```dockerfile  
# ====> Node 20 Alpine & Flowise 2.2.5  
FROM node:20-alpine  
USER root  
  
ARG FLOWISE_PATH=/usr/local/lib/node_modules/flowise  
ARG BASE_PATH=/root/.flowise  
ARG DATABASE_PATH=$BASE_PATH  
ARG SECRETKEY_PATH=$BASE_PATH  
ARG LOG_PATH=$BASE_PATH/logs  
ARG BLOB_STORAGE_PATH=$BASE_PATH/storage  
  
RUN apk add --no-cache git python3 py3-pip make g++ build-base cairo-dev pango-dev chromium  
ENV PUPPETEER_SKIP_DOWNLOAD=true  
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser  
  
RUN npm install -g flowise@2.2.5  
RUN mkdir -p $LOG_PATH $FLOWISE_PATH/uploads && chmod -R 777 $LOG_PATH $FLOWISE_PATH  
  
WORKDIR /data  
CMD ["npx", "flowise", "start"]




## 📦 Stap 2: AgentFlow importeren in Flowise  
  
Nadat je **Flowise** draait in **Hugging Face**:  
  
1. **Open** je Flowise Space in de browser.  
2. **Klik** op **Add New** → **Import Chatflow**.  
3. **Upload** het bestand `GA-ASSISTED-SHDG.json` uit dit repository.  
4. **Klik** op **Save Chatflow**.  
5. **Test** je chatbot direct via de ingebouwde chat-interface.  
  
💡 **Tip:**    
Het `GA-ASSISTED-SHDG.json` bestand bevat een vooraf ingestelde **RAG-chatflow** die je kunt aanpassen aan je eigen onderwijscontext.  
  
---
```

  
## 📦 Stap 2: AgentFlow importeren in Flowise  
  
Nadat je **Flowise** draait in **Hugging Face**:  
  
1. **Open** je Flowise Space in de browser.  
2. **Klik** op **Add New** → **Import Chatflow**.  
3. **Upload** het bestand `GA-ASSISTED-SHDG.json` uit dit repository.  
4. **Klik** op **Save Chatflow**.  
5. **Test** je chatbot direct via de ingebouwde chat-interface.  
  
💡 **Tip:**    
Het `GA-ASSISTED-SHDG.json` bestand bevat een vooraf ingestelde **RAG-chatflow** die je kunt aanpassen aan je eigen onderwijscontext.  
  
---  
  
## 📦 Stap 3: Azure OpenAI credentials instellen  
  
Om **Azure OpenAI** modellen (zoals GPT-3.5 of GPT-4) te gebruiken in Flowise:  
  
1. **Maak** een Azure account aan via [Azure Portal](https://portal.azure.com).  
2. **Zoek** naar **Azure OpenAI** in de portal en **maak** een nieuwe resource:  
   - Kies subscription, resource group, regio, naam.  
   - Selecteer een pricing tier.  
3. **Na deployment**:  
   - Ga naar **Keys and Endpoint** en kopieer **API Key** en **Endpoint URL**.  
4. **Model deployen**:  
   - Ga naar **Model deployments** → **Create**.  
   - Kies model (bijv. `gpt-35-turbo`).  
   - Geef een **Deployment Name** op.  
5. **In Flowise**:  
   - Voeg een **Azure OpenAI node** toe in je chatflow.  
   - Vul **API Key**, **Endpoint** en **Deployment Name** in.  
  
💡 **Veiligheidstip:**    
Gebruik **Variables and Secrets** in Hugging Face om je API keys veilig op te slaan.  
  
---  
  
## ⚖️ Digitale dilemma’s & AI-act  
  
In het onderwijs moet je rekening houden met:  
  
- **Privacy & AVG** – Minimaliseer het gebruik van persoonsgegevens.  
- **Transparantie** – Informeer gebruikers dat ze met AI communiceren.  
- **Bias & betrouwbaarheid** – Beoordeel en test je chatbot op vooroordelen en fouten.  
- **AI-act compliance** – Houd rekening met de classificatie van AI-systemen en verplichtingen.  
  
---  
  
## 🚀 Lokale ontwikkeling (optioneel)  
  
Wil je eerst lokaal werken voordat je naar Hugging Face deployt?  
  
```bash  
npm install -g flowise  
npx flowise start  
