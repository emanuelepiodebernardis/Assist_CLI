from assist.schemas.models import (
    Skill,
    TaskInput,
    ValidationReport,
)

from assist.core.prompt_context_builder import (
    PromptContextBuilder,
)


class PromptBuilder:

    @staticmethod
    def _build_skills_block(
        skills: list[Skill],
    ) -> str:

        return "\n\n".join(
            skill.content
            for skill in skills
        )

    @staticmethod
    def _build_context_block(
        task: TaskInput,
    ) -> str:

        context = (
            PromptContextBuilder()
            .aggregate(
                options=task.options,
                target_file=task.file_path,
            )
        )

        return (
            PromptContextBuilder()
            .render(context)
        )

    @staticmethod
    def _build_generation_request(
        task: TaskInput,
    ) -> str:

        candidates = [
            task.raw_input,
            task.options.get("prompt"),
            task.options.get("description"),
            task.options.get("specification"),
            task.options.get("goal"),
        ]

        for candidate in candidates:
            if (
                isinstance(candidate, str)
                and candidate.strip()
            ):
                return candidate.strip()

        target_name = (
            task.file_path
            or "nuovo modulo"
        )

        language = (
            task.language
            or "python"
        )

        return (
            f"Crea {target_name} in {language} seguendo "
            "il contesto strutturale e le skill fornite."
        )

    @staticmethod
    def _build_validation_json_schema() -> str:

        return """
# FORMATO DI OUTPUT

Restituisci SOLO un JSON valido con questa struttura.

VINCOLI OBBLIGATORI:
- "severity" DEVE essere esattamente una di queste 4 stringhe:
  "critical", "high", "medium", "low"
  Non sono ammessi altri valori (no "minor", "info", "warning",
  "trivial", "blocker", ecc.).
- "is_valid" deve essere true o false (boolean, non stringa).
- "quality_score" e "clarity_score" devono essere numeri tra 0.0 e 1.0.
- "location" puo essere null oppure una stringa.

STRUTTURA:

{
  "is_valid": true,
  "quality_score": 0.0,
  "clarity_score": 0.0,
  "issues": [
    {
      "severity": "critical",
      "message": "string",
      "location": "string or null"
    }
  ],
  "actions": [
    "string"
  ]
}

Non aggiungere testo fuori dal JSON.
""".strip()

    @staticmethod
    def build_review_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        if not task.raw_input:
            raise ValueError(
                "TaskInput.raw_input is empty. "
                "File content must be injected "
                "before prompt building."
            )

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica della codebase. Usale per ancorare la review
a fatti rilevati nel progetto, non a impressioni generiche.

{rendered_context}

# CODICE DA ANALIZZARE

```python
{task.raw_input}
```

# ESEGUI ORA LA REVIEW

Applica le regole definite nelle skill sopra.

Produci l'output nel formato esatto richiesto
da code_review e project_rules.

Inizia con "## Sommario".

Non aggiungere prefazioni.
""".strip()

    @staticmethod
    def build_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# REVIEW DA VALIDARE

{draft}

# VALIDAZIONE

Sei il reviewer finale.

Il tuo compito è bloccare il merge se la review
non è sufficientemente rigorosa, concreta o conforme
alle skill.

Valuta:

- correttezza tecnica
- chiarezza
- conformità al formato richiesto
- presenza di fix concreti
- coerenza con il contesto strutturale

{validation_schema}
""".strip()

    @staticmethod
    def build_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# REVIEW DA CORREGGERE

{draft}

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi la review usando il validation report.

Mantieni rigorosamente il formato richiesto
da code_review e project_rules.

La review finale deve:

- iniziare con "## Sommario"
- contenere fix concreti
- essere coerente con il contesto strutturale
- non contenere prefazioni
- non contenere spiegazioni meta

