---
name: pytest_generation
version: 2.0
applies_to: [test]
priority: 80
max_output_words: 1200
conflict_resolution: project_rules_wins
inject_position: middle
self_check_persona: adversarial
---

# pytest_generation v2.0

## 1. Scopo della skill

Generare test pytest per un file Python target. I test devono riflettere il comportamento osservabile del file, non inventarne uno nuovo. La copertura privilegia profondità su ampiezza: meglio dieci test ben pensati che venti ripetitivi.

## 2. Dati del context utilizzati

Questa skill legge i seguenti campi dal context strutturale. Se un campo non è disponibile nella versione corrente del sistema, ometti la decisione condizionale corrispondente senza segnalarlo come problema.

- `semantic_context.functions` — lista delle funzioni del file con signature, complexity, line_count
- `semantic_context.classes` — lista delle classi del file
- `code_quality_context.god_classes` — classi marcate come god class
- `code_quality_context.long_methods` — metodi marcati come long
- `code_quality_context.complexity_warnings` — funzioni con complessità ciclomatica alta
- `architectural_risk_context.high_fan_out` — funzioni con fan-out elevato
- `cross_file_context.function_calls` — quali funzioni del file target sono chiamate da altri file (segnale di "pubblico de facto")

## 3. Stile pytest atteso

Convenzioni obbligatorie:

- Funzioni di test nominate `test_<funzione>_<scenario>` (snake_case, descrittivo, mai generico tipo `test_function_1`)
- Pattern Arrange-Act-Assert esplicito: tre blocchi separati da una riga vuota, anche per test brevi
- Fixture pytest per setup condiviso tra più test della stessa classe o modulo
- `pytest.mark.parametrize` quando si testano più casi simili sullo stesso comportamento
- Type hint sui parametri delle funzioni di test (coerente con `project_rules`)
- Docstring breve (una riga) che spiega COSA verifica il test, non COME

Vincoli operativi:

- Niente import wildcard (`from module import *` è vietato)
- Usa `pytest.raises` per testare eccezioni, mai `try/except` con assert nei branch
- Ogni test verifica UN COMPORTAMENTO. Più assert per test sono ammessi se riguardano lo stesso comportamento (esempio: una funzione ritorna una tupla, verifica tutti gli elementi). È sbagliato un test che verifica contemporaneamente happy path e error case.
- Mock di dipendenze esterne (file I/O, network, time) con `monkeypatch` o `unittest.mock` quando necessario per evitare side effect

## 4. Definizione di "funzione pubblica"

Una funzione del file target è considerata pubblica se soddisfa almeno una di queste condizioni:

- Il nome non inizia con underscore
- Il nome compare in `__all__` del modulo (se presente)
- Il nome compare in `cross_file_context.function_calls` come target (è chiamata da almeno un altro modulo)

Le funzioni che non sono pubbliche secondo questa definizione possono comunque essere testate se sono complesse o critiche, ma non è obbligatorio.

## 5. Copertura attesa

Per ogni funzione pubblica del file target:

- **Sempre**: un test del caso felice (input valido tipico, verifica del risultato atteso)
- **Se la funzione ha più di due parametri non banali, o tipi complessi (Dict, List nested, oggetti Pydantic)**: aggiungi un test di edge case (valori limite, container vuoti, valori null/None dove ammessi)
- **Se la signature dichiara `raise` espliciti, o la funzione fa I/O, parsing, type coercion**: aggiungi un test di errore atteso (input invalido → eccezione corretta con `pytest.raises`)
- **Se la funzione appare in `code_quality_context.complexity_warnings` o ha complessità > 7**: aggiungi un test per ogni branch logico rilevante (un test per ramo del flusso di controllo, non un test per ogni `if`)

Limite operativo assoluto: massimo 20 test totali per file. Se il file ne richiederebbe di più applicando le regole, prioritizza in questo ordine:
1. Funzioni in `cross_file_context.function_calls` (usate altrove, alta criticità)
2. Funzioni in `code_quality_context.complexity_warnings` (alta complessità, alto rischio bug)
3. Funzioni in `god_classes` o `long_methods` (alto valore di copertura)
4. Resto delle funzioni pubbliche in ordine di apparizione

