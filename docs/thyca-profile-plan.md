# Thyca profile refresh

Status: implementation complete; preparing review branch

## Goal

Present Nguyễn Hoà / Flowerf19 as an AI engineer working on agents, memory,
retrieval, and context engineering. Use the Thyca notebook aesthetic already
chosen with the user: cream paper, brown ink, serif type, restrained margins
and feather details. Keep profile copy in English.

The user authorizes updating profile information and selecting suitable projects.

## Project selection

| Placement | Project | Evidence and purpose |
| --- | --- | --- |
| Lead project | [Thyca](https://github.com/Flowerf19/thyca-ai) | Personal assistant harness; terminal and local WebUI; skills, tools, MCP; Markdown and lexical memory. |
| Selected work | [Another Brain](https://github.com/Flowerf19/another-brain) | Shared local memory for coding agents, embedded MCP, SQLite and ONNX embeddings. |
| Selected work | [March7](https://github.com/Flowerf19/March7) | Discord Twin-Soul agents and A2A memory consolidation; self-heal remains in development. |
| Selected work | [RAG](https://github.com/Flowerf19/RAG) | PDF retrieval, semantic + BM25 hybrid search, query enhancement and reranking. |
| Selected work | [Agent Skills](https://github.com/Flowerf19/agents-skills) | Reusable planning, implementation, debugging, review and documentation workflows. |

My Health and Finance Agent VN are outside the selected AI portfolio narrative.
Their repositories are not modified.

User revision: ModelsReview and Vietnamese Reranker Benchmark are excluded from
this profile refresh and reserved for other work.

## Content and layout

1. Cover: name, AI engineer role, Hanoi, and a concise personal introduction.
2. Areas of work: agents, memory/retrieval, local inference and engineering craft.
3. Selected projects: five linked notebook entries, led by Thyca.
4. Contact: preserve the existing verified profile contact links.
5. A readable text alternative for accessibility and search.

Descriptions are grounded in each public README. Do not invent employment,
metrics, project maturity, user counts, or features. Replace the existing
hard-coded language percentages with a factual area-of-work section.

## Implementation

- Store editorial project choices in `profile.json`.
- Generate self-hosted SVG assets with a cream surface and responsive mobile
  variants. GitHub owns the surrounding page theme.
- Keep a small public repository metadata cache for reproducible offline output.
- Preserve automatic description refresh for projects using their GitHub About
  text; use curated summaries where README details are more accurate.
- Update `README.template.md`, `scripts/generate_readme.py`, and the existing
  workflow together. Stage generated assets as well as README during refresh.
- Work on `feat/thyca-profile`; prepare a pull request for review.

## Completion checks

- [x] Read the profile repository and public project READMEs.
- [x] Record the plan before editing profile content.
- [x] Create the Thyca visual system and selected project copy.
- [x] Update generator, template and workflow.
- [x] Verify desktop and mobile renderings, links and SVG text bounds.
- [x] Verify offline reproducibility and refresh failure handling.
- [ ] Publish the review branch and PR if GitHub write tools are available.


## Maintenance

Edit `profile.json` for project selection and editorial copy, then run:

```sh
python scripts/generate_readme.py --offline
python -m unittest discover -s scripts -p "test_*.py"
python scripts/generate_readme.py --offline --check
```

Omit `--offline` to refresh public repository metadata. Set `curated: true`
to preserve an editorial summary instead of using the repository About text.
The generated SVGs include separate mobile layouts and text alternatives.
