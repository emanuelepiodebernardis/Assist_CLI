---
name: diff_review
version: 2.0
applies_to: [diff]
priority: 80
max_output_words: 1500
conflict_resolution: project_rules_wins
inject_position: middle
self_check_persona: adversarial
---

# diff_review v2.0

## 1. Scopo della skill

Eseguire la review tecnica di un diff git (commit singolo, range di commit, o working directory). L'output si concentra sui CAMBIAMENTI introdotti, non sui file completi. Identifica regressioni potenziali, breaking change su interfacce pubbliche, side effect non documentati, e produce suggerimenti azionabili.

L'output NON è una review del file. È una review specifica del diff.

## 2. Dati del context utilizzati

Questa skill legge i seguenti campi dal context strutturale. I campi marcati come **opzionali** non sono prodotti dal sistema corrente: se assenti, applica le regole degradate descritte nella sezione corrispondente.

**Sempre disponibili:**

- `diff_context.files` — lista dei file modificati con i loro hunk
- `diff_context.summary` — aggregati totali (additions, deletions, files_changed)
- `diff_context.raw_diff` — output testuale completo di `git diff`
- `repository_context.related_files` — file impattati direttamente
- `semantic_context` — funzioni e classi dei file modificati
- `cross_file_context.imports` — chi importa cosa nel progetto
- `cross_file_context.function_calls` — chi chiama cosa nel progetto
- `code_quality_context` — warning sui file modificati

**Opzionali (versioni future):**

- `diff_context.exports_modified` — lista dei simboli toccati dal diff che sono esportati pubblicamente (presenti in `__all__` o importati da almeno un altro modulo del progetto). Quando disponibile, è il criterio principale per identificare breaking change.

## 3. Identificazione delle modifiche pubbliche

Una modifica si considera "su simbolo pubblico" se soddisfa una di queste condizioni, in ordine di affidabilità:

1. **Caso ideale** (con `exports_modified` disponibile): il simbolo è in `diff_context.exports_modified`.
2. **Caso degradato** (senza `exports_modified`): il simbolo soddisfa una di queste condizioni euristiche:
   - Il nome non inizia con underscore
   - Il simbolo compare in `cross_file_context.function_calls` come target da altri file
   - Il simbolo è esportato in un `__init__.py` (presente in `cross_file_context.imports`)

Quando lavori in caso degradato, segnala esplicitamente nelle note che la valutazione di "pubblico" è euristica e potrebbe avere falsi positivi/negativi.

## 4. Formato dell'output

L'output è un documento markdown strutturato in quattro sezioni nominate. Due sono sempre presenti, due sono condizionali. È esplicitamente vietato includere sezioni vuote con frasi tipo "Nessun rischio rilevato".

### 4.1 Sezione `## Sommario` (sempre, max 150 parole)

Inquadra il diff in 2-4 frasi:
- Cosa cambia (in sintesi: nuova feature, bug fix, refactoring, modifica di interfaccia)
- Quanti file impattati, ordine di grandezza delle modifiche
- Una eventuale annotazione di alto livello (es. "il diff modifica un'interfaccia esportata in 3 punti")

NON descrivere il diff riga per riga. Il Sommario è la sintesi orientata al lettore.

### 4.2 Sezione `## Modifiche rilevanti` (sempre, max 600 parole)