## 6. Protocollo bug

Se identifichi un bug nel codice originale durante la stesura dei test, NON correggerlo nei test. Il test deve asserire il comportamento attuale (anche buggy) e il bug va segnalato con un commento Python sopra l'asserzione del comportamento errato.

Esempio:

```python
def test_calculate_total_handles_empty_list():
    # BUG: la funzione ritorna None invece di 0 per lista vuota.
    # Comportamento osservato preservato per non rompere chiamanti esistenti.
    result = calculate_total([])
    assert result is None
```

In questo modo:
- Il test cattura il comportamento attuale (regressione test)
- Il bug è documentato esplicitamente nel codice
- Chi correggerà il bug aggiornerà sia la funzione sia il test

## 7. Formato dell'output

L'output è un file pytest puro, pronto per essere salvato come `test_<modulo>.py` ed eseguito senza modifiche.

Vincoli stretti:

- Nessun blocco markdown (no triple backtick di apertura/chiusura)
- Nessuna prefazione (no "Ecco i test richiesti")
- Nessuna postfazione (no "Spero che questi test ti siano utili")
- Nessun commento di sezione tipo `# === SETUP ===`
- Solo: shebang opzionale, docstring del modulo opzionale, import, fixture, classi/funzioni di test

Struttura tipica:

```python
"""Test suite for <module_name>."""

import pytest

from <module_path> import <funzioni_da_testare>


@pytest.fixture
def sample_input():
    return {...}


def test_function_happy_path(sample_input):
    """Verifica che function ritorni il risultato atteso su input valido."""
    # Arrange
    expected = {...}

    # Act
    result = function(sample_input)

    # Assert
    assert result == expected
```

## 8. Self-check criteria (persona avversariale)

Quando valuti la tua bozza di test, applica questi criteri con default conservativo (preferisci segnalare un problema potenziale piuttosto che lasciarlo passare):

- **Esecuzione**: il file è pytest valido? `pytest --collect-only` non darebbe errori?
- **Determinismo**: nessun test dipende da ordine di esecuzione, timing, file system non controllato, network?
- **Significato**: ogni test verifica un comportamento osservabile, non un dettaglio implementativo?
- **Indipendenza**: i test non condividono stato mutabile attraverso variabili globali o classi?
- **Ripetibilità**: lanciare i test 100 volte produce 100 successi (o 100 fallimenti coerenti)?
- **Copertura**: ogni funzione pubblica ha almeno il caso felice? Le condizioni delle sezioni 5 sono rispettate?
- **Conformità**: type hint, naming, struttura AAA, max 20 test rispettati?
- **Protocollo bug**: se hai notato un bug, è documentato come commento `# BUG:` sopra l'assert?

Severity assignment:
- `critical`: il file non parsa, ha syntax error, contiene wildcard, o testa il framework anziché la funzione
- `high`: test non deterministici, dipendenze tra test, mancata copertura di funzioni in `cross_file_context`
- `medium`: copertura subottimale di edge case, naming poco descrittivo, mancanza di docstring
- `low`: refinement stilistico, fixture estraibili, parametrize applicabile

## 9. Rubrica deterministica del quality_score

Il quality_score finale è la media pesata di quattro criteri, ciascuno valutato da 0.0 a 1.0:

- **Correttezza tecnica** (peso 0.25): i test esprimono asserzioni corrette sul comportamento del codice originale
- **Copertura** (peso 0.25): le funzioni pubbliche e critiche sono testate secondo le regole della sezione 5
- **Conformità formale** (peso 0.25): pytest valido, type hint, naming, struttura AAA, no wildcard
- **Densità informativa** (peso 0.25): no test ripetitivi, no asserzioni banali, ogni test produce informazione utile

Soglia di validità: quality_score < 0.70 → `is_valid: false`, blocca l'output.
