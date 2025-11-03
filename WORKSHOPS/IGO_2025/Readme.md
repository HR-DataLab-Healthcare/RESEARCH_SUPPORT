# Bouw je eigen Chatbot: Digitale Dilemma’s in de Klas – Slimme Assistent of AI-act Valstrik?  
  
Dit repository bevat alle materialen, instructies en voorbeeldcode voor de interactieve workshop waarin deelnemers leren hoe ze zelf een functionele chatbot kunnen bouwen, testen en inzetten in een onderwijscontext.    
We combineren technische stappen met kritische reflectie op **privacy**, **ethiek** en de **Europese AI-act**.  
  
---  
  
## 🎯 Doel van de Workshop  
Aan het einde van deze workshop:  
- Heb je een **werkend chatbot-prototype** dat gebruik maakt van **Retrieval Augmented Generation (RAG)**.  
- Begrijp je hoe AI-tools zoals **Flowise AI** en **Large Language Models (LLMs)** technisch werken.  
- Kun je de kansen én risico’s van AI in het onderwijs benoemen.  
- Ben je bekend met relevante wet- en regelgeving (AI-act, AVG).  
  
---  
  
## 🛠️ Gebruikte Technologieën  
- **Flowise AI** – Open-source low-code tool voor het bouwen van LLM-applicaties.  
- **LangChain** – Framework voor LLM-orchestratie.  
- **OpenAI API** – Voor embeddings en chatmodellen (GPT-3.5 of GPT-4).  
- **Node.js** en **pnpm** – Voor installatie en lokaal draaien van Flowise.  
- **RAG** (Retrieval Augmented Generation) – Techniek om externe bronnen (zoals PDF’s) te gebruiken voor accurate antwoorden.  
  
---  
  
## 📚 Inhoud  
1. **Introductie AI in het Onderwijs**  
   - Wat is een chatbot?  
   - Toepassingen in lesvoorbereiding, studentenbegeleiding en administratie.  
   - Privacy en ethiek: wat zegt de AI-act?  
  
2. **Technische Basis**  
   - Installeren van Node.js  
   - Installeren en starten van Flowise AI  
   - Basisprincipes van LLM-orchestratie  
  
3. **Stap-voor-Stap Chatbot Bouwen**  
   - **Document Loader** – PDF als externe databron  
   - **Text Splitter** – Tekst opdelen in betekenisvolle chunks  
   - **Vector Store** – Tekst opslaan als vectors voor semantisch zoeken  
   - **Embeddings** – OpenAI embedding API gebruiken  
   - **Retrieval Chain** – Context behouden bij vervolgvragen  
   - **Chat Model** – GPT-3.5 of GPT-4 integreren  
  
4. **Testen & Uitrollen**  
   - Lokaal testen via `http://localhost:3000`  
   - Koppelen aan een website of LMS  
   - Praktijkcases in de klas  
  
5. **Digitale Dilemma’s**  
   - Data privacy en AVG  
   - Bias en betrouwbaarheid  
   - AI-act compliance checklist  
  
---  
  
## 🚀 Installatie & Starten  
  
### 1. Vereisten  
- Node.js (v18+ aanbevolen)  
- pnpm (package manager)  
- OpenAI API key  
  
### 2. Installatie Flowise AI (snelste manier)  
```bash  
npm install -g flowise  
npx flowise start  
