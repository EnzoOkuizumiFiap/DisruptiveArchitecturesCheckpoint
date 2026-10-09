"""
Pipeline de Ingestão e Processamento da Base de Conhecimento (Clean Code & DRY)
Disruptive Architectures: IA e IoT

Responsabilidades:
1. Extração semântica de markdown com preservação de blocos de código (C++, Arduino, Python).
2. Divisão de documentos em chunks estruturados por seções e cabeçalhos.
3. Mapeamento de URLs canônicas da árvore MkDocs.
4. Sincronização DRY do widget JavaScript para a pasta material/js/.
"""

import os
import re
import json
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

DEFAULT_BASE_URL = "https://enzookuizumifiap.github.io/DisruptiveArchitecturesCheckpoint"
TARGET_CHUNK_WORDS = 320
OVERLAP_WORDS = 50


class DocumentProcessor:
    """Processador de documentos Markdown para geração de base RAG."""

    def __init__(self, material_dir: Path, base_url: str = DEFAULT_BASE_URL):
        self.material_dir = material_dir
        self.base_url = base_url.rstrip("/")

    def extrair_categoria(self, md_path: Path) -> str:
        """Determina a categoria acadêmica com base na estrutura de pastas."""
        rel = md_path.relative_to(self.material_dir).as_posix()
        if "aulas/iot" in rel:
            return "1º Semestre - IoT"
        elif "aulas/genAI" in rel:
            return "2º Semestre - GenAI"
        elif "aulas/IA" in rel:
            return "2º Semestre - IA & Machine Learning"
        elif "aulas/checkpoint" in rel or "avaliacao" in rel:
            return "Checkpoints e Avaliações"
        elif "agenda" in rel:
            return "Agenda e Cronograma"
        elif rel == "index.md":
            return "Apresentação da Disciplina"
        return "Material Geral"

    def path_para_url(self, md_path: Path) -> str:
        """Converte o path do arquivo markdown na URL canônica do MkDocs."""
        rel = md_path.relative_to(self.material_dir)
        partes = list(rel.parts)
        if partes[-1] == "index.md":
            partes = partes[:-1]
        else:
            partes[-1] = partes[-1].removesuffix(".md")

        caminho = "/".join(partes)
        return f"{self.base_url}/{caminho}/" if caminho else f"{self.base_url}/"

    def extrair_titulo(self, texto: str, md_path: Path) -> str:
        """Extrai o título principal do documento ou usa o nome do arquivo."""
        match = re.search(r"^#\s+(.+)$", texto, flags=re.MULTILINE)
        if match:
            return match.group(1).strip()
        if md_path.stem == "index":
            return md_path.parent.name.replace("-", " ").capitalize()
        return md_path.stem.replace("-", " ").capitalize()

    def limpar_markdown(self, texto: str) -> str:
        """Normaliza markdown preservando intactos os blocos de código."""
        texto = re.sub(r"^---.*?---\s*", "", texto, flags=re.DOTALL)
        texto = re.sub(r"!\[(.*?)\]\(.*?\)", r"[Imagem: \1]", texto)
        texto = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", texto)
        texto = re.sub(r"<[^>]+>", "", texto)
        texto = re.sub(r"\n{3,}", "\n\n", texto)
        return texto.strip()

    def chunkar_documento(
        self,
        texto: str,
        titulo_doc: str,
        doc_url: str,
        categoria: str,
        rel_path: str
    ) -> List[Dict[str, Any]]:
        """Divide o documento preservando cabeçalhos e blocos de código."""
        secoes_raw = re.split(r"(^#{2,3}\s+.+$)", texto, flags=re.MULTILINE)
        secoes = []
        subtitulo_atual = titulo_doc
        buffer_texto = []

        for parte in secoes_raw:
            parte_limpa = parte.strip()
            if not parte_limpa:
                continue
            if parte_limpa.startswith("## ") or parte_limpa.startswith("### "):
                if buffer_texto:
                    secoes.append((subtitulo_atual, "\n\n".join(buffer_texto)))
                    buffer_texto = []
                subtitulo_atual = re.sub(r"^#{2,3}\s+", "", parte_limpa).strip()
            else:
                buffer_texto.append(parte_limpa)

        if buffer_texto:
            secoes.append((subtitulo_atual, "\n\n".join(buffer_texto)))

        if not secoes:
            secoes = [(titulo_doc, texto)]

        chunks = []
        idx = 0
        for subtitulo, corpo in secoes:
            palavras = corpo.split()
            if not palavras:
                continue

            if len(palavras) <= TARGET_CHUNK_WORDS:
                if len(corpo.strip()) > 25:
                    chunks.append(self._criar_chunk_dict(
                        idx=idx,
                        rel_path=rel_path,
                        titulo_doc=titulo_doc,
                        subtitulo=subtitulo,
                        categoria=categoria,
                        doc_url=doc_url,
                        texto=corpo.strip(),
                        words_count=len(palavras)
                    ))
                    idx += 1
            else:
                inicio = 0
                while inicio < len(palavras):
                    fim = min(inicio + TARGET_CHUNK_WORDS, len(palavras))
                    trecho = " ".join(palavras[inicio:fim]).strip()
                    if len(trecho) > 40:
                        chunks.append(self._criar_chunk_dict(
                            idx=idx,
                            rel_path=rel_path,
                            titulo_doc=titulo_doc,
                            subtitulo=f"{subtitulo} (continuação)" if inicio > 0 else subtitulo,
                            categoria=categoria,
                            doc_url=doc_url,
                            texto=trecho,
                            words_count=len(trecho.split())
                        ))
                        idx += 1
                    if fim == len(palavras):
                        break
                    inicio = fim - OVERLAP_WORDS

        return chunks

    def _criar_chunk_dict(
        self,
        idx: int,
        rel_path: str,
        titulo_doc: str,
        subtitulo: str,
        categoria: str,
        doc_url: str,
        texto: str,
        words_count: int
    ) -> Dict[str, Any]:
        titulo_completo = f"{titulo_doc} - {subtitulo}" if subtitulo != titulo_doc else titulo_doc
        return {
            "id": f"{rel_path}::chunk_{idx}",
            "title": titulo_completo,
            "section": subtitulo,
            "document_title": titulo_doc,
            "category": categoria,
            "url": doc_url,
            "content": f"# {titulo_doc}\n## {subtitulo}\n\n{texto}",
            "word_count": words_count,
        }

    def processar_tudo(self) -> List[Dict[str, Any]]:
        """Varre e processa todos os arquivos .md da pasta material."""
        arquivos = sorted(self.material_dir.rglob("*.md"))
        print(f"[*] Processando {len(arquivos)} arquivos markdown em {self.material_dir}...")

        todos_chunks = []
        for path in arquivos:
            try:
                texto_raw = path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"[!] Falha ao ler {path}: {e}")
                continue

            if not texto_raw.strip():
                continue

            rel_path = path.relative_to(self.material_dir).as_posix()
            categoria = self.extrair_categoria(path)
            url = self.path_para_url(path)
            titulo = self.extrair_titulo(texto_raw, path)
            texto_limpo = self.limpar_markdown(texto_raw)

            chunks_doc = self.chunkar_documento(
                texto=texto_limpo,
                titulo_doc=titulo,
                doc_url=url,
                categoria=categoria,
                rel_path=rel_path
            )
            todos_chunks.extend(chunks_doc)

        print(f"[+] Total de chunks gerados com sucesso: {len(todos_chunks)}")
        return todos_chunks


