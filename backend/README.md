# Backend

## Executar localmente

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## Executar com Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

Serviços previstos:

- `api` em `http://localhost:8000`
- `sync-worker` para sincronização diária agendada
- `db` PostgreSQL em `localhost:5433`
- `redis` em `localhost:6379`

## Infraestrutura atual

- Persistência com `SQLAlchemy`
- Banco padrão local em `SQLite` para desenvolvimento rápido
- Banco recomendado em ambiente containerizado: `PostgreSQL`
- `Redis` local em Docker para lock distribuído de jobs, base para fila/cache e operação sem custo de licença
- Seed inicial automática no startup da API
- Worker separado para sincronização diária agendada via `app.scheduler`

## Endpoints iniciais

- `GET /`
- `GET /health`
- `GET /public/config/languages`
- `GET /public/highlights`
- `GET /public/politicians`
- `GET /public/politicians/{politician_id}/history`
- `GET /public/bills`
- `GET /public/bills/approved?query=&year_from=&year_to=`
- `POST /auth/login`
- `POST /auth/oauth/google`
- `POST /auth/oauth/microsoft`
- `GET /auth/me`
- `POST /sync/daily`
- `POST /sync/historical?start_year=1988&end_year=1989&items_per_year=10`
- `POST /sync/historical?start_year=1988&end_year=1989&items_per_year=10&resume=true`
- `POST /sync/historical?start_year=1988&end_year=1989&items_per_year=0&batch_size=25&max_concurrency=5`
- `GET /sync/status`
- `GET /sync/runs`
- `GET /sync/issues?status=open&severity=error&issue_type=source_fetch_error`
- `GET /sync/historical/checkpoint`
- `GET /sync/historical/coverage`

## Observação

A sincronização diária agora executa uma ingestão inicial da API aberta da Câmara para popular parlamentares federais, proposições e uma timeline básica de tramitações.

O endpoint histórico foi preparado para backfill retroativo desde 1988, de forma incremental por faixa de anos. O backfill histórico passou a usar os arquivos anuais oficiais da Câmara para proposições, autores e temas, além de snapshots históricos de parlamentares por legislatura. O objetivo é cobrir tanto as proposições legislativas do período quanto todos os parlamentares federais de 1988 até hoje, sem depender apenas das relações derivadas das proposições.

## Estado atual dos workers e agendamento

- Existe um worker dedicado `sync-worker` no `docker-compose` para rodar a sincronização diária automaticamente.
- O agendamento é controlado por variáveis de ambiente.
- O horário padrão está configurado para `00:00` em `America/Sao_Paulo`.
- A sincronização também continua disponível sob demanda via endpoints HTTP internos.
- O `Redis` local em Docker é usado para evitar execuções concorrentes de sync diária e backfill histórico.
- Se o `Redis` estiver indisponível, a aplicação continua operando com fallback sem lock distribuído.

Variáveis disponíveis no `.env`:

- `SYNC_DAILY_ENABLED=true`
- `SYNC_DAILY_HOUR=0`
- `SYNC_DAILY_MINUTE=0`
- `SYNC_DAILY_TIMEZONE=America/Sao_Paulo`
- `REDIS_URL=redis://redis:6379/0`

## Operação manual da sincronização

- **Sincronização diária manual**

```bash
curl -X POST http://127.0.0.1:8000/sync/daily
```

- **Backfill histórico manual**

```bash
curl -X POST "http://127.0.0.1:8000/sync/historical?start_year=1988&end_year=1990&items_per_year=100"
```

`items_per_year=0` significa cobertura anual sem limite para as proposições consideradas historicamente relevantes.

`batch_size` controla o tamanho dos lotes persistidos e `max_concurrency` controla a quantidade de chamadas remotas simultâneas por lote.

- **Retomar backfill a partir do último checkpoint**

```bash
curl -X POST "http://127.0.0.1:8000/sync/historical?start_year=1988&resume=true"
```

- **Consultar status operacional**

```bash
curl http://127.0.0.1:8000/sync/status
```

- **Consultar issues de sincronização**

```bash
curl "http://127.0.0.1:8000/sync/issues?status=open&severity=error"
```

- **Consultar último checkpoint histórico**

```bash
curl http://127.0.0.1:8000/sync/historical/checkpoint
```

- **Consultar cobertura consolidada do backfill histórico**

```bash
curl http://127.0.0.1:8000/sync/historical/coverage
```
