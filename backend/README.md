# Disruptive Architectures — Backend RAG (CP5)

Backend em **FastAPI** com recuperação híbrida (**BM25 + Similaridade Vetorial**) e orquestração do **Google Gemini** para o Checkpoint 5 da disciplina *Disruptive Architectures: IA e IoT* (FIAP).

---

## 🚀 Funcionalidades

- **Busca Híbrida de Alta Precisão (RRF):** Combina pontuação léxica (BM25 Okapi) para termos técnicos de IoT/hardware com busca vetorial semântica de embeddings.
- **Preservação de Código:** Diferencial competitivo em relação ao script de referência — códigos em C++ (Arduino/ESP32) e Python são indexados e retornados com formatação rica.
- **Guardrails Acadêmicos Estritos:** Respostas fundamentadas no material da disciplina, sem alucinação e com links diretos para a documentação MkDocs.
- **Memória Conversacional (Multi-turn):** Suporte a sessões de chat para perguntas de acompanhamento ("E como faço isso no ESP32?").
- **Interface Dual:**
  - Interface Web moderna e responsiva servida em `/chat`.
  - Widget flutuante embutido no site MkDocs com suporte a navegação instantânea SPA.

---

## 🛠️ Como Rodar Localmente

### 1. Criar ambiente virtual e instalar dependências
```bash
cd backend
python -m venv venv
# No Windows:
.\venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configurar a chave de API
Crie um arquivo `.env` na pasta `backend/` baseado no `.env.example`:
```env
GEMINI_API_KEY=sua_chave_do_google_ai_studio
GEMINI_MODEL=gemini-1.5-flash
PORT=8000
```
> *Obtenha sua chave gratuita em: [Google AI Studio](https://aistudio.google.com/)*

### 3. Gerar/Atualizar a Base de Conhecimento
Para reprocessar os arquivos da pasta `material/`:
```bash
python ingest/build_knowledge.py --material-dir ../material --output-json data/knowledge_base.json
```
*(Opcional: use `--with-embeddings` com a `GEMINI_API_KEY` ativa para pré-calcular vetores em `data/embeddings.npy`)*

### 4. Iniciar a API
```bash
uvicorn main:app --reload --port 8000
```

- **Interface Web:** [http://localhost:8000/chat](http://localhost:8000/chat)
- **Documentação Swagger:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Healthcheck:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## ☁️ Como Fazer o Deploy no Render

1. Crie uma conta gratuita em [Render.com](https://render.com/).
2. Clique em **New +** > **Web Service**.
3. Conecte seu repositório GitHub (`DisruptiveArchitecturesCheckpoint`).
4. Configure os parâmetros do Web Service:
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Adicione a variável de ambiente:
   - `GEMINI_API_KEY`: *(Sua chave do Google AI Studio)*
6. Clique em **Create Web Service**.
7. Após o deploy, o Render fornecerá uma URL pública com HTTPS (ex: `https://seu-backend.onrender.com`).
8. Atualize a constante `API_URL` no arquivo `material/js/chat-widget.js` com a sua URL do Render!
