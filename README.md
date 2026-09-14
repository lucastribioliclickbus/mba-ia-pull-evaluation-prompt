# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Desafio de Prompt Engineering: puxar um prompt de baixa qualidade do LangSmith Prompt Hub,
refatorá-lo com técnicas avançadas, publicá-lo de volta e provar a melhoria com métricas
automatizadas (Helpfulness, Correctness, F1-Score, Clarity e Precision), todas acima de 0.8.

O prompt converte relatos de bugs em user stories acionáveis, com critérios de aceitação
testáveis.

---

## Técnicas Aplicadas (Fase 2)

O prompt original (`prompts/bug_to_user_story_v1.yml`) tinha quatro defeitos que explicam as
notas baixas:

1. Sem persona — o modelo não sabia de que lugar estava escrevendo.
2. Sem formato de saída — cada resposta saía com uma estrutura diferente.
3. Sem exemplos — nada calibrava o nível de detalhe esperado.
4. `{bug_report}` repetido no system prompt e no user prompt — o relato chegava duas vezes ao
   modelo, competindo com a instrução.

A versão otimizada (`prompts/bug_to_user_story_v2.yml`) aplica quatro técnicas:

### 1. Role Prompting

**Por quê:** a qualidade de uma user story depende de quem a escreve. Sem papel definido, o
modelo alterna entre relatório técnico e resumo de suporte.

**Como apliquei:** o system prompt abre definindo o papel de Product Owner sênior de time ágil,
com base técnica suficiente para preservar detalhe de engenharia, escrevendo para um time que
vai refinar e estimar a story:

```
Você é um Product Owner sênior de um time ágil de produto digital, com dez anos de
experiência escrevendo user stories a partir de relatos de bugs.
```

### 2. Chain of Thought

**Por quê:** converter bug em user story exige inferência — quem é afetado, qual o
comportamento desejado, qual o valor. Pular essa análise produz stories que só reescrevem o
defeito.

**Como apliquei:** sete etapas de raciocínio explícitas antes de escrever (identificar a
persona, descrever o comportamento desejado, determinar o valor, listar as evidências
objetivas, classificar a complexidade, escolher o esqueleto, revisar), com a instrução de
**não exibir o raciocínio na resposta** — o que preserva a métrica de Clarity, que penaliza
informação redundante:

```
Pense passo a passo, internamente, na ordem abaixo. Nunca exiba estas etapas na resposta.
```

### 3. Skeleton of Thought

**Por quê:** o dataset de avaliação tem bugs de três níveis de complexidade, e a referência de
cada nível tem estrutura própria. Um formato único ou perde detalhe nos bugs críticos, ou
infla os simples — e ambos derrubam F1-Score e Precision.

**Como apliquei:** três esqueletos de saída, escolhidos pela classificação feita no passo 5 do
raciocínio:

| Complexidade | Estrutura da resposta |
|---|---|
| Simples | User story + `Critérios de Aceitação:` com 3 a 5 bullets Dado/Quando/Então |
| Médio | User story + critérios + bloco temático adicional + `Contexto Técnico:` |
| Complexo | `=== USER STORY PRINCIPAL ===`, `=== CRITÉRIOS DE ACEITAÇÃO ===` agrupados por tema (A, B, C…), `=== CRITÉRIOS TÉCNICOS ===`, `=== CONTEXTO DO BUG ===`, `=== TASKS TÉCNICAS SUGERIDAS ===` |

### 4. Few-shot Learning (obrigatório)

**Por quê:** descrever o formato não basta — o modelo precisa ver o nível de detalhe, o tom e o
vocabulário esperados.

**Como apliquei:** três pares entrada/saída completos no system prompt, um por nível de
complexidade. Os exemplos são **próprios, não retirados do dataset de avaliação** — usar os 15
casos avaliados como exemplo seria vazar o gabarito e mediria decoreba, não generalização.

### Regras e edge cases

Além das técnicas, o prompt fixa oito regras de comportamento (responder só com a story, não
inventar dado ausente, preservar identificadores e códigos de erro com exatidão, escrever o
comportamento no positivo, critérios verificáveis por teste, sem estimativa de esforço,
português do Brasil com termos técnicos em inglês, profundidade proporcional ao relato) e cinco
edge cases: relato vago, relato com vários problemas, pedido de melhoria em vez de defeito,
relato em outro idioma e relato contendo dado sensível.

---

## Resultados Finais

### Comparativo v1 vs v2

