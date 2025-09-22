# HR Datalab — Intakeproces Data Science Projecten  
  
Dit repository bevat de documentatie en procesbeschrijving voor het **intakeproces van Data Science-projecten** binnen het HR Datalab van de Hogeschool Rotterdam.    
Het proces is ontworpen om **inhoudelijke**, **technische**, **juridische** en **compliance-aspecten** in één gestructureerd traject te behandelen.  
  
---  
  
## 🌐 Overzicht  
  
Het intakeproces start met een **online formulier** dat door de projectaanvrager wordt ingevuld:  
  
🔗 [Intakeformulier (Microsoft Forms)](https://forms.office.com/Pages/DesignPageV2.aspx?subpage=design&FormId=zrpvyrp8U02GgaBihPf_Ro_UBdB0scVKmjPnS1OYmFhUMDc5WTNFOVI3RzU1NDVBWDJRVUhFTVJJTC4u)  
  
Op basis van deze input organiseert HR Datalab een intakegesprek met alle relevante stakeholders, waaronder **IDT**, **RPS**, **CISO**, **Privacy Officer**, **Functionaris Gegevensbescherming (FG)** en indien nodig een **Jurist**.  
  
---  
  
## 🧩 Doelen van het intakeproces  
  
- Vastleggen van de **use-case** en gewenste uitkomst.  
- Beoordelen van **databeschikbaarheid**, **kwaliteit** en **beveiliging**.  
- Toetsen aan **wet- en regelgeving** (AVG, METC, NDA/DTA).  
- Controleren van compliance met **NIS2** en **AI Act**.  
- Vastleggen van technische en organisatorische randvoorwaarden.  
- Opstellen van een **Datamanagementplan (DMP)**.  
- Besluitvorming over start van het project.  
  
---  
  
## 👥 Rollen en verantwoordelijkheden  
  
| Rol | Verantwoordelijkheden |  
| --- | --- |  
| **Projectaanvrager** | Levert inhoudelijke context, doelen en data aan. |  
| **HR Datalab** | Coördineert intake, analyseert use-case, adviseert over data science-methoden. |  
| **IDT** | Adviseert over IT-architectuur, dataopslag, beveiliging en integratie met systemen. |  
| **RPS** | Ondersteunt in onderzoeksbeleid, METC/AVG, subsidie, DMP en AI Act-toetsing. |  
| **Privacy Officer** | Adviseert over AVG, voert privacy-risicobeoordeling uit, stelt DPIA op indien nodig. |  
| **Functionaris Gegevensbescherming (FG)** | Onafhankelijk toezichthouder op AVG-naleving. |  
| **CISO** | Strategisch verantwoordelijk voor informatiebeveiliging, NIS2-compliance, beveiligingsstandaarden. |  
| **Jurist** | Stelt NDA/DTA op en bewaakt juridische contracten. |  
  
---  
  
## 📜 Relevante kaders en standaarden  
  
- **AVG** — Algemene Verordening Gegevensbescherming.  
- **NIS2** — Europese richtlijn voor netwerk- en informatiebeveiliging.  
- **AI Act** — Europese regelgeving voor AI-systemen (risicoclassificatie en compliance).  
- **Privacy-by-Design** & **Security-by-Design** principes.  
- Gebruik van **open standaarden** voor dataformaten (.csv, .json, etc.).  
  
---  
  
## 🔄 Processtappen  
  
1. **Voorbereiding**    
   - Projectaanvrager vult online intakeformulier in.  
   - HR Datalab controleert volledigheid en plant gesprek met relevante experts.  
  
2. **Intakegesprek**    
   - Bespreken van use-case, data, wet- en regelgeving, technische en organisatorische aspecten.  
   - Compliance-checks: AVG/DPIA, NIS2, AI Act.  
  
3. **Acties na intake**    
   - Opstellen intakeverslag met actielijst.  
   - Technische haalbaarheidsanalyse (IDT).  
   - Opstellen/aanpassen DMP (RPS).  
   - Juridische documenten opstellen (Jurist).  
  
4. **Besluitvorming**    
   - Go/No-go beslissing op projectplan.  
   - Eventuele herziening bij afwijzing.  
  
5. **Start project**    
   - Kick-off meeting.  
   - Uitvoering volgens projectplan.  
  
---  
  
## 📊 Flowchart  
  
```mermaid  
flowchart TD  
  
A[Start: Projectaanvrager vult online intakeformulier in] --> B[HR Datalab ontvangt en controleert formulier]  
  
B --> C[Vooroverleg HR Datalab: bepalen benodigde experts]  
C --> D[Uitnodiging intakegesprek: Projectaanvrager, IDT, RPS, CISO, Privacy Officer, FG, Jurist]  
  
D --> E[Intakegesprek]  
E --> E1[Bespreken use-case & doelstellingen]  
E --> E2[Wet- en regelgeving: AVG, METC, NDA/DTA]  
E --> E3[Data beschikbaarheid & beveiliging]  
E --> E4[Dataformaten, DMP, subsidies]  
E --> E5[Data science stack, open data, archivering]  
  
%% Compliance checks  
E2 --> F1{AVG risico?}  
F1 -->|Ja| G1[Privacy Officer/FG: DPIA uitvoeren]  
F1 -->|Nee| H1[Geen DPIA nodig]  
  
E3 --> F2{NIS2 van toepassing?}  
F2 -->|Ja| G2[CISO: beveiligingsmaatregelen en incidentresponsplan]  
F2 -->|Nee| H2[Standaard databeveiliging]  
  
E4 --> F3{AI-component aanwezig?}  
F3 -->|Ja| G3[AI Act risicoanalyse: classificatie en compliance]  
F3 -->|Nee| H3[Geen AI Act vereisten]  
  
%% Na het gesprek  
E5 --> I[HR Datalab stelt intakeverslag op met actielijst]  
I --> J[IDT: technische haalbaarheidsanalyse]  
I --> K[RPS: datamanagementplan en subsidiecheck]  
I --> L[CISO/Privacy Officer/FG: compliance-advies]  
I --> M[Jurist: NDA/DTA opstellen indien nodig]  
  
%% Besluitvorming  
J & K & L & M --> N[Besluitvorming: akkoord op projectplan]  
N -->|Akkoord| O[Kick-off project]  
N -->|Niet akkoord| P[Herziening plan of afwijzing]  
  
O --> Q[Eind: Projectstart en uitvoering]  