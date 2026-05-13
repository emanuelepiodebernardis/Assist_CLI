---
name: documentation
version: 2.0
applies_to: [explain]
load_examples: false
load_templates: false
priority: high
max_output_words:
  concise: 150
  verbose: 500
conflict_resolution: >
  In caso di conflitto con project_rules, project_rules ha precedenza.
description: >
  Regole per la spiegazione e documentazione di codice Python.
  Include criteri di utilità, struttura per livello di complessità,
  standard docstring Google style, esempi di output calibrati,
  e regole anti-ridondanza applicate sistematicamente.
---

════════════════════════════════════════════════════════════
DOCUMENTATION — REGOLE OPERATIVE
════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════
SEZIONE 1 — PRINCIPIO: COSA MERITA UNA SPIEGAZIONE
════════════════════════════════════════════════════════════

Documentazione utile risponde a domande che il codice non
risponde da solo. Documentazione inutile ripete il codice.

UTILE — spiega il perché:
  i = i + 1  # offset: l'API restituisce indici 0-based, noi 1-based

INUTILE — ripete il cosa:
  i = i + 1  # incrementa i

UTILE — spiega un edge case non ovvio:
  # Se skills è vuota, il modello riceve solo project_rules.
  # Questo è intenzionale: project_rules è sempre presente.

INUTILE — spiega comportamento ovvio:
  # Itera sulla lista delle skills
  for skill in skills:

Test: se rimuovi il commento e il codice dice la stessa cosa,
il commento era inutile.

════════════════════════════════════════════════════════════
SEZIONE 2 — STRUTTURA DELLA SPIEGAZIONE (task: explain)
════════════════════════════════════════════════════════════

Segui questo ordine. Ometti le sezioni senza contenuto utile.

  1. COSA FA (obbligatorio, 1-2 frasi)
     Responsabilità principale. Non i dettagli.

  2. COME FUNZIONA (solo se non ovvio)
     Il meccanismo centrale. Non passo per passo se banale.

  3. EDGE CASE E ASSUNZIONI (solo se rilevanti)
     Cosa presuppone. Cosa non gestisce.

  4. DIPENDENZE (solo se non ovvie)
     Cosa deve esistere perché funzioni.

════════════════════════════════════════════════════════════
SEZIONE 3 — LIVELLO DI DETTAGLIO: CALIBRAZIONE
════════════════════════════════════════════════════════════

Modalità CONCISE (default, max 150 parole):
  Copri solo COSA FA e il meccanismo principale se non ovvio.
  Ometti tutto il resto.

  ESEMPIO DI OUTPUT CONCISE CORRETTO:

  ---
  SkillResolver carica i file SKILL.md dal filesystem dato una lista
  di nomi skill. Per ogni nome, legge prima il frontmatter YAML per
  decidere se caricare anche examples/ e templates/, minimizzando il
  contesto portato nel prompt del modello.

  Presuppone che le skill esistano in skills/<nome>/SKILL.md.
  Lancia SkillNotFoundError se una skill richiesta non esiste.
  ---

  Questo esempio ha 54 parole. È il livello giusto.

Modalità VERBOSE (flag --depth full, max 500 parole):
  Copri tutti e 4 i punti della struttura.
  Aggiungi pattern di design usati, alternative considerate,
  esempi d'uso in contesto reale.

  ESEMPIO DI OUTPUT VERBOSE CORRETTO:

  ---
  ### SkillResolver

  **Responsabilità:** carica e restituisce skills dal filesystem,
  ottimizzando il contesto portato al modello LLM.

  **Come funziona:** per ogni nome skill ricevuto, costruisce il path
  `skills/<nome>/SKILL.md`, legge il frontmatter YAML (senza caricare
  il corpo), e decide se aggiungere examples/ e templates/ in base ai
  flag `load_examples` e `load_templates`. Restituisce List[Skill] con
  il contenuto pronto per l'iniezione nel prompt.

  **Pattern usato:** Lazy loading — il corpo della skill viene letto
  solo se necessario. Questo riduce l'uso della context window del
  modello del 40-60% su task semplici che non richiedono esempi.

  **Assunzioni:** le skill esistono nella directory configurata.
  Non gestisce skill remote o compresse.

  **Dipendenze:** PyYAML per il frontmatter, pathlib per i path.
  ---

════════════════════════════════════════════════════════════
SEZIONE 4 — COSA NON SPIEGARE MAI
════════════════════════════════════════════════════════════

NON spiegare la sintassi Python base:
  ✗ "Il for loop itera sulla lista"
  ✗ "L'if controlla la condizione"
  ✗ "Il return restituisce il valore"

