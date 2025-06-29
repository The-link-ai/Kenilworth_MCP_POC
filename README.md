
# MCP Corpus Template (Construction Coatings Demo)

This repository is a **starter kit** for hosting a public, Model‑Context‑Protocol‑compatible
corpus of construction‑coatings articles on **GitHub Pages**.

## How it works

1. **Run** `python build_corpus.py`  
   → creates `mcp-corpus/` containing scraped article text, chunks & metadata.  
2. **Commit & push** everything to the **`gh-pages`** branch (or let CI do it).  
   GitHub will serve `_site` → `https://<user>.github.io/<repo>/mcp-corpus/…`.
3. Any MCP client can then query:

```
GET https://<user>.github.io/<repo>/mcp-corpus/manifest.json
```

to discover document paths, pull `chunks.jsonl`, and build its own embeddings.

## Local setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt    # or pip install -r <below>
python build_corpus.py
```

**Requirements** *(put these in your requirements.txt)*:

```
beautifulsoup4
sentence_splitter
requests
tqdm
pyyaml
```

## GitHub Pages deployment

A ready‑made GitHub Actions workflow is included in `.github/workflows/deploy.yml`.
On every push to `main`, it will:

1. Run `build_corpus.py`
2. Commit the generated `mcp-corpus/` to the `gh-pages` branch
3. Publish via GitHub Pages.

Once the run completes, your corpus is live at:

```
https://<user>.github.io/<repo>/mcp-corpus/manifest.json
```

## Prompt template

See **prompt_templates/general_prompt_template.md** for an example system
prompt that retrieves relevant chunks via MCP, injects them into ChatGPT, and
cites the source.

---

*Model Context Protocol docs:*  https://modelcontextprotocol.io/introduction