Elenca i cambiamenti significativi del diff. Per ogni cambiamento:
- File coinvolto
- Tipo di modifica (nuova funzione, signature modificata, logica modificata, import aggiunto/rimosso)
- Effetto osservabile (cosa cambia nel comportamento o nell'interfaccia)

Criteri di inclusione:
- Include cambiamenti che alterano il comportamento osservabile
- Include modifiche di signature, naming, return type
- Include aggiunte/rimozioni di funzioni/classi pubbliche
- Include modifiche a logica condizionale (if/else, switch, error handling)
- Escludi cambiamenti puramente cosmetici (riordino import senza side effect, riformattazione, rinomina locale di variabili)

NON commentare codice cancellato come se fosse problematico. Il codice cancellato è una scelta intenzionale del committente, non un bug. Eccezione: se la cancellazione rimuove un comportamento documentato o usato altrove, segnalalo come breaking change.

### 4.3 Sezione `## Rischi` (condizionale, max 400 parole)

Includi questa sezione SOLO se ci sono rischi concreti da elencare. Se non ci sono rischi, ometti completamente la sezione.

Per ogni rischio:
- Tipo: categorizza in una delle quattro categorie sotto
- Severity: `critical` | `high` | `medium` | `low` (coerente con la scala usata da altri agenti del sistema)
- File e righe coinvolte
- Descrizione concisa (max 30 parole)
- Mitigazione suggerita se ovvia (opzionale)

Categorie di rischio:

- **Regressione potenziale**: cambiamento che potrebbe introdurre bug in funzionalità esistenti (esempio: modifica del valore di ritorno di una funzione utilizzata altrove)
- **Breaking change**: modifica del contratto pubblico (signature, exception sollevate, formato output) di un simbolo pubblico (vedi sezione 3)
- **Side effect non documentato**: il diff introduce side effect (mutazione, I/O, mutazione di stato globale) non evidenti dalla signature
- **Inconsistenza con il progetto**: il cambiamento viola una convenzione o uno standard del progetto (verificabile dal `code_quality_context` o dalle skill applicabili)

Raggruppa per severity in ordine decrescente: `critical` prima, `low` per ultimo.

### 4.4 Sezione `## Suggerimenti` (condizionale, max 250 parole)

Includi questa sezione SOLO se hai suggerimenti concreti e azionabili. Se non ne hai, ometti completamente la sezione.

Massimo cinque suggerimenti, prioritizzati. Per ogni suggerimento:
- Frase azionabile (max 20 parole)
- Motivazione concisa (max 30 parole)
- Riferimento al cambiamento specifico nel diff

Vietato:
- Suggerimenti generici ("aggiungere test", "migliorare i nomi") senza specificare dove e come
- Suggerimenti che richiedono lavoro fuori dallo scope del diff (es. "rifare il modulo X"): il suggerimento deve essere applicabile al diff stesso
- Più di 5 suggerimenti

## 5. Vincoli operativi assoluti

- **Focus sul diff**: non revieware codice non modificato dal diff. Eccezione: se per capire l'impatto di una modifica è necessario riferirsi a codice esistente, fallo brevemente e cita il file/funzione di riferimento.
- **No estetica sul non-modificato**: niente commenti tipo "anche questa funzione qui sopra dovrebbe avere docstring"
- **No review estetica del codice cancellato**: il codice cancellato è scelta intenzionale, non commentarlo se non per breaking change documentato
- **Severity calibrata**: usa `critical` solo per rischi con impatto immediato (es. rimozione di funzione esportata usata da altri moduli). Non gonfiare i severity.
- **Identificazione "pubblico" tracciabile**: ogni volta che identifichi un breaking change, cita il dato del context che giustifica la qualifica di "pubblico" (`exports_modified` se disponibile, altrimenti l'euristica usata)

## 6. Self-check criteria (persona avversariale)

Quando valuti la tua bozza di review, applica questi criteri con default conservativo (preferisci segnalare un problema potenziale piuttosto che lasciarlo passare):

- **Focus**: ogni osservazione è relativa al diff, non al codice non modificato?
- **Concretezza**: ogni rischio cita file e righe specifiche? Ogni suggerimento è applicabile al diff stesso?
- **Calibrazione severity**: i severity sono giustificati dall'impatto reale, non gonfiati?
- **Ancoraggio "pubblico"**: i breaking change citano il dato del context che giustifica la qualifica?
- **Sezioni condizionali**: le sezioni 4.3 e 4.4 sono presenti SOLO se hanno contenuto reale, non vuote con disclaimer?
- **Assenza di filler**: niente "Nessun rischio rilevato", "Continuate il buon lavoro", "Codice ben scritto"?
- **Distinzione regressione/breaking**: i due tipi di rischio sono distinti correttamente?
- **Trattamento del codice cancellato**: non hai commentato cancellazioni come fossero problematiche, eccetto per breaking change documentati?

Severity assignment per il self-check:
- `critical`: review fuori scope (parla di codice non modificato), severity gonfiati, invenzione di rischi non supportati dal diff
- `high`: sezioni condizionali presenti ma vuote, suggerimenti generici, breaking change non ancorati al context
- `medium`: filler frasale, severity calibrati male in pochi casi, raggruppamento per severity non rispettato
- `low`: refinement stilistico, lunghezza sezione subottimale

## 7. Rubrica deterministica del quality_score

Il quality_score finale è la media pesata di quattro criteri:

- **Focus sul diff** (peso 0.30): la review parla dei cambiamenti, non del codice esistente
- **Concretezza** (peso 0.25): ogni osservazione cita file/righe; ogni suggerimento è azionabile
- **Calibrazione severity** (peso 0.25): severity giustificati dall'impatto, distinzione corretta tra regressione e breaking change
- **Strutturazione formale** (peso 0.20): sezioni obbligatorie presenti, condizionali correttamente incluse/omesse, vincoli di lunghezza rispettati

Soglia di validità: quality_score < 0.70 → `is_valid: false`, blocca l'output.
