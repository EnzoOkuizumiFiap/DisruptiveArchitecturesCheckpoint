# RAG e bases de conhecimento

No Lab 3, a NIA aprendeu a solicitar ações da aplicação. Neste laboratório, ela aprenderá a consultar informações externas antes de responder.

Você construirá um mecanismo de **Retrieval-Augmented Generation (RAG)** usando documentos fictícios da TechStore, embeddings e busca por similaridade.

[**Abrir no Google Colab**](https://colab.research.google.com/github/arnaldojr/DisruptiveArchitectures/blob/master/material/aulas/genAI/lab4/lab4_rag_colab.ipynb){ .md-button .md-button--primary }

[Baixar notebook](lab4_rag_colab.ipynb){ .md-button download="lab4_rag_colab.ipynb" }

---

## Objetivos do laboratório

Neste laboratório, você irá:

1. distinguir memória de conversa de base de conhecimento;
2. representar textos usando embeddings;
3. comparar uma pergunta com trechos de documentos;
4. recuperar os trechos semanticamente mais próximos;
5. inserir esses trechos no contexto enviado ao LLM;
6. responder com indicação das fontes utilizadas;
7. reconhecer quando a base não contém a resposta.

---

## Por que o System Prompt não é uma base de conhecimento?

É possível colocar algumas informações no System Prompt, mas essa abordagem não escala bem. Documentos podem ser extensos, mudar com frequência ou conter apenas alguns trechos relevantes para cada pergunta.

Além disso, três conceitos diferentes não devem ser confundidos:

| Conceito | Para que serve |
| --- | --- |
| System Prompt | Define comportamento, regras e estilo |
| Histórico da conversa | Mantém informações das interações anteriores |
| Base de conhecimento | Fornece conteúdo externo que pode ser consultado |

O RAG seleciona informações da base antes de pedir ao modelo que produza a resposta.

---

## Arquitetura do RAG

![alt text](image.png)


Vamos implementar cada etapa diretamente em Python. Em uma aplicação maior, o índice em memória poderia ser substituído por um banco vetorial ou serviço de busca.

---

## Embeddings

Um embedding é uma lista de números que representa características semânticas de um conteúdo. Textos relacionados tendem a ocupar posições próximas nesse espaço vetorial.

Por exemplo, uma busca por:

```text
Até quando posso desistir de uma compra?
```

pode recuperar um trecho que contém:

```text
O cliente pode solicitar devolução em até sete dias corridos.
```

As frases não usam as mesmas palavras, mas possuem significado relacionado. Isso diferencia busca semântica de uma simples procura por palavras exatas.

---

## Trechos e similaridade

Documentos extensos são normalmente divididos em **chunks**. Cada trecho recebe seu próprio embedding e preserva uma referência à fonte original.

No notebook, a similaridade de cosseno será usada para ordenar os trechos:

```text
-1                           0                           1
sentidos opostos      pouca relação        grande proximidade
```

Uma pontuação alta indica proximidade vetorial, não uma garantia de que o trecho responde corretamente à pergunta. A etapa de geração ainda precisa seguir regras claras e os resultados precisam ser avaliados.

---

## Resposta fundamentada

Depois da busca, a aplicação enviará ao modelo somente alguns trechos relevantes e instruções como:

- use apenas o contexto fornecido;
- não complete lacunas com conhecimento próprio;
- informe quando a resposta não estiver nos documentos;
- identifique as fontes utilizadas.

Esse processo reduz respostas sem fundamento, mas não elimina erros. RAG depende da qualidade dos documentos, da divisão em trechos, da recuperação e das instruções de geração.

---

## Escopo didático

Vamos criar uma base de dados fictícia dentro do próprio notebook para que ele funcione sozinho no Colab. Ela contém pequenos trechos fictícios sobre suporte, garantia, devolução, privacidade e produtos.

---

## Recuperação Híbrida: Busca Densa (Vetores) + Busca Esparsa (BM25)

Em aplicações reais de engenharia e IoT (como consulta a datasheets, nomes de pinos do ESP32 como `GPIO2`, `ADC1_CH0`, ou códigos de erro de compilação C++), uma abordagem exclusivamente vetorial (densa) apresenta limitações conhecidas.

### Limitações da Busca Puramente Vetorial:
1. **Termos fora de vocabulário ou alfanuméricos exatos:** Códigos de erro (`fatal error: WiFi.h: No such file or directory`) ou identificadores de registradores e pinos nem sempre possuem proximidade semântica no espaço latente de embeddings.
2. **Perda de precisão léxica:** A busca vetorial aproxima textos por conceito global, o que pode trazer trechos contextualmente próximos, mas sem o termo exato pesquisado.

### Como funciona a Recuperação Híbrida:
A recuperação híbrida combina o melhor de dois mundos no pipeline do Lab 4:
- **Busca Densa (Vetorial via Similaridade de Cosseno):** Mapeia a intenção e o significado semântico conceitual da pergunta do usuário através de embeddings densos.
- **Busca Esparsa (Léxica via BM25 Okapi):** Indexa a frequência de termos e a frequência inversa nos documentos (TF-IDF aprimorado), garantindo correspondência exata para nomes de bibliotecas, pinos e erros de sintaxe.

### Fusão de Rankings: Reciprocal Rank Fusion (RRF)
Como as pontuações do BM25 (valores arbitrários não delimitados $[0, \infty)$) e da similaridade de cosseno (intervalo $[-1, 1]$) possuem naturezas e escalas matemáticas completamente heterogêneas, somá-las ou multiplicá-las diretamente causaria distorções severas.

A solução padrão na indústria é o **Reciprocal Rank Fusion (RRF)**, que normaliza e combina os resultados com base exclusivamente nas suas posições ordinais (ranks) em cada lista:

$$RRF(d) = \sum_{m \in M} \frac{w_m}{k + rank_m(d)}$$

Onde:
- $rank_m(d)$ é a posição (1º, 2º, 3º...) do documento $d$ no motor de busca $m$ (BM25 ou Vetorial);
- $k$ é uma constante de suavização (geralmente $k = 60$) para evitar que o primeiro colocado domine desproporcionalmente o ranking;
- $w_m$ é o peso atribuído a cada motor (ex: $0.5$ para BM25 e $0.5$ para vetorial).

### Vantagens da Abordagem Híbrida com RRF:
1. **Resiliência a Termos Exatos:** Localiza instantaneamente termos técnicos precisos (ex: `GPIO13`, `PubSubClient`, `analogRead`).
2. **Compreensão Semântica Ampla:** Mantém a capacidade de responder dúvidas conceituais formuladas de maneiras diferentes das palavras originais da apostila.
3. **Qualidade Superior de Contexto:** Reduz alucinações entregando ao modelo os chunks de maior relevância tanto léxica quanto semântica.

