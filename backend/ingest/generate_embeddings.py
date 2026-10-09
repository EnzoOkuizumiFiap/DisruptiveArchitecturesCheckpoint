"""
Gerador de Embeddings com Google GenAI (gemini-embedding-2)
Disruptive Architectures: IA e IoT — Checkpoint 5

Lê backend/data/knowledge_base.json e gera a matriz normalizada backend/data/embeddings.npy
para alimentar o motor de similaridade de cosseno do VectorStore.
"""

import os
import sys
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))
load_dotenv(backend_dir / ".env")

from google import genai
from app.core.config import settings

KNOWLEDGE_PATH = backend_dir / "data" / "knowledge_base.json"
OUTPUT_NPY = backend_dir / "data" / "embeddings.npy"


def embed_text(client: genai.Client, text: str, max_retries: int = 4) -> list[float]:
    """Gera embedding com retry exponencial para tolerância a rate-limits."""
    clean_text = text[:8000].strip()
    if not clean_text:
        clean_text = "vazio"

    for attempt in range(1, max_retries + 1):
        try:
            res = client.models.embed_content(
                model=settings.GEMINI_EMBEDDING_MODEL,
                contents=clean_text,
            )
            if res.embeddings:
                return res.embeddings[0].values
        except Exception as err:
            if attempt == max_retries:
                print(f"[!] Erro fatal ao embeddar ({err})")
                raise
            sleep_time = attempt * 1.5
            time.sleep(sleep_time)
    raise RuntimeError("Falha após todos os retries.")


def main():
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("[ERRO] GEMINI_API_KEY não configurada!")
        sys.exit(1)

    client = genai.Client(api_key=api_key)

    if not KNOWLEDGE_PATH.exists():
        print(f"[ERRO] {KNOWLEDGE_PATH} não encontrado!")
        sys.exit(1)

    chunks = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8-sig"))
    total = len(chunks)
    print(f"[*] Iniciando geração de embeddings para {total} chunks usando '{settings.GEMINI_EMBEDDING_MODEL}'...")

    embeddings_dict = {}
    start_time = time.time()

    def process_item(item_idx: int, chunk: dict):
        text_to_embed = f"{chunk.get('title', '')}\n\n{chunk.get('content', '')}"
        vec = embed_text(client, text_to_embed)
        return item_idx, vec

    # Processamento concorrente controlado
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_item, idx, chunk): idx
            for idx, chunk in enumerate(chunks)
        }

        concluidos = 0
        for future in as_completed(futures):
            idx, vec = future.result()
            embeddings_dict[idx] = vec
            concluidos += 1
            if concluidos % 100 == 0 or concluidos == total:
                elapsed = time.time() - start_time
                velocidade = concluidos / max(elapsed, 0.1)
                print(f"[{concluidos}/{total}] chunks embeddados ({velocidade:.1f} chunks/s)...")

    # Ordena pelo índice para garantir correspondência 1:1 com knowledge_base.json
    matrix = np.array([embeddings_dict[i] for i in range(total)], dtype=np.float32)
    print(f"[+] Matriz gerada com sucesso: shape={matrix.shape}, dtype={matrix.dtype}")

    OUTPUT_NPY.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(OUTPUT_NPY), matrix)
    print(f"[OK] Arquivo salvo em: {OUTPUT_NPY} ({OUTPUT_NPY.stat().st_size / (1024*1024):.2f} MB)")


if __name__ == "__main__":
    main()
