---
name: refactor
version: 2.0
applies_to: [refactor]
load_examples: true
load_templates: false
priority: high
max_output_words:
  concise: unlimited
  verbose: unlimited
conflict_resolution: >
  In caso di conflitto con project_rules, project_rules ha precedenza.
  Regola specifica: il vincolo comportamentale di questa skill ha
  precedenza su qualsiasi preferenza stilistica.
description: >
  Regole per il refactoring di codice Python. Include il vincolo
  comportamentale assoluto, protocollo di dichiarazione bug, sette
  anti-pattern prioritari con esempi prima/dopo, tecnica Extract Method,
  e checklist di verifica dell'invariante comportamentale.
---

════════════════════════════════════════════════════════════
REFACTOR — REGOLE OPERATIVE
════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════
SEZIONE 1 — VINCOLO ASSOLUTO: LEGGI PRIMA DI TUTTO
════════════════════════════════════════════════════════════

IL REFACTORING NON CAMBIA IL COMPORTAMENTO OSSERVABILE DEL CODICE.

Questo non è negoziabile e non ha eccezioni.

"Comportamento osservabile" significa:
  - Stesso output per stesso input
  - Stesse eccezioni sugli stessi input errati
  - Stesso ordine di operazioni con side effect
  - Stesso comportamento su edge case (None, lista vuota, zero...)

Prima di modificare qualsiasi funzione:
  1. Descrivi in un commento cosa fa il codice originale
  2. Verifica che il tuo refactoring produca lo stesso comportamento
  3. Se trovi un bug: segnalalo in "## Note" — NON correggerlo

═══ PROTOCOLLO BUG TROVATO ════════════════════════════════

Se durante il refactoring trovi un bug nel codice originale:

  a) NON correggere il bug silenziosamente nel codice refactorizzato
  b) Mantieni il comportamento buggy nel codice refactorizzato
  c) Segnala il bug in "## Note" con questo formato:

     ## Note
     **BUG TROVATO (non corretto nel refactoring):**
     La funzione `process()` riga 23 restituisce None invece di
     lanciare ValueError su input vuoto. Questo è un cambio di
     comportamento rispetto alla firma dichiarata.
     Correzione consigliata: [descrizione]

Perché: il refactoring e la correzione di bug sono operazioni
separate. Mescolarle rende impossibile verificare che il
refactoring non abbia introdotto regressioni.

════════════════════════════════════════════════════════════
SEZIONE 2 — QUANDO INTERVENIRE
════════════════════════════════════════════════════════════

Intervieni se e solo se almeno uno di questi criteri è vero:

  1. LEGGIBILITÀ: difficile da capire senza eseguirlo mentalmente
  2. MANUTENIBILITÀ: aggiungere una feature richiede modifiche
     in più di un punto per una sola responsabilità logica
  3. TESTABILITÀ: dipendenze hardcoded o side effect nascosti
     rendono il test unitario impossibile
  4. DUPLICAZIONE: la stessa logica in più di un posto

Non intervenire per preferenze stilistiche senza impatto tecnico.

════════════════════════════════════════════════════════════
SEZIONE 3 — SETTE ANTI-PATTERN: PRIORITÀ IN ORDINE
════════════════════════════════════════════════════════════

