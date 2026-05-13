---
name: python_generation
version: 2.0
applies_to: [generate]
load_examples: true
load_templates: true
priority: high
max_output_words:
  concise: unlimited
  verbose: unlimited
conflict_resolution: >
  In caso di conflitto con project_rules, project_rules ha sempre precedenza.
  Regola specifica di questo file: funzioni max 40 righe (da project_rules).
  Se un template supera 40 righe, estrailo in funzioni private.
description: >
  Regole per la generazione di codice Python pulito, coerente e pronto
  all'uso. Include struttura canonica, pattern preferiti, anti-pattern,
  esempi di output atteso e checklist di self-verifica.
---

════════════════════════════════════════════════════════════
PYTHON GENERATION — REGOLE E STANDARD
════════════════════════════════════════════════════════════

════════════════════════════════════════════════════════════
SEZIONE 1 — OBIETTIVO
════════════════════════════════════════════════════════════

Produci codice Python che:
  1. Funziona correttamente al primo utilizzo
  2. È leggibile da chi non lo ha scritto
  3. È testabile senza modifiche (dipendenze iniettabili)
  4. È estendibile senza riscritture

Non generare "codice che potrebbe funzionare".
Genera codice che funziona.

════════════════════════════════════════════════════════════
SEZIONE 2 — STRUTTURA CANONICA
════════════════════════════════════════════════════════════

── ORDINE DEGLI IMPORT ───────────────────────────────────

  # 1. Standard library
  from __future__ import annotations
  import os
  from pathlib import Path
  from typing import Any, Literal, Optional

  # 2. Third-party (riga vuota di separazione)
  from pydantic import BaseModel, Field

  # 3. Internal (riga vuota di separazione)
  from assist.schemas.models import TaskInput

Usa sempre import assoluti. Mai `from . import x` nei moduli
principali (accettabile solo in `__init__.py`).

── STRUTTURA DI UNA FUNZIONE ────────────────────────────

  def nome_funzione(
      param1: str,
      param2: int,
      param3: Optional[str] = None,
  ) -> dict[str, Any]:
      """Breve descrizione in una riga.

      Descrizione estesa solo se necessaria.

      Args:
          param1: Descrizione. Non ripetere il tipo.
          param2: Descrizione.
          param3: Descrizione. Default None significa X.

      Returns:
          Descrizione del contenuto restituito.

      Raises:
          ValueError: Se param1 è vuoto.

      Example:
          >>> result = nome_funzione("test", 42)
          >>> result["key"]
          'value'
      """
      if not param1:
          raise ValueError(f"param1 non può essere vuoto, ricevuto: {param1!r}")

      result = _helper(param1, param2)
      return result

── STRUTTURA DI UNA CLASSE ──────────────────────────────

  class NomeClasse:
      """Breve descrizione della responsabilità della classe.

      Una classe ha una sola responsabilità.

      Attributes:
          attr1: Descrizione.
          attr2: Descrizione.
      """

      def __init__(self, attr1: str, attr2: int = 0) -> None:
          self.attr1 = attr1
          self.attr2 = attr2
          self._private: Optional[str] = None

      def metodo_pubblico(self) -> str:
          """Descrizione."""
          return self._metodo_privato()

      def _metodo_privato(self) -> str:
          return f"{self.attr1}:{self.attr2}"

════════════════════════════════════════════════════════════
SEZIONE 3 — PATTERN PREFERITI: USALI SEMPRE
════════════════════════════════════════════════════════════

── FAIL FAST: valida l'input all'inizio ─────────────────

  CORRETTO:
    def process(file_path: Path, max_lines: int) -> list[str]:
        if not file_path.exists():
            raise FileNotFoundError(f"File non trovato: {file_path}")
        if max_lines <= 0:
            raise ValueError(f"max_lines deve essere > 0, ricevuto: {max_lines}")
        # logica principale dopo le guardie

── PYDANTIC per strutture dati ──────────────────────────

  CORRETTO:
    class Config(BaseModel):
        model: str = Field(default="claude-3-5-sonnet-20241022")
        temperature: float = Field(default=0.2, ge=0.0, le=1.0)
        max_tokens: int = Field(default=4000, gt=0)

  PROIBITO:
    config = {"model": "...", "temperature": 0.2}   # dict non strutturato

── PATHLIB invece di os.path ────────────────────────────

  CORRETTO:
    from pathlib import Path
    content = Path("skills/project_rules/SKILL.md").read_text(encoding="utf-8")

  PROIBITO:
    import os
    path = os.path.join("skills", "project_rules", "SKILL.md")

── CONTEXT MANAGER per risorse ──────────────────────────

  CORRETTO:
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

  PROIBITO:
    f = open(file_path)
    content = f.read()
    f.close()

── ABC per interfacce sostituibili ──────────────────────

  CORRETTO:
    from abc import ABC, abstractmethod

    class LLMClient(ABC):
        @abstractmethod
        def complete(self, prompt: str, system: str = "") -> str:
            """Invia prompt al modello, restituisce la risposta."""
            ...

    class MockLLMClient(LLMClient):
        def __init__(self, response: str) -> None:
            self._response = response

        def complete(self, prompt: str, system: str = "") -> str:
            return self._response

── ECCEZIONE SPECIFICA con messaggio utile ───────────────

  CORRETTO:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Output LLM non è JSON valido: {e}") from e

  PROIBITO:
    try:
        data = json.loads(raw)
    except Exception:
        data = {}