def sincronizar_widget_mkdocs(root_dir: Path):
    """DRY: Sincroniza o widget.js (Single Source of Truth) para material/js/chat-widget.js e docs/js/chat-widget.js."""
    origem = root_dir / "backend" / "app" / "static" / "widget.js"
    destino = root_dir / "material" / "js" / "chat-widget.js"
    if origem.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(origem), str(destino))
        print(f"[DRY] Widget sincronizado de {origem.name} -> {destino.as_posix()}")

        destino_docs = root_dir / "docs" / "js" / "chat-widget.js"
        if destino_docs.parent.exists():
            shutil.copy2(str(origem), str(destino_docs))
            print(f"[DRY] Widget sincronizado de {origem.name} -> {destino_docs.as_posix()}")


def main():
    parser = argparse.ArgumentParser(description="Ingestor e Processador da Base de Conhecimento RAG")
    parser.add_argument("--material-dir", default="material", help="Diretório da documentação")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL base da documentação")
    parser.add_argument("--output-json", default="backend/data/knowledge_base.json", help="Arquivo JSON de saída")
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent.parent.parent
    mat_path = (root_dir / args.material_dir).resolve()
    out_json = (root_dir / args.output_json).resolve()

    processor = DocumentProcessor(material_dir=mat_path, base_url=args.base_url)
    chunks = processor.processar_tudo()

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[+] Base salva em: {out_json}")

    # Sincroniza widget para o MkDocs (DRY)
    sincronizar_widget_mkdocs(root_dir)


if __name__ == "__main__":
    main()
