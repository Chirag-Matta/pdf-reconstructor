# ordering.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple, Dict, Optional
import os
from rich import print

# Optional OpenAI refinement
import openai

MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast; swap for larger if needed

class Orderer:
    def __init__(self, model_name: str = MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def embed_pages(self, texts: List[str]) -> np.ndarray:
        # handle empty pages by mapping to empty string
        texts_clean = [t if t and t.strip() else "[empty page]" for t in texts]
        embs = self.model.encode(texts_clean, show_progress_bar=False, convert_to_numpy=True)
        return embs

    def similarity_matrix(self, embs: np.ndarray) -> np.ndarray:
        sim = cosine_similarity(embs)
        return sim

    def greedy_order(self, sim: np.ndarray) -> Tuple[List[int], List[float]]:
        """Return order (list of page indices) and transition confidences (cosine scores)."""
        n = sim.shape[0]
        if n == 0:
            return [], []

        # choose start as page with lowest mean similarity (likely intro/cover)
        mean_sim = sim.mean(axis=1)
        start = int(np.argmin(mean_sim))
        order = [start]
        used = {start}
        confidences = []

        while len(order) < n:
            cur = order[-1]
            candidates = [(j, sim[cur, j]) for j in range(n) if j not in used]
            if not candidates:
                break
            # pick highest similarity
            next_idx, score = max(candidates, key=lambda x: x[1])
            order.append(next_idx)
            confidences.append(float(score))
            used.add(next_idx)

        # confidences list has length n-1; pad front with 1.0 for first page
        confidences = [1.0] + confidences
        return order, confidences

    def refine_with_llm(self, summaries: List[str], initial_order: List[int]) -> Optional[List[int]]:
        """
        Optional: call OpenAI to refine the order.
        Provide a short prompt with page summaries and the initial order.
        Returns refined order (list of indices) or None if not available.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[yellow]OPENAI_API_KEY not set - skipping LLM refinement[/yellow]")
            return None
        openai.api_key = api_key

        # build short prompt
        prompt_lines = ["You are ordering pages. Each page summary below:"]
        for i, s in enumerate(summaries):
            summary = s.strip().replace("\n", " ")
            prompt_lines.append(f"Page {i}: {summary[:500]}")
        prompt_lines.append(f"\nCurrent best guessed order: {initial_order}")
        prompt_lines.append("Return only a Python-list of page numbers (zero-based indices) for the refined order.")
        prompt = "\n".join(prompt_lines)

        try:
            resp = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=100,
                temperature=0.0,
                n=1,
            )
            text = resp.choices[0].text.strip()
            # attempt to parse a list
            # e.g. text = "[2, 0, 1, 3]"
            parsed = eval(text, {"__builtins__": {}})  # guarded eval
            if isinstance(parsed, list) and len(parsed) == len(summaries):
                return parsed
        except Exception as e:
            print(f"[red]LLM refine failed:[/red] {e}")
        return None