| Aspecto | v1 (original) | v2 (otimizado) |
|---|---|---|
| Persona | ausente | Product Owner sênior de time ágil |
| Formato de saída | não especificado | 3 esqueletos por nível de complexidade |
| Exemplos | nenhum | 3 pares entrada/saída |
| Raciocínio guiado | nenhum | 7 etapas, não exibidas na resposta |
| Regras de comportamento | nenhuma | 8 regras explícitas |
| Edge cases | nenhum | 5 tratados |
| Variável `{bug_report}` | duplicada no system e no user | apenas no user prompt |
| Tamanho do system prompt | 232 caracteres | ~9.200 caracteres |

### Métricas

> A serem preenchidas com a saída de `python src/evaluate.py` após a execução com credenciais
> próprias do LangSmith e do provedor de LLM. Os números abaixo saem do terminal e do dashboard;
> nada aqui é estimado.

| Métrica | v1 | v2 | Mínimo |
|---|---|---|---|
| Helpfulness | — | — | 0.80 |
| Correctness | — | — | 0.80 |
| F1-Score | — | — | 0.80 |
| Clarity | — | — | 0.80 |
| Precision | — | — | 0.80 |

### Evidências no LangSmith

- Dashboard público: _preencher com o link do projeto após a execução_
- Prompt publicado: `{seu_username}/bug_to_user_story_v2` no Prompt Hub
- Screenshots das avaliações: `screenshots/`

---

## Como Executar

### Pré-requisitos

- Python 3.12 ou 3.13
- Conta no [LangSmith](https://smith.langchain.com) com API key
- API key da [OpenAI](https://platform.openai.com/api-keys) **ou** do
  [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Ambiente

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Credenciais

```bash
cp .env.example .env
```

Preencha no `.env`:

| Variável | Descrição |
|---|---|
| `LANGSMITH_API_KEY` | Chave da sua conta LangSmith |
| `LANGSMITH_PROJECT` | Nome do projeto onde as execuções aparecem |
| `USERNAME_LANGSMITH_HUB` | Seu handle no Prompt Hub (visível no ícone de cadeado de qualquer prompt publicado) |
| `LLM_PROVIDER` | `google` ou `openai` |
| `GOOGLE_API_KEY` / `OPENAI_API_KEY` | Chave do provedor escolhido |
| `LLM_MODEL` | Modelo que gera as user stories |
| `EVAL_MODEL` | Modelo que avalia as respostas (pode ser mais capaz que o anterior) |

### 3. Pull do prompt original

```bash
python src/pull_prompts.py
```

Puxa `leonanluppi/bug_to_user_story_v1` do Hub e grava em
`prompts/bug_to_user_story_v1.yml`.

### 4. Push do prompt otimizado

```bash
python src/push_prompts.py
```

Valida `prompts/bug_to_user_story_v2.yml` e publica como
`{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2`, **público**, com descrição, tags e um README
listando as técnicas aplicadas.

A visibilidade só é definida na criação do repositório no Hub: se o prompt já existia como
privado, torne-o público pelo dashboard.

### 5. Avaliação

```bash
python src/evaluate.py
```

Cria o dataset no LangSmith a partir de `datasets/bug_to_user_story.jsonl` (15 bugs), puxa o
prompt publicado, roda os 15 casos e calcula as 5 métricas. O critério de aprovação exige
**todas** acima de 0.8, não só a média.

### 6. Testes de validação

```bash
pytest tests/test_prompts.py -v
```

Dez testes sobre o prompt otimizado, sem rede e sem custo: presença e conteúdo do system
prompt, persona definida, formato de user story com Dado/Quando/Então, exemplos few-shot
pareados, ausência de `[TODO]`, mínimo de duas técnicas declaradas, estrutura validada pelo
`validate_prompt_structure` do projeto, `{bug_report}` só no user prompt, edge cases
documentados e renderização do template com a variável do dataset.

---

## Estrutura do projeto

```
├── prompts/
│   ├── bug_to_user_story_v1.yml   # prompt original, gerado pelo pull
│   └── bug_to_user_story_v2.yml   # prompt otimizado
├── datasets/
│   └── bug_to_user_story.jsonl    # 15 bugs (5 simples, 7 médios, 3 complexos)
├── src/
│   ├── pull_prompts.py            # pull do Hub → YAML local
│   ├── push_prompts.py            # YAML → push público no Hub
│   ├── evaluate.py                # avaliação automática (fornecido)
│   ├── metrics.py                 # as 5 métricas (fornecido)
│   └── utils.py                   # funções auxiliares (fornecido)
└── tests/
    └── test_prompts.py            # validação do prompt otimizado
```
