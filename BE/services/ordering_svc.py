# ordering_svc.py
import numpy as np
from typing import List, Tuple
import os
from rich import print
import json
import google.generativeai as genai
from sentence_transformers import SentenceTransformer

from .strategies import (
    PageNumberStrategy,
    ConfigurableBusinessLogicStrategy,
    StructuralPatternStrategy,
    SemanticSimilarityStrategy,
    DateSequenceStrategy,
    LLMReasoningStrategy,
    OrderingResult
)

class Orchestrator:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.gemini_model = None
        self.embedding_model = None
        self._setup_gemini()
        self._setup_embedding_model(model_name)

        self.strategies = self._initialize_strategies()

    def _setup_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            try:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
                print("[green]Gemini client initialized[/green]")
            except Exception as e:
                print(f"[red]Gemini initialization failed: {e}[/red]")
        else:
            print("[yellow]GEMINI_API_KEY not set - LLM refinement disabled[/yellow]")

    def _setup_embedding_model(self, model_name: str):
        try:
            self.embedding_model = SentenceTransformer(model_name)
            print(f"[green]Embedding model '{model_name}' loaded[/green]")
        except Exception as e:
            print(f"[red]Failed to load embedding model: {e}[/red]")

    def _initialize_strategies(self) -> List:
        return [
            PageNumberStrategy(),
            ConfigurableBusinessLogicStrategy(),
            StructuralPatternStrategy(),
            SemanticSimilarityStrategy(self.embedding_model),
            DateSequenceStrategy(),
            LLMReasoningStrategy(self.gemini_model),
        ]

    def get_order(self, page_texts: List[str]) -> Tuple[List[int], List[float]]:
        n_pages = len(page_texts)
        if n_pages == 0:
            return [], []

        page_contents = [{ "page_index": i, "content": text } for i, text in enumerate(page_texts)]

        strategy_results: List[OrderingResult] = []
        for strategy in self.strategies:
            if strategy.can_handle(page_contents):
                result = strategy.attempt_ordering(page_contents)
                strategy_results.append(result)
                print(f"[cyan]Strategy '{strategy.name}' completed with confidence {result.confidence:.2f}[/cyan]")
                for reason in result.reasoning:
                    print(f"  - {reason}")

        if not strategy_results:
            print("[red]No strategy could determine an order. Falling back to default.[/red]")
            return list(range(n_pages)), [0.0] * n_pages

        # Select the best result based on confidence
        best_result = max(strategy_results, key=lambda x: x.confidence)
        
        print(f"[bold green]Selected strategy: '{best_result.method}' (Confidence: {best_result.confidence:.2f})[/bold green]")

        final_order = best_result.order

        # Ensure the order is valid
        if len(final_order) != n_pages or len(set(final_order)) != n_pages:
            print("[red]Winning strategy produced an invalid order. Falling back to default.[/red]")
            final_order = list(range(n_pages))

        # Dummy confidences for now
        confidences = [best_result.confidence] * n_pages

        return final_order, confidences