NON spiegare comportamento ovvio dalla signature:
  ✗ def add(a: int, b: int) -> int: non ha bisogno di spiegazione
  ✗ def is_empty(lst: list) -> bool: non ha bisogno di spiegazione

NON riformulare commenti esistenti:
  Se il codice ha già `# offset di 1 per l'API`, non scrivere
  "Come si vede dal commento, c'è un offset di 1 per l'API".

NON spiegare cose che il nome descrive già:
  ✗ "MAX_RETRIES è la costante che definisce il numero massimo di retry"

════════════════════════════════════════════════════════════
SEZIONE 5 — DOCSTRING STANDARD (Google style)
════════════════════════════════════════════════════════════

── FUNZIONE SEMPLICE ────────────────────────────────────

  def load_skill(skill_path: Path) -> dict[str, Any]:
      """Carica i metadati di una skill dal filesystem.

      Args:
          skill_path: Percorso al file SKILL.md.

      Returns:
          Dict con frontmatter YAML. Contiene sempre 'name',
          'version', 'applies_to'.

      Raises:
          FileNotFoundError: Se skill_path non esiste.
          ValueError: Se il frontmatter è assente o malformato.
      """

── FUNZIONE CON EXAMPLE ────────────────────────────────

  Aggiungi Example quando la signature non è autoesplicativa
  o quando l'output ha una struttura non ovvia.

  def build_prompt(task: TaskInput, skills: list[Skill]) -> tuple[str, str]:
      """Costruisce system prompt e user prompt per il modello.

      Args:
          task: Input strutturato con comando, file e opzioni.
          skills: Liste di Skill caricate dal SkillResolver.

      Returns:
          Tupla (system_prompt, user_prompt). Il codice sorgente
          è nel user_prompt dentro tag <code>.

      Example:
          >>> task = TaskInput(command="review", file_path=Path("m.py"))
          >>> skills = resolver.load(["project_rules", "code_review"])
          >>> system, user = build_prompt(task, skills)
          >>> "<code>" in user
          True
      """

── CLASSE ────────────────────────────────────────────────

  class SkillResolver:
      """Carica skills dal filesystem su richiesta degli agenti.

      Legge il frontmatter di ogni SKILL.md prima del corpo,
      minimizzando il contesto portato al modello.

      Attributes:
          skills_root: Directory radice delle skills.

      Example:
          >>> resolver = SkillResolver(Path("assist/skills"))
          >>> skills = resolver.load(["project_rules", "code_review"])
          >>> len(skills)
          2
      """

── QUANDO OMETTERE ──────────────────────────────────────

  Ometti (o usa solo una riga) per:
    - Metodi privati (_nome) con logica ovvia
    - Property getter semplici
    - __init__ quando la docstring della classe descrive gli attributi
    - Funzioni di test: il nome è la documentazione

════════════════════════════════════════════════════════════
SEZIONE 6 — COMMENTI INLINE: QUANDO SÌ E QUANDO NO
════════════════════════════════════════════════════════════

SÌ — spiega decisioni non ovvie:
  MAX_RETRIES = 2  # >2 aumenta la latenza senza beneficio misurabile

SÌ — spiega workaround o bug conosciuti:
  result = value + 1  # API usa indici 0-based, noi 1-based

SÌ — spiega regex o espressioni complesse:
  PLACEHOLDER_RE = re.compile(r"<[A-Z_]+>|TODO:|FIXME:")
  # trova placeholder non intenzionali nell'output LLM

SÌ — separa sezioni logiche in funzioni lunghe (accettabile):
  # ── Validazione input ─────────────────────────────────

NO — ripete il codice:
  items = []  # lista vuota

NO — storia del codice (appartiene al commit message):
  # 2024-03-15: modificato per gestire il caso edge

NO — spiega il "cosa" invece del "perché":
  for item in items:   # itera sugli item

════════════════════════════════════════════════════════════
SEZIONE 7 — CHECKLIST SELF-VERIFICA PRIMA DI RESTITUIRE
════════════════════════════════════════════════════════════

  [ ] La spiegazione risponde a domande che il codice non risponde?
  [ ] Nessun commento ripete il codice?
  [ ] Gli Example nei docstring sono eseguibili e corretti?
  [ ] Le eccezioni documentate corrispondono a quelle effettivamente lanciate?
  [ ] I tipi in Args/Returns corrispondono ai type hints nella firma?
  [ ] Il totale di parole è entro il limite della modalità attiva?
       (concise: 150, verbose: 500)
  [ ] Nessuna spiegazione della sintassi Python base?