════════════════════════════════════════════════════════════
SEZIONE 4 — GENERAZIONE DA SPECIFICA
════════════════════════════════════════════════════════════

Quando l'utente fornisce una specifica testuale o parziale:

  1. Identifica le entità: classi, funzioni, tipi
  2. Identifica i contratti: input, output, eccezioni possibili
  3. Genera nell'ordine: tipi → interfacce → implementazioni → helper
  4. Non inferire comportamenti non specificati.
     Se la specifica è ambigua, scegli il comportamento più
     conservativo e commentalo:

       # NOTA: la specifica non indica il comportamento su input vuoto.
       # Questa implementazione lancia ValueError. Modifica se necessario.

  5. Include sempre un Example nel docstring se la firma non è
     autoesplicativa.

════════════════════════════════════════════════════════════
SEZIONE 5 — ESEMPIO DI OUTPUT ATTESO
════════════════════════════════════════════════════════════

Di seguito un esempio completo di output accettabile per una
richiesta di generazione. Calibra il tuo output su questo standard.

INPUT UTENTE: "Genera una funzione che carica una skill dal filesystem."

OUTPUT CORRETTO:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


MAX_SKILL_SIZE_BYTES: int = 500_000


def load_skill(skill_path: Path) -> dict[str, Any]:
    """Carica e deserializza una skill dal filesystem.

    Args:
        skill_path: Percorso al file SKILL.md della skill.

    Returns:
        Dict con i metadati del frontmatter YAML. Contiene sempre
        le chiavi 'name', 'version', 'applies_to'.

    Raises:
        FileNotFoundError: Se skill_path non esiste.
        ValueError: Se il file supera MAX_SKILL_SIZE_BYTES, o se
                    il frontmatter è assente o malformato.

    Example:
        >>> skill = load_skill(Path("skills/python_generation/SKILL.md"))
        >>> skill["name"]
        'python_generation'
    """
    if not skill_path.exists():
        raise FileNotFoundError(
            f"Skill non trovata: {skill_path}. "
            "Verifica che il percorso sia corretto."
        )

    size = skill_path.stat().st_size
    if size > MAX_SKILL_SIZE_BYTES:
        raise ValueError(
            f"File skill troppo grande: {size} byte "
            f"(limite: {MAX_SKILL_SIZE_BYTES})."
        )

    content = skill_path.read_text(encoding="utf-8")
    return _parse_frontmatter(content, source=skill_path)


def _parse_frontmatter(content: str, source: Path) -> dict[str, Any]:
    """Estrae il frontmatter YAML dal contenuto di un SKILL.md.

    Args:
        content: Contenuto completo del file.
        source: Percorso del file, usato nei messaggi di errore.

    Returns:
        Dict con i metadati estratti.

    Raises:
        ValueError: Se il frontmatter è assente, malformato o
                    mancano chiavi obbligatorie.
    """
    if not content.startswith("---"):
        raise ValueError(
            f"Frontmatter YAML assente in {source}. "
            "Il file deve iniziare con '---'."
        )

    parts = content.split("---", maxsplit=2)
    if len(parts) < 3:
        raise ValueError(
            f"Frontmatter non chiuso in {source}. "
            "Assicurati di chiudere il blocco con '---'."
        )

    try:
        metadata: dict[str, Any] = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"YAML malformato in {source}: {e}") from e

    _validate_required_keys(metadata, source)
    return metadata


def _validate_required_keys(metadata: dict[str, Any], source: Path) -> None:
    """Verifica la presenza delle chiavi obbligatorie nel frontmatter.

    Args:
        metadata: Dict estratto dal frontmatter.
        source: Percorso del file per i messaggi di errore.

    Raises:
        ValueError: Se una o più chiavi obbligatorie sono assenti.
    """
    required = {"name", "version", "applies_to"}
    missing = required - set(metadata.keys())
    if missing:
        raise ValueError(
            f"Chiavi mancanti nel frontmatter di {source}: "
            f"{', '.join(sorted(missing))}"
        )
```

Questo esempio mostra:
  - Costante di modulo per il limite (no magic number)
  - Fail fast con messaggi di errore utili
  - Funzioni estratte (_parse_frontmatter, _validate_required_keys)
  - Docstring Google style con Example eseguibile
  - Type hints completi incluso il return type di _validate (-> None)
  - from e for encadré: nessuna funzione supera 40 righe

════════════════════════════════════════════════════════════
SEZIONE 6 — CHECKLIST SELF-VERIFICA PRIMA DI RESTITUIRE
════════════════════════════════════════════════════════════

Esegui questa checklist mentalmente prima di restituire il codice.
Se una voce è NO, correggi prima di procedere.

  [ ] Type hints su tutti i parametri e return type pubblici?
  [ ] Type hint su tutti i return type privati?
  [ ] Ogni funzione pubblica ha docstring con Args e Returns?
  [ ] Nessun magic number senza costante nominata?
  [ ] Nessun except Exception senza handling specifico?
  [ ] Nessuna funzione supera 40 righe?
  [ ] Import nell'ordine corretto (stdlib → third-party → internal)?
  [ ] Nessun TODO, FIXME, placeholder, pass non intenzionale?
  [ ] Il codice è eseguibile senza modifiche manuali?
  [ ] Example nel docstring per funzioni con signature non ovvia?
