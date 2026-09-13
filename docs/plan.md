# CornHole League — piano di progetto (roadmap didattica)

## Contesto

Web app per gestire il campionato annuale di cornhole dell'associazione. Progetto piccolo, pensato per
imparare a essere autonomo su Django + React (dopo il FantaF1, che era Django con template server-side).
Ambito iniziale volutamente ridotto: **scontro diretto + salvataggio risultato + classifica**. Nessuna
regola di gioco da implementare. Il punteggio assegnato a ogni partita verrà deciso più avanti, quindi va
reso configurabile e non "cablato".

## Decisioni prese (dalle domande)

| Tema | Decisione |
|---|---|
| Architettura | SPA React (Vite) in `frontend/`; Django espone API REST (DRF) e in produzione serve anche la build. Un solo servizio, login con **sessione + cookie** (niente JWT, niente CORS in prod). |
| Giocatori | Giocatore = utente loggato. Ogni componente di una squadra deve avere un'utenza. |
| Inserimento risultato | Uno dei giocatori crea la partita già col punteggio; **tutti** gli altri partecipanti devono confermare (2 in singolo, 4 in doppio). |
| Tornei | Per ogni stagione: torneo **singolo** (1v1) e torneo **doppio** (2v2). Terzo torneo "ombra" = classifica **combinata** calcolata sommando i punti dei due tornei per giocatore (non è una tabella, è un calcolo). |
| Coppie | Libere, cambiano a ogni partita → nessuna entità "squadra"; i punti vanno ai singoli. |
| Calendario | Nessuno: partite registrate a posteriori. |
| Login | Solo **Google** per ora, via `django-allauth` (Apple = aggiungere un provider più avanti; richiede Apple Developer Program a pagamento, dominio verificato e HTTPS). |
| Metodo | **Io scrivo l'infrastruttura** (settings, Vite, allauth, Docker, deploy) spiegandola; **tu scrivi la logica** (modelli, servizio classifica, API, componenti React) — per ogni passo: concetto → scheletro/esempio → tu scrivi → io rivedo. |
| Deploy | Target: **VM Oracle + Docker Compose + Caddy (HTTPS automatico) + Neon** (vedi sezione Deploy). Fallback: Render come FantaF1. |

Assunzioni esplicite (correggibili): UI in italiano, codice/identificatori in inglese; classifiche visibili solo a utenti loggati (soci); stagioni e tornei creati dall'admin (tu) via Django admin, non da React; punteggio effettivo salvato (es. 21‑15), niente pareggi, nessun vincolo "si arriva a 21".

## Stack

- Python 3.14.6 (venv già presente) + **Django 6.1** (già installato; supporta 3.14 nativamente → niente workaround `django_compat` come nel FantaF1)
- `djangorestframework`, `django-allauth[socialaccount]` (modalità **headless** per SPA), `dj-database-url`, `psycopg[binary]`, `python-dotenv`, `whitenoise`, `gunicorn`
- Frontend: **Vite + React (JavaScript/JSX, non TypeScript per ridurre le novità)**, `react-router`, **Tailwind v4** via plugin `@tailwindcss/vite` (lo conosci già dal FantaF1; qui niente CLI standalone), `fetch` nativo con un piccolo helper `api.js` (CSRF incluso). Niente librerie di stato/query per ora.
- DB: SQLite in locale, **Neon (PostgreSQL)** in produzione via `DATABASE_URL` — stesso schema del FantaF1.
- Node 20.10 e Docker già installati sul Mac.

> Al momento dell'`pip install` verificare che DRF e allauth dichiarino supporto a Django 6.1; se uno dei due è indietro, ripiegare su Django 5.2 LTS.

## Struttura repo (target)

Il repo git è `/Users/gabro/Git/CornHoleLeagueOG/CornHoleLeagueOG` (remote GitHub `TheGabro/CornHoleLeagueOG`), ma la venv è nella cartella **esterna**. Fase 0 sistema questo.

