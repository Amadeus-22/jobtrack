# Résumé dataset

Every résumé variant sent during the search, stored as data next to the
application log. Each `variant` matches the `resume` field in
[`../applications.jsonl`](../applications.jsonl), so each response rate in the
report can be traced back to the exact document that produced it.

## Files

| File | Content |
|---|---|
| `manifest.jsonl` | One record per variant (schema below) |
| `<variant>.pdf` | The document that was actually sent |
| `<variant>.html` | Its source |

## Schema: `manifest.jsonl`

| Field | Type | Description |
|---|---|---|
| `variant` | string | Identifier used in `applications.jsonl` (`resume` field) |
| `target_role` | string | Role the variant was written for |
| `language` | string | BCP 47 tag: `en` or `pt-BR` |
| `created_on` | date | When the variant was produced (`YYYY-MM-DD`) |
| `pdf` / `html` | string | File names in this folder |
| `pdf_sha256` | string | Checksum of the PDF, to detect silent edits |

## Variants

| Variant | Target role | Language |
|---|---|---|
| `ai-engineer` | Software Engineer, AI-Assisted Development | en |
| `algoseek-support` | Algorithmic Support Engineer | en |
| `backend-generic` | Backend Software Engineer | en |
| `backend-python` | Backend Engineer | en |
| `blip-ia-dados` | Especialista em IA — Dados para Agentes (MCP) | pt-BR |
| `cientista-dados` | Cientista de Dados | pt-BR |
| `fullstack-ai` | Fullstack AI Engineer | en |
| `fullstack-php-crm` | Desenvolvedor Full Stack PHP/React — Projeto CRM | pt-BR |
| `ia-agentes` | Engenheiro de IA / Desenvolvedor Python e Go | pt-BR |
| `ml-platform` | ML Platform / Machine Learning Engineer | en |
| `platform-engineer` | Support/Platform Engineer | en |
| `sustentacao-php` | Analista de Sustentação N3 / Desenvolvedor PHP | pt-BR |

`upwork-profile`, used in the log, is the Upwork profile itself and has no file.

## Conventions

- Variants are immutable once used. To change one, add a new variant with a new
  name. Otherwise earlier response rates would describe a document that no longer exists.
- Add a variant by dropping `<variant>.pdf` and `<variant>.html` here and
  appending one line to `manifest.jsonl`.
