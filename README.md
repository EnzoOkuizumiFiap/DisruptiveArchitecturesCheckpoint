# 🚀 Disruptive Architectures: IA e IoT — Checkpoint 5

**Assistente Virtual Acadêmico com RAG Híbrido (BM25 + Vetores) & Google Gemini**  
*FIAP — Tecnologia em Desenvolvimento de Sistemas (TDS) 2026*  
**Professor:** Arnaldo Viana  

---

## 👥 Equipe de Desenvolvimento 

| Nome | RM | GitHub | LinkedIn |
| :--- | :---: | :---: | :--- |
| **Enzo Okuizumi** | **561432** | [EnzoOkuizumiFiap](https://github.com/EnzoOkuizumiFiap) | [LinkedIn](https://www.linkedin.com/in/enzo-okuizumi-b60292256/) |
| **Gustavo Okada** | **563428** | [Gdev3356](https://github.com/Gdev3356) | [LinkedIn](https://www.linkedin.com/in/gustavo-okada-53a3b8359/) |
| **Lucas Barros Gouveia** | **566422** | [LuzBGouveia](https://github.com/LuzBGouveia) | [LinkedIn](https://www.linkedin.com/in/lucas-barros-gouveia-09b147355/) |
| **Luna de Carvalho Guimarães** | **562290** | [lunaguima](https://github.com/lunaguima) | [LinkedIn](https://www.linkedin.com/in/luna-guimar%C3%A3es-b0ba82309/) |
| **Milton Marcelino** | **564836** | [MiltonMarcelino](https://github.com/MiltonMarcelino) | [LinkedIn](https://www.linkedin.com/in/milton-marcelino-250298142/) |

---

## 🌐 Links em Produção

| Serviço | URL | Descrição |
| :--- | :--- | :--- |
| 📚 **Materiais de Aula + Chatbot Flutuante** | [GitHub Pages](https://enzookuizumifiap.github.io/DisruptiveArchitecturesCheckpoint/) | Site oficial com apostila completa e assistente integrado `🤖` no canto inferior. |
| 🤖 **Interface Web Dedicada do Chatbot** | [Render Cloud](https://disruptive-architectures-backend.onrender.com/chat) | Interface conversacional estilo ChatGPT com navegação entre históricos de conversas. |
| ⚡ **API Health Check** | [Render Health](https://disruptive-architectures-backend.onrender.com/api/health) | Diagnóstico em tempo real dos motores BM25, Vetorial e Provedor Google GenAI. |
| 📖 **Documentação Swagger (OpenAPI)** | [Swagger UI](https://disruptive-architectures-backend.onrender.com/docs) | Especificação completa de todas as rotas da API RESTful. |

---

## 🏗️ Arquitetura e Engenharia de Software

O projeto foi inteiramente concebido sob rigorosos princípios de **Clean Code**, **SOLID**, **DRY** e **KISS**:

```
DisruptiveArchitecturesCheckpoint/
├── backend/
│   ├── app/
│   │   ├── api/routes.py            # Endpoints RESTful (Chat, Sessões, Health, Busca)
│   │   ├── core/                    # Configurações Pydantic, Logging estruturado e Exceptions
│   │   ├── models/schemas.py        # DTOs e Schemas Pydantic v2
│   │   ├── services/
│   │   │   ├── base.py              # Interfaces abstratas (DIP / ISP)
│   │   │   ├── bm25.py              # Motor Okapi BM25 com Índice Invertido O(postings)
│   │   │   ├── vector_store.py      # Busca Vetorial L2-Normalizada com Cosseno NumPy
│   │   │   ├── rag_engine.py        # Fusão Híbrida via Reciprocal Rank Fusion (RRF)
│   │   │   ├── gemini.py            # Google GenAI 2.x SDK (gemini-3.5-flash-lite) com Cache LRU
│   │   │   └── memory.py            # Sessões multi-turn com gravação atômica em disco
│   │   └── static/
│   │       ├── chat.html            # Interface web moderna com sidebar retrátil
│   │       └── widget.js            # Single Source of Truth do widget flutuante
│   ├── data/
│   │   ├── knowledge_base.json      # 962 chunks com preservação cirúrgica de código
│   │   └── embeddings.npy           # Matriz vetorial pré-calculada (gemini-embedding-2)
│   ├── ingest/
│   │   ├── build_knowledge.py       # Pipeline de extração semântica e chunking
│   │   └── generate_embeddings.py   # Gerador concorrente de embeddings Google GenAI
│   ├── tests/                       # Suíte automatizada de testes de domínio e API
│   ├── Dockerfile                   # Containerização para deploy
│   ├── requirements.txt             # Dependências estritas e atualizadas
│   └── main.py                      # Ponto de entrada FastAPI com lifespan e CORS
├── material/                        # Apostilas, roteiros e laboratórios (IoT + IA)
├── mkdocs.yml                       # Configuração do Material for MkDocs
├── render.yaml                      # Blueprint de Infraestrutura como Código para o Render
└── iniciar.ps1                      # Inicializador automático para ambiente de desenvolvimento local
```

---

## ⚡ Diferenciais do Assistente RAG

1. **Busca Híbrida Real (Léxica + Semântica):**
   * **BM25 Okapi com Índice Invertido:** Encontra com precisão cirúrgica palavras-chave técnicas de hardware (`ESP32`, `MQTT`, `GPIO2`, `Node-RED`).
   * **Google GenAI Embeddings (`gemini-embedding-2`):** Captura o significado semântico conceitual (3072 dimensões).
   * **Reciprocal Rank Fusion (RRF):** Funde os dois rankings com pesos balanceados (`BM25_WEIGHT = 0.5`, `VECTOR_WEIGHT = 0.5`).

2. **Preservação de Código:**
   * Blocos de código em **C++ / Arduino**, **Python** e esquemas de circuitos são mantidos intactos durante o chunking e retornados com formatação rica.

3. **Memória Conversacional Multi-Turn:**
   * O aluno pode tirar dúvidas em sequência (*"Como configuro o Wi-Fi?"* e depois *"E como publico no broker MQTT com ele?"*).
   * Persistência de sessões com escrita atômica anti-corrupção e histórico navegável no chat.

4. **Cache em Memória de Embeddings:**
   * Consultas recorrentes respondem o vetor em **0ms** sem consumir cota de requisições da API.

5. **Guardrails Acadêmicos:**
   * O assistente responde exclusivamente com base nos materiais oficiais da matéria, evitando alucinações e citando as fontes canônicas com links diretos para cada aula.

---

## 💻 Como Rodar Localmente

### Pré-requisitos
* Python 3.11+
* Git

### Opção 1: Inicialização Rápida (PowerShell)
Na raiz do repositório, execute:
```powershell
.\iniciar.ps1
```
> O script inicia o Backend FastAPI (porta `8000`), o MkDocs (porta `8080`) e já abre o navegador na documentação com o widget flutuante ativo!

### Opção 2: Manualmente

**1. Iniciar o Backend (Terminal 1):**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**2. Iniciar o Site de Materiais (Terminal 2):**
```bash
pip install -r requirements.txt
python -m mkdocs serve -a 127.0.0.1:8080
```

---

## 🧪 Execução de Testes Automatizados

O projeto conta com suíte de testes de integração e domínio:

```bash
# Testes do Motor RAG, Tokenização e Memória:
python backend/tests/test_rag.py

# Testes de Integração dos Endpoints da API:
python backend/tests/test_api.py
```