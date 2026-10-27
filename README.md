# Syncraft

Agentic production simulation. This repo holds two things, deployed together as
the `syncraft` app on digital-lab.tek.sdu.dk:

| Part | Folder | URL |
|---|---|---|
| Project page (static) | `site/` | `/syncraft/` |
| Demo (Streamlit + LangChain agent) | `app/`, `agents/`, `tools/` | `/syncraft/demo/` |

## Run locally

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY
uv run streamlit run app/main.py
# or exactly like on the server:
docker compose up --build     # http://127.0.0.1:8502/syncraft/demo/
```

Locally the simulation state is stored in `app/state/graph.json` and
`products.json`; in the container in `/data` (`SYNCRAFT_STATE_DIR`).
`uv run python main.py` starts a terminal chat with the same agent.

Change the model with `LLM_MODEL` (any `provider:model` LangChain's
`init_chat_model` accepts); only that provider's API key is needed.

## Deploy

Work on `main`; `production` is live within a minute:

```bash
git push origin main:production
```

The API key lives on the server in `/srv/apps/syncraft/.env` (see `.env.example`).
Server-side contract: Digital-Lab-SDU README, "Adding an app".

## Known limitations

- All visitors share one simulation and one conversation: the state files
  and the agent's memory (thread id `"1"`) are global, and "Reset chat"
  resets it for everyone.

## Todo

- License type
- Switch the model endpoint to OpenRouter