── 1. GOD FUNCTION ──────────────────────────────────────

  PRIMA:
    def handle_request(file_path, output_path, verbose):
        data = open(file_path).read()
        lines = [l for l in data.split("\n") if l.strip()]
        result = []
        for line in lines:
            processed = line.upper().strip()
            if verbose:
                print(f"Processing: {line}")
            result.append(processed)
        with open(output_path, "w") as f:
            f.write("\n".join(result))
        return len(result)

  DOPO:
    def read_lines(file_path: Path) -> list[str]:
        return [
            line
            for line in file_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def process_line(line: str) -> str:
        return line.upper().strip()

    def write_output(lines: list[str], output_path: Path) -> None:
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def handle_request(file_path: Path, output_path: Path) -> int:
        lines = read_lines(file_path)
        processed = [process_line(line) for line in lines]
        write_output(processed, output_path)
        return len(processed)

  Nota: il parametro `verbose` con print() è un side effect
  nascosto. In questo refactoring è stato rimosso (breaking change).
  Se deve essere mantenuto, segnalalo in ## Note e usare logging.

── 2. BOOLEAN TRAP ──────────────────────────────────────

  PRIMA:
    def get_data(source, use_cache):
        if use_cache:
            return _from_cache(source)
        return _from_network(source)

  DOPO:
    def get_data_cached(source: str) -> Data:
        """Recupera dati dalla cache locale."""
        return _from_cache(source)

    def get_data_fresh(source: str) -> Data:
        """Recupera dati freschi dalla rete."""
        return _from_network(source)

── 3. NESTED CONDITIONALS PROFONDI ──────────────────────

  PRIMA:
    def validate(data):
        if data is not None:
            if "name" in data:
                if len(data["name"]) > 0:
                    if data["name"].isalpha():
                        return True
        return False

  DOPO (guard clause):
    def validate(data: dict | None) -> bool:
        if data is None:
            return False
        if "name" not in data:
            return False
        name = data["name"]
        return len(name) > 0 and name.isalpha()

── 4. DUPLICAZIONE CON VARIAZIONE MINIMA ────────────────

  PRIMA:
    def load_generator_skills():
        return Path("skills/python_generation/SKILL.md").read_text()

    def load_review_skills():
        return Path("skills/code_review/SKILL.md").read_text()

  DOPO:
    def load_skill(skill_name: str) -> str:
        path = Path(f"skills/{skill_name}/SKILL.md")
        if not path.exists():
            raise FileNotFoundError(f"Skill non trovata: {skill_name}")
        return path.read_text(encoding="utf-8")

── 5. DIPENDENZA HARDCODED NON INIETTABILE ──────────────

  PRIMA:
    class GeneratorAgent:
        def __init__(self):
            self.client = AnthropicClient(api_key=os.getenv("KEY"))

  DOPO:
    class GeneratorAgent:
        def __init__(self, llm: LLMClient) -> None:
            self.llm = llm

── 6. MAGIC NUMBER E MAGIC STRING ───────────────────────

  PRIMA:
    if quality_score < 0.85:
        retry()
    if len(content) > 4000:
        truncate()

  DOPO:
    QUALITY_THRESHOLD: float = 0.85
    MAX_INPUT_TOKENS: int = 4000

    if quality_score < QUALITY_THRESHOLD:
        retry()
    if len(content) > MAX_INPUT_TOKENS:
        truncate()

── 7. ECCEZIONE TROPPO GENERICA ─────────────────────────

  PRIMA:
    try:
        result = process(data)
    except Exception:
        result = None

  DOPO:
    try:
        result = process(data)
    except ProcessingError as e:
        logger.warning("Processing fallito per input %.50s: %s", data, e)
        result = None

════════════════════════════════════════════════════════════
SEZIONE 4 — TECNICA: EXTRACT METHOD
════════════════════════════════════════════════════════════

Quando una funzione è lunga, identifica blocchi che:
  - Hanno un commento sopra che spiega cosa fanno
  - Potrebbero avere un nome proprio
  - Potrebbero essere utili in isolamento

Estraili come funzioni private con docstring minima.

  PRIMA:
    def run(task):
        # validate input
        if not task.file_path.exists():
            raise FileNotFoundError(...)
        if task.language not in SUPPORTED:
            raise ValueError(...)

        # load skills
        skills = []
        for name in SKILL_MAP[task.command]:
            skills.append(load_skill(name))

        # generate
        prompt = build_prompt(task, skills)
        return llm.complete(prompt)

  DOPO:
    def run(self, task: TaskInput) -> str:
        _validate_task(task)
        skills = _load_skills_for(task.command)
        return _generate(task, skills)

    def _validate_task(task: TaskInput) -> None:
        if not task.file_path.exists():
            raise FileNotFoundError(f"File non trovato: {task.file_path}")
        if task.language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Linguaggio non supportato: {task.language}")

    def _load_skills_for(command: str) -> list[Skill]:
        return [load_skill(name) for name in SKILL_MAP[command]]

    def _generate(task: TaskInput, skills: list[Skill]) -> str:
        return self.llm.complete(build_prompt(task, skills))

════════════════════════════════════════════════════════════
SEZIONE 5 — FORMATO OUTPUT
════════════════════════════════════════════════════════════

## Modifiche apportate
[Lista. Ogni voce: pattern applicato + cosa è cambiato + perché.]

  - Extract Method: separata validazione in _validate_task()
    → la funzione principale ora ha una sola responsabilità
  - Guard clause: rimossi 3 livelli di nesting in validate()
    → leggibile linearmente senza tracciare lo stato dei branch
  - Dependency injection: LLMClient ora iniettato nel costruttore
    → testabile con MockLLMClient senza chiamate reali

## Codice refactorizzato

```python
[codice completo e funzionante]
```

## Note
[Opzionale. Bug trovati, comportamenti ambigui, breaking change
 intenzionali con giustificazione, suggerimenti per test post-refactoring.]

════════════════════════════════════════════════════════════
SEZIONE 6 — CHECKLIST INVARIANTE COMPORTAMENTALE
════════════════════════════════════════════════════════════

Prima di restituire il codice, verifica ogni punto:

  [ ] Il comportamento su input valido è identico all'originale?
  [ ] Il comportamento su input None/vuoto è identico all'originale?
  [ ] Le stesse eccezioni vengono lanciate sui stessi input errati?
  [ ] I side effect (print, log, scrittura file) sono identici?
  [ ] Nessun bug è stato corretto silenziosamente?
       (se sì → segnalato in ## Note)
  [ ] Ogni funzione estratta ha un nome che descrive l'intenzione?
  [ ] Nessun magic number introdotto?
  [ ] Type hints presenti su tutte le funzioni pubbliche e private?
