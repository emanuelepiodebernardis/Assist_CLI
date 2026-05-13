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

{{
  "is_valid": true,
  "quality_score": 0.0,
  "clarity_score": 0.0,
  "issues": [
    {{
      "severity": "critical",
      "message": "string",
      "location": "string or null"
    }}
  ],
  "actions": [
    "string"
  ]
}}

Non aggiungere testo fuori dal JSON.
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

{{
  "is_valid": true,
  "quality_score": 0.0,
  "clarity_score": 0.0,
  "issues": [
    {{
      "severity": "critical",
      "message": "string",
      "location": "string or null"
    }}
  ],
  "actions": [
    "string"
  ]
}}

Non aggiungere testo fuori dal JSON.
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

{{
  "is_valid": true,
  "quality_score": 0.0,
  "clarity_score": 0.0,
  "issues": [
    {{
      "severity": "critical",
      "message": "string",
      "location": "string or null"
    }}
  ],
  "actions": [
    "string"
  ]
}}

Non aggiungere testo fuori dal JSON.
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

{{
  "is_valid": true,
  "quality_score": 0.0,
  "clarity_score": 0.0,
  "issues": [
    {{
      "severity": "critical",
      "message": "string",
      "location": "string or null"
    }}
  ],
  "actions": [
    "string"
  ]
}}

Non aggiungere testo fuori dal JSON.
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