Restituisci SOLO la review finale.
""".strip()

    @staticmethod
    def build_generate_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        generation_request = (
            PromptBuilder
            ._build_generation_request(task)
        )

        language = (
            task.language
            or "python"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica della codebase. Usale per ancorare la generazione
a fatti rilevati nel progetto, non a idee astratte.

{rendered_context}

# SPECIFICA DI GENERAZIONE

{generation_request}

# VINCOLI DI OUTPUT

Genera SOLO codice {language} valido.

REGOLE OBBLIGATORIE:
- non aggiungere spiegazioni
- non usare markdown fences
- non aggiungere prefazioni
- non aggiungere testo fuori dal codice
- il risultato deve essere pronto per essere parsato come codice

Se il task richiede un file o un modulo, restituisci direttamente
il contenuto completo del file.
""".strip()

    @staticmethod
    def build_generate_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        language = (
            task.language
            or "python"
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# CODICE {language.upper()} GENERATO DA VALIDARE

```{language}
{draft}
```

# VALIDAZIONE

Sei il reviewer finale del codice generato.

Valuta il draft rispetto alle skill e al contesto strutturale.

Verifica in particolare:
- sintassi {language} valida
- conformita alle skill (type hints, docstring, naming, lunghezza funzioni)
- assenza di placeholder (TODO, FIXME, pass non intenzionale)
- coerenza con il contesto del progetto

{validation_schema}
""".strip()

    @staticmethod
    def build_generate_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        language = (
            task.language
            or "python"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# CODICE DA CORREGGERE

```{language}
{draft}
```

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi il codice usando il validation report.

REGOLE OBBLIGATORIE:
- restituisci SOLO codice {language} valido
- non aggiungere spiegazioni
- non usare markdown fences nell'output finale
- non aggiungere testo fuori dal codice
- il risultato deve essere sintatticamente valido
- il risultato deve essere coerente con le skill
- mantieni le parti del draft che il report non ha segnalato
""".strip()

    @staticmethod
    def build_refactor_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        if not task.raw_input:
            raise ValueError(
                "TaskInput.raw_input is empty. "
                "File content must be injected "
                "before prompt building."
            )

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        language = (
            task.language
            or "python"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica della codebase. Usale per identificare quali
anti-pattern reali sono presenti, non per inventare problemi.

{rendered_context}

# CODICE DA REFACTORIZZARE

```{language}
{task.raw_input}
```

# ESEGUI ORA IL REFACTORING

Applica le regole definite nelle skill sopra.

VINCOLO ASSOLUTO:
Il refactoring NON cambia il comportamento osservabile del codice.
Stesso output per stesso input. Stesse eccezioni sugli stessi
input errati. Stessi side effect nello stesso ordine.

PROTOCOLLO BUG:
Se trovi un bug nel codice originale, NON correggerlo.
Mantieni il comportamento buggy nel refactoring.
Segnala il bug nella sezione "## Note" del formato output.

Produci l'output nel formato esatto definito dalla skill refactor:
- "## Modifiche apportate" con elenco dei pattern applicati
- "## Codice refactorizzato" con il codice completo in un blocco ```{language}
- "## Note" (opzionale) per bug trovati o breaking change consapevoli

Non aggiungere prefazioni.
""".strip()

    @staticmethod
    def build_refactor_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        language = (
            task.language
            or "python"
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# CODICE ORIGINALE

```{language}
{task.raw_input}
```

# REFACTORING PROPOSTO DA VALIDARE

{draft}

# VALIDAZIONE

Sei il reviewer finale del refactoring.

Il tuo default è BLOCCARE. Cerca attivamente motivi per non approvare.

Verifica in particolare:
- INVARIANTE COMPORTAMENTALE: il codice refactorizzato produce lo
  stesso output dell'originale sugli stessi input? Stesse eccezioni?
  Stessi side effect?
- BUG SILENZIATI: il refactoring ha corretto silenziosamente un bug
  dell'originale senza segnalarlo in "## Note"? Se sì, severity high.
- CONFORMITA SKILL: il refactoring segue i pattern definiti nella
  skill refactor (Extract Method, guard clause, dependency injection,
  no magic number)?
- FORMATO: l'output contiene "## Modifiche apportate" e
  "## Codice refactorizzato"? Le note ci sono se ci sono bug?
- SINTASSI: il codice nel blocco "## Codice refactorizzato" e' {language}
  sintatticamente valido?

{validation_schema}
""".strip()

    @staticmethod
    def build_refactor_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        language = (
            task.language
            or "python"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# CODICE ORIGINALE

```{language}
{task.raw_input}
```

# REFACTORING DA CORREGGERE

{draft}

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi il refactoring usando il validation report.

REGOLE OBBLIGATORIE:
- mantieni l'INVARIANTE COMPORTAMENTALE rispetto al codice originale
- se il report segnala un bug silenziato, ripristina il comportamento
  originale e sposta la segnalazione in "## Note"
- mantieni il formato richiesto dalla skill refactor:
  "## Modifiche apportate" + "## Codice refactorizzato" + "## Note" (opzionale)
- il blocco "## Codice refactorizzato" deve contenere {language} valido
- mantieni le parti del draft che il report non ha segnalato
- non aggiungere prefazioni
- non aggiungere spiegazioni meta

Restituisci SOLO l'output corretto nel formato definito.
""".strip()

    @staticmethod
    def build_explain_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        if not task.raw_input:
            raise ValueError(
                "TaskInput.raw_input is empty. "
                "File content must be injected "
                "before prompt building."
            )

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        language = (
            task.language
            or "python"
        )

        depth = (
            task.options.get("depth")
            or "brief"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica della codebase. Usale per spiegare il codice
in modo concreto, ancorato a fatti rilevati nel progetto,
non a impressioni generiche.

{rendered_context}

# CODICE DA SPIEGARE

```{language}
{task.raw_input}
```

# ESEGUI ORA LA SPIEGAZIONE

Applica le regole definite nelle skill sopra.

Profondita richiesta: {depth}

La spiegazione deve coprire:
- scopo del file
- struttura generale
- funzioni e responsabilita principali
- dipendenze rilevanti
- eventuali criticita o pattern degni di nota
- relazione con il contesto strutturale del progetto

Produci l'output nel formato esatto richiesto dalla skill
documentation. Inizia con "## Sommario".

Non aggiungere prefazioni.
""".strip()

    @staticmethod
    def build_explain_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# SPIEGAZIONE DA VALIDARE

{draft}

# VALIDAZIONE

Sei il reviewer finale della spiegazione.

Il tuo compito e' bloccare la pubblicazione se la spiegazione
non e' sufficientemente accurata, chiara o conforme alle skill.

Valuta in particolare:
- accuratezza tecnica rispetto al codice originale
- chiarezza didattica e progressione logica
- completezza (scopo, struttura, dipendenze, criticita)
- coerenza con il contesto strutturale del progetto
- conformita al formato richiesto dalla skill documentation
- assenza di prefazioni o postfazioni
- assenza di ripetizione del codice senza valore aggiunto

{validation_schema}
""".strip()

    @staticmethod
    def build_explain_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# SPIEGAZIONE DA CORREGGERE

{draft}

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi la spiegazione usando il validation report.

Mantieni rigorosamente il formato richiesto dalla skill
documentation e da project_rules.

La spiegazione finale deve:

- iniziare con "## Sommario"
- essere accurata rispetto al codice originale
- essere coerente con il contesto strutturale
- non contenere prefazioni o postfazioni
- non contenere spiegazioni meta su cosa hai corretto
- mantenere le parti del draft che il report non ha segnalato

Restituisci SOLO la spiegazione finale corretta.
""".strip()

    @staticmethod
    def build_test_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        if not task.raw_input:
            raise ValueError(
                "TaskInput.raw_input is empty. "
                "File content must be injected "
                "before prompt building."
            )

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        language = (
            task.language
            or "python"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica della codebase. Usale per ancorare la generazione
dei test a fatti reali rilevati nel progetto.

Le funzioni e classi rilevate nel semantic_context
rappresentano il comportamento osservabile del file.

Usale per determinare:
- cosa testare
- quali edge case sono rilevanti
- quali funzioni sono pubbliche o critiche
- quali branch logici richiedono copertura dedicata

{rendered_context}

# CODICE DA TESTARE

```{language}
{task.raw_input}
```

# GENERA ORA I TEST PYTEST

Applica rigorosamente le regole definite nelle skill sopra.

VINCOLI ASSOLUTI:
- NON inventare comportamento non presente nel codice
- NON correggere bug del codice originale
- se trovi un bug, preserva il comportamento osservato
  e documentalo con commento "# BUG:"
- genera test ancorati al comportamento osservabile
- privilegia test significativi rispetto a test ridondanti

# VINCOLI DI OUTPUT

REGOLE OBBLIGATORIE:
- restituisci SOLO codice pytest valido
- non usare markdown fences
- non aggiungere spiegazioni
- non aggiungere prefazioni
- non aggiungere testo fuori dal codice
- il risultato deve essere pronto per essere salvato
  come file test_<module>.py ed eseguito direttamente

Il file finale deve contenere:
- import validi
- fixture necessarie
- test pytest validi
- struttura Arrange-Act-Assert
- naming descrittivo dei test
""".strip()

    @staticmethod
    def build_test_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        language = (
            task.language
            or "python"
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# CODICE ORIGINALE

```{language}
{task.raw_input}
```

# TEST PYTEST DA VALIDARE

```{language}
{draft}
```

# VALIDAZIONE

Sei il reviewer finale della test suite.

Il tuo default e' BLOCCARE.

Cerca attivamente:
- test non deterministici
- copertura insufficiente
- edge case mancanti
- assert deboli o banali
- dipendenze tra test
- uso scorretto di fixture
- mocking inutile
- violazioni delle skill
- dettagli implementativi testati al posto
  del comportamento osservabile

Verifica in particolare:
- sintassi pytest valida
- pytest --collect-only passerebbe?
- ogni funzione pubblica ha almeno un happy path?
- gli edge case richiesti sono presenti?
- i test sono indipendenti?
- il protocollo BUG e' rispettato?
- naming e struttura AAA sono corretti?
- i test riflettono il comportamento reale del codice?

{validation_schema}
""".strip()

    @staticmethod
    def build_test_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        language = (
            task.language
            or "python"
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# CODICE ORIGINALE

```{language}
{task.raw_input}
```

# TEST DA CORREGGERE

```{language}
{draft}
```

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi la test suite usando il validation report.

REGOLE OBBLIGATORIE:
- mantieni i test validi gia presenti
- correggi SOLO i problemi segnalati
- preserva il comportamento osservabile del codice originale
- NON correggere silenziosamente bug del codice originale
- se esiste un bug, documentalo con commento "# BUG:"
- mantieni naming descrittivo e struttura AAA
- restituisci SOLO codice pytest valido
- non usare markdown fences nell'output finale
- non aggiungere spiegazioni
- non aggiungere testo fuori dal codice
- il risultato deve essere sintatticamente valido
- mantieni le parti del draft che il report non ha segnalato
""".strip()

    @staticmethod
    def _build_impacted_files_block(
        task: TaskInput,
    ) -> str:
        """Costruisce la sezione FILE IMPATTATI con il contenuto
        di ogni file toccato dal diff.

        task.options["impacted_files_content"] e' un dict {path: content}
        popolato dall'orchestrator usando GitDiffExtractor + ProjectGraph.
        """

        impacted_files = (
            task.options.get(
                "impacted_files_content",
                {},
            )
        )

        if not impacted_files:
            return "(nessun file impattato disponibile)"

        sections = []

        for path, content in impacted_files.items():

            sections.append(
                f"## File: {path}\n\n"
                f"```python\n"
                f"{content}\n"
                f"```"
            )

        return "\n\n".join(sections)

    @staticmethod
    def build_diff_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        if not task.raw_input:
            raise ValueError(
                "TaskInput.raw_input is empty. "
                "Git diff content must be injected "
                "before prompt building."
            )

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        impacted_files_block = (
            PromptBuilder
            ._build_impacted_files_block(task)
        )

        range_spec = (
            task.options.get(
                "range_spec",
                "HEAD",
            )
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica della codebase. Usale per inquadrare il diff
nel contesto reale del progetto.

{rendered_context}

# FILE IMPATTATI

I file seguenti sono quelli toccati dal diff o che dipendono
da simboli modificati. Il contenuto e' la versione CORRENTE
del file (post-modifica), non quella precedente.

{impacted_files_block}

# DIFF DA ANALIZZARE

Range git: {range_spec}

```diff
{task.raw_input}
```

# ESEGUI ORA LA REVIEW DEL DIFF

Applica rigorosamente le regole definite nella skill diff_review.

VINCOLI ASSOLUTI:
- Focus sui CAMBIAMENTI, non sui file completi
- Non commentare codice non modificato dal diff
- Non commentare codice cancellato come fosse problematico
  (la cancellazione e' una scelta intenzionale del committente)
- Identifica breaking change solo su simboli che hai motivo
  di considerare pubblici (vedi sezione 3 della skill)
- Severity calibrata: usa critical solo per impatto immediato
- Sezioni "## Rischi" e "## Suggerimenti" SOLO se hanno
  contenuto reale (non sezioni vuote con "Nessun problema rilevato")

Produci l'output nel formato esatto definito dalla skill diff_review:
- "## Sommario" sempre
- "## Modifiche rilevanti" sempre
- "## Rischi" se ci sono rischi
- "## Suggerimenti" se ci sono suggerimenti

Non aggiungere prefazioni.
""".strip()

    @staticmethod
    def build_diff_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# DIFF ORIGINALE

```diff
{task.raw_input}
```

# REVIEW DEL DIFF DA VALIDARE

{draft}

# VALIDAZIONE

Sei il reviewer finale della review del diff.

Il tuo default e' BLOCCARE. Cerca attivamente motivi
per non approvare.

Verifica in particolare:
- FOCUS SUL DIFF: la review parla dei cambiamenti del diff,
  non del codice non modificato?
- CONCRETEZZA: ogni rischio cita file e righe specifiche?
  Ogni suggerimento e' applicabile al diff stesso?
- CALIBRAZIONE SEVERITY: i severity sono giustificati dall'impatto
  reale, non gonfiati? Non c'e' un critical per un piccolo refactor?
- ANCORAGGIO "PUBBLICO": i breaking change citano il dato del
  context che giustifica la qualifica di "pubblico"?
- SEZIONI CONDIZIONALI: "## Rischi" e "## Suggerimenti" sono
  presenti SOLO se hanno contenuto reale? Non vuote con disclaimer?
- ASSENZA DI FILLER: niente "Nessun rischio rilevato",
  "Codice ben scritto", "Continuate cosi'"?
- TRATTAMENTO DEL CODICE CANCELLATO: non e' stato commentato
  come problematico, eccetto per breaking change documentati?

{validation_schema}
""".strip()

    @staticmethod
    def build_diff_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# DIFF ORIGINALE

```diff
{task.raw_input}
```

# REVIEW DA CORREGGERE

{draft}

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi la review del diff usando il validation report.

REGOLE OBBLIGATORIE:
- mantieni il FOCUS SUL DIFF: niente commenti sul codice non modificato
- correggi SOLO i problemi segnalati dal validation report
- mantieni il formato richiesto dalla skill diff_review:
  - "## Sommario" sempre
  - "## Modifiche rilevanti" sempre
  - "## Rischi" se ci sono rischi reali
  - "## Suggerimenti" se ci sono suggerimenti azionabili
- calibra correttamente le severity (no inflation)
- mantieni le parti del draft che il report non ha segnalato
- non aggiungere prefazioni
- non aggiungere spiegazioni meta su cosa hai corretto

Restituisci SOLO la review finale corretta.
""".strip()

    @staticmethod
    def build_repo_prompt(
        task: TaskInput,
        skills: list[Skill],
    ) -> str:
        """Costruisce il prompt per il task `repo`.

        Diversamente dagli altri task, repo non ha task.raw_input
        (non c'e' un singolo file da analizzare). Tutto il segnale
        per l'overview deriva dal context strutturale aggregato a
        livello di repository, popolato dall'orchestrator.

        L'agente legge:
        - task.repo_path: identifica il repository analizzato
        - context aggregato: project_size, health_score, god_classes,
          long_methods, complexity_warnings, risks, ecc.
        """

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        repo_path = (
            task.repo_path
            or "."
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

Le seguenti informazioni provengono da un'analisi statica
deterministica dell'intero repository. Sono i dati aggregati
a livello di progetto: dimensione, salute architetturale,
rischi, hotspot di complessita.

Ogni affermazione del tuo overview deve essere riconducibile
a uno di questi dati. Non inventare pattern architetturali,
non aggiungere giudizi morali sul codice, non riassumere file
singoli.

{rendered_context}

# REPOSITORY ANALIZZATO

Path: {repo_path}

# ESEGUI ORA L'OVERVIEW

Applica rigorosamente le regole definite nella skill repository_overview.

VINCOLI ASSOLUTI:
- ANCORAGGIO AI DATI: ogni affermazione di fatto deve poter essere
  ricondotta a un campo specifico del context aggregato sopra
- NO INVENZIONE DI PATTERN: non affermare che il progetto usa MVC,
  Clean Architecture, microservizi o altri pattern architetturali
  se non sono dimostrabili dai nomi delle directory o dai dati
- NO GIUDIZI MORALI: niente "ben scritto", "scarsa qualita",
  "scelta discutibile"
- NO FILLER: niente "Continuate il buon lavoro", "Codice promettente"
- NO RIASSUNTO DEL CODICE: l'overview e' sopra il codice, non
  descrive cosa fanno classi o funzioni singole

Produci l'output nel formato esatto definito dalla skill
repository_overview:
- "## Panoramica" sempre (max 200 parole)
- "## Architettura" sempre (max 250 parole)
- "## Salute del codice" sempre (max 350 parole)
- "## Rischi architetturali" SOLO se ci sono rischi (max 300 parole)
- "## Raccomandazioni" SOLO se ci sono raccomandazioni concrete
  (max 250 parole, massimo 5 raccomandazioni)

Non aggiungere prefazioni.
""".strip()

    @staticmethod
    def build_repo_self_check_prompt(
        draft: str,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        repo_path = (
            task.repo_path
            or "."
        )

        validation_schema = (
            PromptBuilder
            ._build_validation_json_schema()
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# REPOSITORY ANALIZZATO

Path: {repo_path}

# OVERVIEW DA VALIDARE

{draft}

# VALIDAZIONE

Sei il reviewer finale dell'overview del repository.

Il tuo default e' BLOCCARE. Cerca attivamente motivi
per non approvare.

Verifica in particolare:
- ANCORAGGIO AI DATI: ogni affermazione di fatto e' riconducibile
  a un campo del context aggregato? Affermazioni come "il progetto
  e' ben strutturato" senza supporto da dati specifici sono violazioni
- INVENZIONE DI PATTERN: l'overview afferma pattern architetturali
  (MVC, Clean Architecture, microservizi, CQRS, hexagonal) senza
  prova esplicita nei dati o nei nomi delle directory? Se si',
  severity critical.
- GIUDIZI MORALI: ci sono frasi tipo "ben scritto", "scarsa qualita",
  "scelta discutibile"? Se si', severity high.
- SEZIONI CONDIZIONALI: "## Rischi architetturali" e
  "## Raccomandazioni" sono presenti SOLO se hanno contenuto reale?
  Non vuote con disclaimer?
- DENSITA: l'overview e' almeno 400 parole? Non c'e' filler?
- CONCRETEZZA: le raccomandazioni sono azionabili? Citano i dati
  che le motivano?
- TONO: e' tecnico ma accessibile? I termini tecnici introdotti
  sono spiegati la prima volta?
- RIASSUNTO DEL CODICE: l'overview descrive cosa fanno classi o
  funzioni singole invece di restare a livello di progetto?

{validation_schema}
""".strip()

    @staticmethod
    def build_repo_correction_prompt(
        draft: str,
        report: ValidationReport,
        task: TaskInput,
        skills: list[Skill],
    ) -> str:

        skills_block = (
            PromptBuilder
            ._build_skills_block(skills)
        )

        rendered_context = (
            PromptBuilder
            ._build_context_block(task)
        )

        report_json = (
            report.model_dump_json(indent=2)
        )

        repo_path = (
            task.repo_path
            or "."
        )

        return f"""{skills_block}

# CONTESTO STRUTTURALE DEL PROGETTO

{rendered_context}

# REPOSITORY ANALIZZATO

Path: {repo_path}

# OVERVIEW DA CORREGGERE

{draft}

# VALIDATION REPORT

{report_json}

# CORREZIONE

Correggi l'overview usando il validation report.

REGOLE OBBLIGATORIE:
- mantieni l'ANCORAGGIO AI DATI: ogni affermazione deve essere
  riconducibile al context
- rimuovi pattern architetturali inventati non supportati dai dati
- rimuovi giudizi morali e filler
- mantieni il formato richiesto dalla skill repository_overview:
  - "## Panoramica" sempre
  - "## Architettura" sempre
  - "## Salute del codice" sempre
  - "## Rischi architetturali" SOLO se ci sono rischi reali
  - "## Raccomandazioni" SOLO se ci sono raccomandazioni concrete
- mantieni le parti del draft che il report non ha segnalato
- non aggiungere prefazioni
- non aggiungere spiegazioni meta su cosa hai corretto

Restituisci SOLO l'overview finale corretto.
""".strip()