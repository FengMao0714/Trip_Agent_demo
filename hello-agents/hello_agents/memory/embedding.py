"""Unified embedding provider with local and fallback backends."""

from typing import List, Optional, Union
import os
import threading

import numpy as np


class EmbeddingModel:
    """Minimal embedding interface."""

    def encode(self, texts: Union[str, List[str]]):
        raise NotImplementedError

    @property
    def dimension(self) -> int:
        raise NotImplementedError


class LocalTransformerEmbedding(EmbeddingModel):
    """Local embedding backend using sentence-transformers first."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._backend = None
        self._st_model = None
        self._hf_tokenizer = None
        self._hf_model = None
        self._dimension = None
        self._load_backend()

    def _load_backend(self):
        try:
            from sentence_transformers import SentenceTransformer

            self._st_model = SentenceTransformer(self.model_name)
            test_vec = self._st_model.encode("test_text")
            self._dimension = len(test_vec)
            self._backend = "st"
            return
        except Exception:
            self._st_model = None

        try:
            from transformers import AutoModel, AutoTokenizer
            import torch

            self._hf_tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._hf_model = AutoModel.from_pretrained(self.model_name)
            with torch.no_grad():
                inputs = self._hf_tokenizer(
                    "test_text",
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                )
                outputs = self._hf_model(**inputs)
                test_embedding = outputs.last_hidden_state.mean(dim=1)
                self._dimension = int(test_embedding.shape[1])
            self._backend = "hf"
            return
        except Exception:
            self._hf_tokenizer = None
            self._hf_model = None

        raise ImportError(
            "No local embedding backend is available. "
            "Install sentence-transformers or transformers+torch."
        )

    def encode(self, texts: Union[str, List[str]]):
        if isinstance(texts, str):
            inputs = [texts]
            single = True
        else:
            inputs = list(texts)
            single = False

        if self._backend == "st":
            vecs = self._st_model.encode(inputs)
            if hasattr(vecs, "tolist"):
                vecs = [v for v in vecs]
        else:
            import torch

            tokenized = self._hf_tokenizer(
                inputs,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512,
            )
            with torch.no_grad():
                outputs = self._hf_model(**tokenized)
                embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
            vecs = [v for v in embeddings]

        if single:
            return vecs[0]
        return vecs

    @property
    def dimension(self) -> int:
        return int(self._dimension or 0)


class TFIDFEmbedding(EmbeddingModel):
    """Offline-safe fallback with a fixed-size hashing vectorizer."""

    def __init__(self, max_features: int = 384):
        self.max_features = max_features
        self._dimension = max_features
        self._vectorizer = None
        self._init_vectorizer()

    def _init_vectorizer(self):
        try:
            from sklearn.feature_extraction.text import HashingVectorizer

            self._vectorizer = HashingVectorizer(
                n_features=self.max_features,
                alternate_sign=False,
                norm="l2",
                lowercase=True,
            )
        except ImportError as exc:
            raise ImportError(
                "scikit-learn is required for the tfidf fallback backend."
            ) from exc

    def fit(self, texts: List[str]):
        return self

    def encode(self, texts: Union[str, List[str]]):
        if isinstance(texts, str):
            texts = [texts]
            single = True
        else:
            single = False

        matrix = self._vectorizer.transform(texts)
        embeddings = matrix.toarray()
        if single:
            return embeddings[0]
        return [row for row in embeddings]

    @property
    def dimension(self) -> int:
        return self._dimension


class DashScopeEmbedding(EmbeddingModel):
    """DashScope embedding backend."""

    def __init__(
        self,
        model_name: str = "text-embedding-v3",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self._dimension = None
        if not self.base_url:
            self._init_client()
        test = self.encode("health_check")
        self._dimension = len(test)

    def _init_client(self):
        try:
            import dashscope  # noqa: F401

            if self.api_key:
                os.environ["DASHSCOPE_API_KEY"] = self.api_key
        except ImportError as exc:
            raise ImportError("dashscope is required for DashScope embeddings.") from exc

    def encode(self, texts: Union[str, List[str]]):
        if isinstance(texts, str):
            inputs = [texts]
            single = True
        else:
            inputs = list(texts)
            single = False

        if self.base_url:
            import requests

            url = self.base_url.rstrip("/") + "/embeddings"
            headers = {
                "Authorization": f"Bearer {self.api_key}" if self.api_key else "",
                "Content-Type": "application/json",
            }
            payload = {"model": self.model_name, "input": inputs}
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code >= 400:
                raise RuntimeError(
                    f"Embedding REST request failed: {resp.status_code} {resp.text}"
                )
            data = resp.json()
            items = data.get("data") or []
            vecs = [np.array(item.get("embedding")) for item in items]
            if single:
                return vecs[0]
            return vecs

        from dashscope import TextEmbedding

        rsp = TextEmbedding.call(model=self.model_name, input=inputs)
        if isinstance(rsp, dict):
            embeddings_obj = (rsp.get("output") or {}).get("embeddings")
        else:
            embeddings_obj = getattr(getattr(rsp, "output", None), "embeddings", None)
        if not embeddings_obj:
            raise RuntimeError("DashScope returned an empty embedding payload.")
        vecs = [np.array(item.get("embedding") or item.get("vector")) for item in embeddings_obj]
        if single:
            return vecs[0]
        return vecs

    @property
    def dimension(self) -> int:
        return int(self._dimension or 0)


def create_embedding_model(model_type: str = "local", **kwargs) -> EmbeddingModel:
    """Create an embedding backend."""

    if model_type in ("local", "sentence_transformer", "huggingface"):
        model_name = kwargs.get("model_name") or "sentence-transformers/all-MiniLM-L6-v2"
        return LocalTransformerEmbedding(model_name=model_name)
    if model_type == "dashscope":
        model_name = kwargs.get("model_name") or "text-embedding-v3"
        return DashScopeEmbedding(
            model_name=model_name,
            api_key=kwargs.get("api_key"),
            base_url=kwargs.get("base_url"),
        )
    if model_type == "tfidf":
        max_features = kwargs.get("max_features")
        if max_features is None:
            try:
                max_features = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
            except Exception:
                max_features = 384
        return TFIDFEmbedding(max_features=max_features)
    raise ValueError(f"Unsupported embedding model type: {model_type}")


def create_embedding_model_with_fallback(
    preferred_type: str = "dashscope",
    **kwargs,
) -> EmbeddingModel:
    """Create an embedder with fallbacks."""

    if preferred_type in ("sentence_transformer", "huggingface"):
        preferred_type = "local"

    fallback_order = ["dashscope", "local", "tfidf"]
    if preferred_type in fallback_order:
        fallback_order.remove(preferred_type)
        fallback_order.insert(0, preferred_type)

    for model_type in fallback_order:
        try:
            return create_embedding_model(model_type, **kwargs)
        except Exception as exc:
            print(
                f"\n[debug] embedding backend {model_type} failed to load: {exc}"
            )
            continue

    raise RuntimeError(
        "All embedding backends are unavailable. Check dependencies and configuration."
    )


_lock = threading.RLock()
_embedder: Optional[EmbeddingModel] = None


def _build_embedder() -> EmbeddingModel:
    preferred = os.getenv("EMBED_MODEL_TYPE", "dashscope").strip()
    default_model = (
        "text-embedding-v3"
        if preferred == "dashscope"
        else "sentence-transformers/all-MiniLM-L6-v2"
    )
    model_name = os.getenv("EMBED_MODEL_NAME", default_model).strip()
    kwargs = {}
    if model_name:
        kwargs["model_name"] = model_name

    api_key = os.getenv("EMBED_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key

    base_url = os.getenv("EMBED_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url

    try:
        kwargs["max_features"] = int(os.getenv("QDRANT_VECTOR_SIZE", "384"))
    except Exception:
        kwargs["max_features"] = 384

    return create_embedding_model_with_fallback(preferred_type=preferred, **kwargs)


def get_text_embedder() -> EmbeddingModel:
    """Get the shared embedding instance."""

    global _embedder
    if _embedder is not None:
        return _embedder
    with _lock:
        if _embedder is None:
            _embedder = _build_embedder()
        return _embedder


def get_dimension(default: int = 384) -> int:
    """Return the active embedding dimension."""

    try:
        return int(getattr(get_text_embedder(), "dimension", default))
    except Exception:
        return int(default)


def refresh_embedder() -> EmbeddingModel:
    """Force rebuilding the shared embedding instance."""

    global _embedder
    with _lock:
        _embedder = _build_embedder()
        return _embedder