```
CornHoleLeagueOG/            ← root del repo (aprire QUESTA in VS Code)
├─ .venv/                    ← ricreata qui, in .gitignore
├─ .env / .env.example
├─ manage.py
├─ config/                   ← progetto Django (settings, urls, wsgi)
├─ league/                   ← unica app Django
│  ├─ models.py  admin.py  serializers.py  views.py  urls.py  permissions.py
│  ├─ services/standings.py  ← logica classifica (funzioni pure, testabili)
│  └─ tests/
├─ frontend/                 ← Vite + React
│  ├─ src/{api.js, main.jsx, App.jsx, pages/, components/}
│  └─ dist/                  ← build, in .gitignore, servita da Django in prod
├─ docs/                     ← questo piano + appunti per fase (come docs/plans del FantaF1)
├─ Dockerfile  docker-compose.yml  Caddyfile
└─ .claude/launch.json
```

## Modello dati

```
User (AbstractUser custom, definito PRIMA della prima migrazione — regola d'oro Django)
   + nickname (opzionale, mostrato in classifica)

Season      name, year, is_active
Tournament  season FK, name, kind ∈ {SINGLES, DOUBLES}, points_win=3, points_loss=0, is_active
Match       tournament FK, played_at (date), score_a, score_b,
            status ∈ {PENDING, CONFIRMED, REJECTED}, created_by FK, created_at, notes
MatchPlayer match FK, user FK, side ∈ {A, B}, confirmed (bool), confirmed_at
            unique (match, user)
```

Regole (in `Match.clean()` / serializer): giocatori per lato = 1 se SINGLES, 2 se DOUBLES; un utente non può stare su entrambi i lati; `score_a != score_b`; chi crea la partita deve esserne un partecipante ed è auto‑confermato; la partita passa a CONFIRMED quando tutti i `MatchPlayer` sono confermati; un `reject` la porta a REJECTED (il creatore può correggerla → tornano tutte le conferme a `False`).

Perché `points_win/points_loss` sul torneo e niente colonna "punti" sulla partita: i punti sono **derivati**, si calcolano al volo dalla regola corrente → cambiare la regola non richiede migrazione dei dati. Se in futuro la regola diventa complessa (bonus scarto, ecc.) si estende `services/standings.py`.

## Classifica (`league/services/standings.py`)

- `tournament_standings(tournament)` → per utente: played, won, lost, points_for, points_against, diff, **points**; solo partite CONFIRMED; ordinamento points ↓, diff ↓, won ↓, nickname.
- `season_combined_standings(season)` → somma per utente delle righe dei tornei della stagione (il torneo "ombra").
- Funzioni pure sopra i queryset, coperte da test unitari. È il pezzo di logica più importante ed è tuo.

## API (DRF, session auth + CSRF)

| Metodo | Path | Note |
|---|---|---|
| GET | `/api/me/` | utente corrente (o endpoint sessione di allauth) |
| GET | `/api/players/` | utenti attivi, per scegliere avversari/compagni |
| GET | `/api/seasons/`, `/api/tournaments/?season=` | sola lettura |
| GET/POST | `/api/matches/?tournament=` | POST con `players` annidati `[{user, side}]` + punteggi |
| GET | `/api/matches/{id}/` | dettaglio con partecipanti e stato conferme |
| POST | `/api/matches/{id}/confirm/`, `/reject/` | custom action, solo partecipanti |
| GET | `/api/tournaments/{id}/standings/` | classifica torneo |
| GET | `/api/seasons/{id}/standings/` | classifica combinata ("ombra") |

Login: `/_allauth/browser/v1/auth/provider/redirect` (POST form → Google → callback → cookie di sessione) e `/_allauth/browser/v1/auth/session` per sapere chi è loggato. Tutto sotto lo stesso dominio → in dev Vite fa da proxy verso Django (`server.proxy` per `/api` e `/_allauth`), quindi **zero CORS** anche in sviluppo.

## Pagine React

`/login` (bottone Google) · `/` dashboard (stagione attiva, tornei, "partite da confermare") ·
`/tournaments/:id` classifica + ultime partite · `/matches/new` form (torneo → giocatori per lato → punteggi) ·
`/matches/:id` dettaglio con Conferma/Rifiuta · `/seasons/:id/combined` classifica ombra.

## Fasi (ogni fase = una o più sessioni; chiude con commit + appunti in `docs/`)

Legenda: **[IO]** infrastruttura che scrivo e spiego · **[TU]** logica che scrivi tu con concetto + scheletro + revisione.

