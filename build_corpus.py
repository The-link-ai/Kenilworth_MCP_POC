
"""build_corpus.py

Usage:
    python build_corpus.py

Requirements (install first):
    pip install beautifulsoup4 sentence_splitter requests tqdm pyyaml

Description:
    * Downloads the 10 article URLs listed below (feel free to add more).
    * Cleans HTML (removes nav, footer, scripts, ads).
    * Saves raw markdown, JSONL chunks (≈250 tokens, 50‑token overlap) and metadata.
    * Updates manifest.json so any MCP client can discover the documents.

After running, you'll have:
    mcp-corpus/
        manifest.json
        config/aliases.yaml  (copied in)
        documents/<uuid>/
            article.md
            chunks.jsonl
            metadata.jsonl

You can then push the entire mcp-corpus folder to a GitHub repository
and serve it via GitHub Pages (see README.md).
"""
import uuid, pathlib, hashlib, json, re, requests, yaml, datetime
from bs4 import BeautifulSoup
from sentence_splitter import split_text_into_sentences
from tqdm import tqdm

ARTICLE_URLS = [
    "https://www.constructionspecifier.com/aluminum-framed-fenestration-a-guide-to-specifying-paints-and-coatings/3/",
    "https://www.constructionspecifier.com/hydrophobic-coatings-unlock-protection-against-water-intrusion/",
    "https://www.constructionspecifier.com/customize-acoustic-ceilings-with-specialty-coatings/",
    "https://www.constructionspecifier.com/specifying-antimicrobial-coatings-for-architectural-aluminum/",
    "https://www.constructionspecifier.com/quick-cure-coatings-with-pmma-puma-technology/",
    "https://www.constructionspecifier.com/bright-ideas-long-lasting-color-performance-for-field-applied-coatings/",
    "https://www.constructionspecifier.com/corrosion-resistance-and-environmental-considerations-for-architectural-metal-coatings/",
    "https://www.constructionspecifier.com/transformative-urban-planning-with-roof-coatings/",
    "https://www.constructionspecifier.com/using-coatings-exterior-restoration-projects/",
    "https://www.constructionspecifier.com/selecting-durable-high-performance-paints-coatings/",
]

CORPUS_ROOT = pathlib.Path("mcp-corpus")
DOCS_DIR    = CORPUS_ROOT / "documents"
CONFIG_DIR  = CORPUS_ROOT / "config"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# copy aliases.yaml from template if exists
template_aliases = pathlib.Path(__file__).parent / "config" / "aliases.yaml"
if template_aliases.exists():
    import shutil
    shutil.copy(template_aliases, CONFIG_DIR / "aliases.yaml")

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    # collapse multiple spaces
    text = re.sub(r"\s{2,}", " ", text)
    return text

def chunk_text(text, window=250, overlap=50):
    # naive whitespace tokenization
    tokens = text.split()
    i = 0
    while i < len(tokens):
        yield " ".join(tokens[i:i+window])
        i += window - overlap

manifest = []

for url in tqdm(ARTICLE_URLS, desc="Processing"):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    raw_text = clean_html(resp.text)
    if len(raw_text) < 100:
        print("⚠️  Skipping (too short):", url)
        continue

    # metadata guess
    title = raw_text.split(".")[0][:120]
    author = "Unknown"
    pub_date = ""

    doc_id = str(uuid.uuid4())
    dpath = DOCS_DIR / doc_id
    dpath.mkdir()

    # write markdown
    md_path = dpath / "article.md"
    md_path.write_text(f"# {title}\n\n{raw_text}\n\n*(Source: {url})*", encoding="utf-8")

    chunks = []
    metas  = []
    for idx, chunk in enumerate(chunk_text(raw_text)):
        chk_id = hashlib.sha256(f"{doc_id}-{idx}".encode()).hexdigest()[:16]
        chunks.append({"chunk_id": chk_id, "text": chunk})
        metas.append({
            "chunk_id": chk_id,
            "title": title,
            "author": author,
            "pub_date": pub_date,
            "page_no": None,
            "tags": [],
            "numeric": {},
            "source_url": url,
            "masterformat": ""
        })

    with (dpath / "chunks.jsonl").open("w", encoding="utf-8") as f:
        for row in chunks:
            json.dump(row, f, ensure_ascii=False)
            f.write("\n")
    with (dpath / "metadata.jsonl").open("w", encoding="utf-8") as f:
        for row in metas:
            json.dump(row, f, ensure_ascii=False)
            f.write("\n")

    manifest.append({
        "doc_uuid": doc_id,
        "title": title,
        "source": url,
        "path": f"documents/{doc_id}/chunks.jsonl"
    })

(CORPUS_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print("✅  Built corpus with", len(manifest), "documents. Saved to", CORPUS_ROOT.resolve())
