# ai-utils cheat sheet

This project already depends on `ai-utils[eval]`. Everything below is available when needed: add the extra,
copy the snippet. The full runnable tour of every module is the
[quickstart notebook](https://github.com/H3NR1QU3M4LT4/ai-utils/blob/main/notebooks/quickstart.ipynb).

Add extras by editing the dependency in `pyproject.toml`, e.g. `"ai-utils[eval,search,pdf,office,ocr,blob]"`,
then `uv sync`.

| I need to... | Use | Extra |
|---|---|---|
| Call an LLM with structured output, retries, concurrency limit | `ai_utils.llm.LLMClient` | — |
| Embed text | `ai_utils.llm.EmbeddingClient` | — |
| Log/trace to App Insights | `ai_utils.core.telemetry.setup_logging`, `setup_tracing`, `log_operation` | — |
| Turn a file (txt, html, docx, pptx, xlsx, pdf, image) into Markdown | `ai_utils.preprocessing.load_document` | `pdf`, `office`, `ocr` |
| OCR scans and images | `ai_utils.preprocessing.ocr.analyze_document` | `ocr` |
| Read/write Blob Storage | `ai_utils.storage` | `blob` |
| Clean HTML/Markdown/PDF text | `ai_utils.rag.cleaning` | — (`pdf` for PDFs) |
| Chunk text | `ai_utils.rag.chunking` | — |
| Index and search Azure AI Search | `ai_utils.rag.search_client` | `search` |
| Ingest files and answer with citations (RAG) | `ai_utils.rag.pipeline` | `search` |
| Evaluate answers, LLM-as-a-judge, log scores | `ai_utils.evaluation` + `azure.ai.evaluation` | `eval` |

Auth everywhere: `ENVIRONMENT=local` uses keys/connection strings from `.env`; anything else uses Entra ID.
Environment variables per service are listed in the ai-utils `.env.example`.

## LLM

```python
from pydantic import BaseModel

from ai_utils.core.telemetry import setup_logging, setup_tracing
from ai_utils.llm import EmbeddingClient, LLMClient, TextResponse

logger, tracer = setup_logging("my-service"), setup_tracing("my-service")
llm = LLMClient(logger=logger, tracer=tracer, max_concurrency=5)  # create once, reuse


class Invoice(BaseModel):
    vendor: str
    total_eur: float


answer = await llm.complete("What is RAG?", TextResponse, system_message="Be brief.")
invoice = await llm.complete(f"Extract the invoice:\n{text}", Invoice)
answers = await llm.complete_batch(["q1", "q2"], TextResponse)  # concurrent, order kept
caption = await llm.complete("Describe this", TextResponse, images=[png_bytes])
vectors = await EmbeddingClient(logger=logger).embed_batch(["a", "b"])
```

## Files to text (`pdf`, `office`, `ocr`)

```python
from ai_utils.preprocessing import load_document
from ai_utils.preprocessing.ocr import get_document_intelligence_client

document = await load_document("manual.docx")  # or bytes + filename="manual.docx"
print(document.text, document.format, document.used_ocr)

async with get_document_intelligence_client() as ocr:  # images and scanned PDFs need OCR
    scanned = await load_document(scan_bytes, filename="scan.pdf", ocr_client=ocr, logger=logger)
```

## Blob Storage (`blob`)

```python
from ai_utils.storage import download_blob, get_blob_service_client, list_blob_names, upload_blob

async with get_blob_service_client() as blobs:
    names = await list_blob_names(blobs, "raw", prefix="manuals/")
    data = await download_blob(blobs, "raw", names[0])
    await upload_blob(blobs, "processed", "manual.md", "# text")
```

## Cleaning and chunking

```python
from ai_utils.rag.chunking import chunk_markdown_by_headings, chunk_sentence_based
from ai_utils.rag.cleaning import clean_html, clean_markdown

chunks = chunk_markdown_by_headings(clean_markdown(document.text), max_chunk_size=2048)
for chunk in chunks:
    print(chunk.heading_path, chunk.text[:80])
pieces = chunk_sentence_based(clean_html(html), max_chunk_size=512)
```

## Search and RAG (`search`)

```python
from ai_utils.rag.pipeline import answer_with_context, ingest_files
from ai_utils.rag.search_client import create_default_index, get_search_client, hybrid_search

await create_default_index("manuals", vector_dimensions=3072)  # text-embedding-3-large
embedder = EmbeddingClient(logger=logger)
async with get_search_client("manuals") as search:
    report = await ingest_files(["a.pdf", ("b.docx", b_bytes)], embedder, search, max_concurrency=4, logger=logger)
    print(report.indexed, report.failed)  # one bad file doesn't stop the batch

    hits = await hybrid_search(search, "lens cleaning", vector=(await embedder.embed_batch(["lens cleaning"]))[0])
    rag = await answer_with_context("How do I clean the lens?", llm, embedder, search, logger=logger)
    print(rag.answer, [(s["source"], s["heading"]) for s in rag.sources])
```

## Evaluation (`eval`)

```python
from azure.ai.evaluation import GroundednessEvaluator, RelevanceEvaluator, evaluate

from ai_utils.evaluation import RubricJudge, log_evaluation, model_config_from_env

config = model_config_from_env()  # AZURE_OPENAI_JUDGE_DEPLOYMENT overrides
result = evaluate(
    data="evals/results/responses.jsonl",  # rows with query, response, context
    evaluators={
        "relevance": RelevanceEvaluator(config),
        "groundedness": GroundednessEvaluator(config),
        "rubric": RubricJudge("Cites the manual section it relies on."),
    },
)
log_evaluation(result, run_name="prompt-v2", logger=logger)  # charted by the ai-utils workbook
```

## Monitoring

Every call above logs one event (`llm.complete`, `search.query`, `preprocessing.load`, `eval.score`, ...).
The ai-utils [`dashboards/`](https://github.com/H3NR1QU3M4LT4/ai-utils/tree/main/dashboards) folder has the
Application Insights workbook over them and the Bicep file to deploy it.

## Concurrency

Create each client once and reuse it: its semaphore (`max_concurrency`) is what bounds parallel calls.
I/O-bound work: `asyncio.gather`. Many files: `ingest_files(max_concurrency=...)`. CPU-bound cleaning/chunking of
many documents: `clean_documents_parallel` / `chunk_documents_parallel` (worker processes).