### Fase 0 — Igiene repo
[IO] venv dentro il repo, `.gitignore`, `requirements.txt`, `.env.example`, `docs/` con questo piano. Branch `develop` come nel FantaF1.
*Impari:* perché la venv sta nel repo ma non in git; flusso branch feature → develop → main.

### Fase 1 — Progetto Django + User custom + settings
[IO] `django-admin startproject config .`, settings con `.env`, `DATABASE_URL` (SQLite fallback), `AUTH_USER_MODEL`.
[TU] `league/models.py`: classe `User(AbstractUser)` con `nickname`; `admin.py`; prima migrazione; superuser.
*Impari:* perché il custom user va fatto subito; settings per ambiente; `makemigrations`/`migrate`.
*Verifica:* `manage.py check`, login in `/admin/`.

### Fase 2 — Modelli di dominio
[TU] Season, Tournament, Match, MatchPlayer + `clean()` + registrazione in admin (inline dei MatchPlayer).
*Impari:* FK/`related_name`, `TextChoices`, `UniqueConstraint`, validazione a livello modello, `select_related`.
*Verifica:* creare stagione/torneo/partita dall'admin; `manage.py shell` per interrogare.

### Fase 3 — Servizio classifica + test
[TU] `services/standings.py` e `tests/test_standings.py` (casi: nessuna partita, solo pending, singolo, doppio, combinata, parità di punti).
*Impari:* separare la logica dalle view (come `fantaApp/services/` nel FantaF1), `TestCase`, fixture in codice.
*Verifica:* `manage.py test league`.

### Fase 4 — API con DRF
[IO] installazione DRF, `REST_FRAMEWORK` (SessionAuthentication, IsAuthenticated), router, **un** ViewSet di esempio (`SeasonViewSet`) commentato.
[TU] serializer + viewset per Tournament, Match (creazione con `players` annidati, validazione), azioni `confirm`/`reject`, endpoint standings, `permissions.py` (`IsParticipant`).
*Impari:* serializer vs form, ViewSet/Router, `@action`, permessi, come DRF gestisce CSRF con la sessione.
*Verifica:* browsable API su `/api/`, chiamate con `curl`/httpie loggato via admin.

### Fase 5 — Login Google (allauth headless)
[IO] configurazione allauth + provider Google + headless; walkthrough Google Cloud Console (OAuth client, redirect URI `http://localhost:8000/accounts/google/login/callback/` in dev); `ACCOUNT_EMAIL_VERIFICATION` auto per email Google verificate; `/api/me/`.
*Impari:* cos'è OAuth2/OIDC in 5 minuti, sessione vs token, perché il cookie di sessione basta per una SPA sullo stesso dominio, cosa cambierà per Apple.
*Verifica:* login con Google da una pagina minimale → `/api/me/` risponde col tuo utente.

### Fase 6 — Scaffold frontend
[IO] `npm create vite@latest frontend`, Tailwind v4 plugin, react-router, proxy dev, `src/api.js` (fetch con `credentials`, header `X-CSRFToken` letto dal cookie), `AuthContext` minimo, layout/navbar, `.claude/launch.json` con due server (Django 8000 + Vite 5173).
*Impari:* cosa fa Vite, come è fatto un componente, props/state/effects, perché serve il proxy, il tema chiaro/scuro con `data-theme` come nel FantaF1 ma via Tailwind plugin.
*Verifica:* `npm run dev`, pagina che mostra "Ciao {nickname}" dopo login.

### Fase 7 — Pagine
[TU] le pagine elencate sopra, una alla volta: login → dashboard → classifica → nuova partita → dettaglio/conferma → combinata.
*Impari:* form controllati, fetch + stati loading/error, routing con parametri, componenti riusabili (tabella classifica usata da 3 pagine), aggiornamento UI dopo un POST.
*Verifica:* flusso completo a mano con 2 account Google (tuo + uno di test).

### Fase 8 — Build di produzione servita da Django
[IO] `vite build` → `frontend/dist`; `STATICFILES_DIRS` + WhiteNoise; `TemplateView` catch‑all che serve `dist/index.html` (esclusi `/api`, `/admin`, `/_allauth`); `DEBUG=False` in locale per provare.
*Impari:* differenza dev server vs build, hashing degli asset, perché la SPA ha bisogno del catch‑all.
*Verifica:* `gunicorn config.wsgi` in locale con build servita.

