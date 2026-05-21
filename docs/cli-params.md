# Parametri CLI di cutf

Il comando pubblico del pacchetto e `cutf`. L'entrypoint e definito in [pyproject.toml](../pyproject.toml#L25) e la CLI viene costruita in [cutf/app.py](../cutf/app.py#L51).

## Sintassi generale

```text
cutf --path PERCORSO --list-extension [--skip-dir NOME [NOME ...]]
cutf --path PERCORSO [flag operativi] [--ai-ollama-url URL] [--skip-dir NOME [NOME ...]] --extensions .ext1 .ext2 ...
```

## Vincoli obbligatori

Il programma impone due regole iniziali, validate in [cutf/app.py](../cutf/app.py) e coperte anche dai test in [tests/test_app.py](../tests/test_app.py):

1. Devi specificare almeno una modalita operativa tra `--checks`, `--convert`, `--all`, `--fix-wrong-with-ai` o `--list-extension`.
2. Devi specificare almeno un'estensione con `--extensions` per le modalita `--checks`, `--convert`, `--all` e `--fix-wrong-with-ai`.

Inoltre:

1. `--fix-wrong-with-ai` non puo essere combinato con `--checks`, `--convert`, `--all` o `--list-extension`
2. `--list-extension` e una modalita dedicata e puo essere usata solo con `--path` e l'opzionale `--skip-dir`
3. se usi `--fix-wrong-with-ai`, devi fornire un URL Ollama tramite `--ai-ollama-url`, variabile d'ambiente `OLLAMA_URL` o file `.env` vicino all'eseguibile

Inoltre, prima di partire:

1. verifica che il path passato esista davvero come file o directory, in [cutf/app.py](../cutf/app.py)
2. verifica che `iconv` sia disponibile nel `PATH` di sistema solo quando serve il flusso standard di check/conversione, in [cutf/app.py](../cutf/app.py)

Se `iconv` manca, il programma termina con errore solo per le modalita che passano dal flusso standard dei file. Le modalita `--fix-wrong-with-ai` e `--list-extension` non lo richiedono.

## Elenco dettagliato dei parametri

### `--path`

Definito in [cutf/app.py](../cutf/app.py).

Serve a indicare il file o la directory da processare.

Puo puntare a:

1. un file singolo
2. una directory

Comportamento:

1. se il path e un file, viene processato solo quel file
2. se il path e una directory, il tool scorre ricorsivamente tutti i file con `os.walk`, come si vede in [cutf/app.py](../cutf/app.py#L171)
3. se usi `--skip-dir`, le directory con nome corrispondente vengono potate dalla ricorsione prima della discesa

Nota pratica: anche nel caso di file singolo, il file viene comunque sottoposto al filtro delle estensioni ammesse.

Eccezione importante:

1. in modalita `--list-extension`, il file singolo viene contato sempre, anche senza `--extensions`

### `--skip-dir`

Definito in [cutf/app.py](../cutf/app.py).

Serve a escludere directory per nome durante la scansione ricorsiva.

Comportamento reale:

1. il match e per nome esatto della cartella, ovunque sotto il path iniziale
2. puoi passare piu nomi nella stessa occorrenza, per esempio `--skip-dir .git node_modules`
3. puoi ripetere il flag, per esempio `--skip-dir .git --skip-dir node_modules`
4. quando il tool incontra una directory da saltare, stampa subito un messaggio con il path skippato
5. una directory skippata non viene attraversata e quindi i file al suo interno non vengono mai passati al controller dei file

Esempio pratico:

1. `cutf --path C:\dev --all --extensions .py .cs --skip-dir .git`

In questo caso tutte le cartelle `.git` trovate sotto `C:\dev` vengono ignorate.

Nota pratica:

1. il flag ha effetto solo quando `--path` punta a una directory
2. se il nome e scritto con maiuscole o minuscole diverse, su Windows il confronto segue il comportamento naturale del filesystem

### `--list-extension`

Definito in [cutf/app.py](../cutf/app.py).

Attiva una modalita dedicata che non esegue controlli, conversioni o fix AI: si limita a censire tutte le estensioni trovate sotto il path indicato.

Cosa fa realmente:

1. accetta solo `--path` e l'opzionale `--skip-dir`
2. se il path e una directory, scorre ricorsivamente tutti i file con `os.walk`
3. se il path e un file, conta solo quel file
4. usa `os.path.splitext` per ricavare l'estensione e normalizza il risultato in minuscolo
5. aggrega i file senza suffisso nella voce `(no extension)`
6. rispetta le directory escluse con `--skip-dir`
7. stampa una tabella `rich` con estensione e conteggio file
8. non richiede `--extensions`
9. non usa `iconv`
10. non chiede conferma all'utente

Esempi:

1. `cutf --path C:\dev --list-extension`
2. `cutf --path C:\dev --list-extension --skip-dir .git node_modules`

### `--checks`

Definito in [cutf/app.py](../cutf/app.py).

Abilita il controllo dei caratteri problematici nel file.

Cosa fa realmente:

1. non converte il file
2. esegue una scansione del testo decodificato alla ricerca del carattere di sostituzione `�`
3. calcola per ogni occorrenza linea, posizione nel testo e offset nel file
4. per ogni occorrenza salva informazioni come linea, posizione, stringa coinvolta e se la riga e commento o codice

La logica e implementata in [cutf/controller/fileChecker.py](../cutf/controller/fileChecker.py).

Quando e attivo da solo:

1. il file viene solo analizzato
2. nessuna conversione viene eseguita

### `--convert`

Definito in [cutf/app.py](../cutf/app.py).

Abilita la conversione dei file non UTF verso UTF-8 con BOM.

Comportamento reale:

1. il tool rileva la codifica del file con `chardet`, in [cutf/controller/fileController.py](../cutf/controller/fileController.py#L43)
2. controlla se la codifica e gia considerata UTF-like, in [cutf/controller/fileController.py](../cutf/controller/fileController.py#L55)
3. converte il file solo se la conversione e davvero necessaria, in [cutf/controller/fileController.py](../cutf/controller/fileController.py#L60)

Le codifiche considerate gia compatibili e quindi non convertite sono:

1. `utf-8`
2. `utf-8-sig`
3. `utf-16`
4. `utf-16le`
5. `utf-16be`

Questo significa che `--convert` non forza sempre la riscrittura del file. Converte solo i file che risultano fuori da questo gruppo.

Quando la conversione avviene:

1. il file viene convertito tramite `iconv`
2. subito dopo viene eseguito anche il controllo dei caratteri problematici

Questa parte e in [cutf/controller/fileController.py](../cutf/controller/fileController.py#L68).

### `--copyOld`

Definito in [cutf/app.py](../cutf/app.py).

Crea una copia del file originale prima della conversione.

Importante:

1. funziona solo se il file deve davvero essere convertito
2. se il file e gia considerato UTF-like, non viene creato nessun backup

La condizione si vede in [cutf/controller/fileController.py](../cutf/controller/fileController.py#L63).

Dove finisce la copia:

1. nella cartella temporanea di sistema
2. dentro una sottocartella chiamata `SrcChE`

Questa logica e in [cutf/util/path.py](../cutf/util/path.py#L6).

### `--printMissingCharString`

Definito in [cutf/app.py](../cutf/app.py).

Fa stampare anche il contenuto della riga in cui e stato trovato un carattere problematico.

Effetto concreto:

1. nel report non vedi solo file, linea e posizione
2. vedi anche la stringa completa coinvolta

E usato in:

1. [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py)
2. [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py)

Ha senso soprattutto insieme a:

1. `--checks`
2. `--convert`
3. `--all`

### `--printAllSkippedFile`

Definito in [cutf/app.py](../cutf/app.py).

Controlla come vengono mostrati i file saltati.

Comportamento:

1. se il flag non e presente, il report mostra solo il conteggio dei file skipped
2. se il flag e presente, il report elenca uno per uno tutti i file saltati

La logica e in [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py).

Un file viene segnato come skipped quando:

1. non ha un'estensione supportata
2. oppure non c'e alcuna operazione utile da eseguire su quel file

### `--all`

Definito in [cutf/app.py](../cutf/app.py).

E una scorciatoia che abilita insieme:

1. `--checks`
2. `--convert`

In [cutf/app.py](../cutf/app.py) si vede che:

1. `enable_checks` e vero se hai passato `--checks` oppure `--all`
2. `enable_convert` e vero se hai passato `--convert` oppure `--all`

Quindi `--all` equivale a dire: controlla sempre i file e converti quelli che ne hanno bisogno.

### `--verbose`

Definito in [cutf/app.py](../cutf/app.py).

Abilita una modalita con log piu dettagliati.

Effetti concreti:

1. stampa messaggi aggiuntivi durante la scansione
2. mostra piu dettagli su apertura file, controlli, conversione e completamento
3. rende piu esplicite anche le intestazioni del report finale

Le stampe aggiuntive sono visibili in:

1. [cutf/controller/fileController.py](../cutf/controller/fileController.py)
2. [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py)

Non cambia la logica del programma. Cambia solo la quantita di output mostrato.

### `--only-relevant`

Definito in [cutf/app.py](../cutf/app.py).

Serve a filtrare il report dei caratteri problematici per mostrare solo i risultati considerati piu utili.

Effetti concreti:

1. nasconde tutta la sezione dei missing chars trovati nei commenti, come in [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py)
2. nella sezione del codice nasconde le occorrenze meno utili, come in [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py)

In pratica:

1. senza questo flag ottieni un report piu completo
2. con questo flag ottieni un report piu sintetico e meno rumoroso

### `--extensions`

Definito in [cutf/app.py](../cutf/app.py).

E un parametro multi-valore obbligatorio per le modalita di scansione standard.

Accetta una o piu estensioni separate da spazio, per esempio:

1. `--extensions .py`
2. `--extensions .cpp .h .cs .ini`

Comportamento reale:

1. il confronto e case-insensitive
2. le estensioni vengono normalizzate in minuscolo
3. il match e esatto sull'estensione ottenuta da `os.path.splitext`
4. non viene usato in modalita `--list-extension`

La logica e in [cutf/controller/fileController.py](../cutf/controller/fileController.py).

### `--fix-wrong-with-ai`

Definito in [cutf/app.py](../cutf/app.py).

Attiva una modalita interattiva dedicata per correggere i caratteri `�` con l'aiuto di Ollama.

Comportamento reale:

1. non esegue nessuna conversione di codifica
2. scansiona ogni file compatibile per trovare il carattere `�`
3. per ogni occorrenza invia a Ollama la riga corrente, la posizione del carattere e il contesto vicino
4. mostra in CLI la riga originale e la riga proposta
5. chiede all'utente se applicare, ritentare o saltare
6. se l'utente approva, riscrive il file mantenendo la codifica e il BOM originali
7. dopo la scrittura verifica che il carattere sia stato davvero sostituito

La logica passa da:

1. [cutf/controller/fileController.py](../cutf/controller/fileController.py)
2. [cutf/controller/aiFixController.py](../cutf/controller/aiFixController.py)
3. [cutf/util/ollama.py](../cutf/util/ollama.py)
4. [cutf/util/textfile.py](../cutf/util/textfile.py)

Scelte interattive disponibili:

1. `1` applica la modifica proposta
2. `2` richiede una nuova proposta a Ollama
3. `3` lascia invariato quel carattere e passa al successivo

Modello usato di default:

1. `qwen2.5:1.5b-instruct`

### `--ai-ollama-url`

Definito in [cutf/app.py](../cutf/app.py).

Permette di specificare esplicitamente l'URL base di Ollama per la modalita `--fix-wrong-with-ai`.

Ordine di risoluzione dell'URL:

1. valore passato con `--ai-ollama-url`
2. chiave `OLLAMA_URL` in un file `.env` nella stessa cartella dell'eseguibile
3. variabile d'ambiente `OLLAMA_URL` del processo corrente
4. variabile d'ambiente utente corrente su Windows, se disponibile

Esempio:

1. `--ai-ollama-url http://localhost:11434`

Effetto pratico:

1. decide quali file vengono davvero processati
2. vale sia quando passi una directory sia quando passi un file singolo

## Interazioni importanti tra i flag

### `--checks` da solo

Esegue solo il controllo dei caratteri problematici. Non converte nulla.

### `--convert` da solo

Converte i file solo se la codifica rilevata non e gia nel gruppo considerato UTF-like.

Se il file e gia ritenuto compatibile:

1. non viene convertito
2. non viene controllato, a meno che non sia attivo anche `--checks` o `--all`

### `--all`

E la modalita piu completa:

1. esegue i controlli
2. converte quando necessario

### `--fix-wrong-with-ai`

E una modalita separata:

1. non puo convivere con `--checks`, `--convert`, `--all` o `--list-extension`
2. non usa `iconv`
3. non cambia la codifica del file
4. richiede un endpoint Ollama raggiungibile

### `--list-extension`

E una modalita separata:

1. non puo convivere con `--checks`, `--convert`, `--all` o `--fix-wrong-with-ai`
2. puo essere usata solo con `--path` e l'opzionale `--skip-dir`
3. non usa `iconv`
4. non richiede `--extensions`
5. non chiede conferma
6. non genera `FileScanResult`, ma stampa direttamente una tabella riepilogativa

### `--copyOld` senza conversione reale

Non crea nessun backup se il file non deve essere convertito.

### `--copyOld` in modalita AI o list-extension

Non ha effetto pratico, perche queste modalita non usano il flusso di conversione. In pratica `--list-extension` non accetta proprio questo flag.

### Flag di reportistica

Questi flag non cambiano quali file vengono processati, ma solo come vengono mostrati i risultati del flusso standard:

1. `--printMissingCharString`
2. `--printAllSkippedFile`
3. `--only-relevant`
4. `--verbose`

In modalita `--list-extension` questi flag non sono ammessi.

## Flusso generale della CLI

La funzione principale e in [cutf/app.py](../cutf/app.py) e segue questo ordine:

1. parse degli argomenti
2. validazione minima dei flag obbligatori
3. risoluzione eventuale di `OLLAMA_URL` per la modalita AI
4. verifica del path
5. creazione della configurazione [cutf/model/AppSetting.py](../cutf/model/AppSetting.py)
6. se e attiva `--list-extension`, censimento delle estensioni e stampa immediata della tabella
7. altrimenti verifica di `iconv` nel sistema solo se serve
8. richiesta di conferma all'utente
9. scansione di file singolo o directory
10. stampa del report finale con [cutf/controller/resultHandler.py](../cutf/controller/resultHandler.py)

## Esempi d'uso

### Solo controllo

```bash
cutf --path ./src --checks --extensions .py .cpp
```

### Conversione con backup

```bash
cutf --path ./src --convert --copyOld --extensions .cs .ini
```

### Modalita completa con report filtrato

```bash
cutf --path ./src --all --only-relevant --extensions .py .txt
```

### File singolo con log dettagliato

```bash
cutf --path ./main.cpp --all --verbose --extensions .cpp
```

### Lista estensioni trovate

```bash
cutf --path ./src --list-extension --skip-dir .git node_modules
```

### Correzione interattiva con Ollama

```bash
cutf --path ./src --fix-wrong-with-ai --extensions .cpp .py
```

### Correzione interattiva con URL esplicito

```bash
cutf --path ./src --fix-wrong-with-ai --ai-ollama-url http://localhost:11434 --extensions .cpp
```