### Fase 9 — Deploy
[IO+TU insieme] Dockerfile multi‑stage (stage Node per la build, stage Python per gunicorn), `docker-compose.yml` (web + caddy), `Caddyfile` (HTTPS automatico Let's Encrypt), setup VM Oracle (Docker, apertura porte 80/443 in security list **e** iptables), Neon `DATABASE_URL`, redirect URI Google di produzione, DNS.
*Impari:* container multi‑stage, reverse proxy, variabili d'ambiente in prod, migrazioni su Neon, rollback = redeploy immagine precedente.
*Verifica:* checklist come `docs/plans/release-v0.2-neon.md` del FantaF1 (build immagine, migrate su Neon, login Google in prod, admin raggiungibile, nessun segreto in git).

## Deploy — risposte alle tue domande

**VM Oracle invece di Render: sì, ha senso.** Ti serve: (1) Docker + Compose sulla VM; (2) porte 80/443 aperte sia nella *Security List* della VCN Oracle sia nel firewall del SO (le immagini Ubuntu di Oracle hanno regole iptables restrittive di default — è la trappola classica); (3) un **dominio** che punti all'IP pubblico della VM; (4) Caddy come reverse proxy: ottiene e rinnova il certificato HTTPS da solo. Il DB resta su Neon (nessun Postgres da gestire sulla VM, backup inclusi).

**Dominio dell'associazione: sì, basta un sottodominio.** Se l'associazione ha `esempio.it`, chi gestisce il DNS aggiunge un record `A` `cornhole.esempio.it → <IP VM>`. Il sito principale non viene toccato. Serve solo l'accesso al pannello DNS (o chiedere a chi ce l'ha).

**Cosa serve per far "girare" l'app online:** dominio (o sottodominio) → HTTPS (Caddy) → l'URL `https://cornhole.esempio.it/accounts/google/login/callback/` va aggiunto ai *redirect URI autorizzati* nel client OAuth Google. Google **non** accetta IP nudi né `http` per i redirect in produzione: senza dominio il login Google in prod non parte. In sviluppo invece `localhost` è accettato, quindi il dominio non ti blocca fino alla Fase 9.

**Se il dominio non arriva:** opzione A — dominio economico (~10 €/anno); opzione B — sottodominio gratuito DuckDNS (funziona con Caddy, con Google è accettato ma è "da laboratorio"); opzione C — Render come FantaF1: ti dà gratis `nome.onrender.com` in HTTPS, zero configurazione server, ma il free tier va in sleep. Per la consent screen Google, con soli scope `openid email profile` non serve la verifica dell'app: puoi restare in modalità *Testing* (max 100 utenti test) o pubblicare.

## Metodo di lavoro (rituali)

- Ogni sessione parte con "Fase N, ultimo passo fatto, prossimo passo" (come `docs/plans/chat-context-template.md` del FantaF1).
- Per i passi **[TU]**: prima ti spiego il concetto e ti mostro un esempio *diverso* da quello che devi scrivere (non copiabile pari pari), poi scrivi tu, poi revisiono e ti chiedo di spiegare una scelta.
- Per i passi **[IO]**: scrivo il file e lo commentiamo insieme; nessun file "magico" senza spiegazione.
- Un branch `feature/<fase>` per fase, PR verso `develop`, merge; `main` solo per i deploy.
- In `docs/` un file breve per fase con "cosa ho imparato / dubbi" scritto da te: serve a te per la prossima app.

## Verifica end‑to‑end (a fine roadmap)

1. Due utenti fanno login con Google.
2. L'admin crea stagione 2026 con tornei Singolo e Doppio dall'admin.
3. Utente A registra una partita di singolo 21‑15 contro B → B la vede "da confermare" → conferma → compare in classifica singolo.
4. Quattro utenti: partita di doppio; finché uno non conferma non entra in classifica; un `reject` la marca e permette la correzione.
5. Classifica combinata = somma delle due.
6. `manage.py test league` verde; build Vite servita da Django con `DEBUG=False`; deploy su VM con HTTPS e login Google funzionante.
