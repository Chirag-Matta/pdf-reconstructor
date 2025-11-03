# ordering.py - Improved version with better heuristics
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Tuple, Optional
import os
import re
from rich import print
import json
from scipy.spatial import distance_matrix
import numpy as np

# Optional OpenAI refinement
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[yellow]OpenAI not available - LLM refinement disabled[/yellow]")

MODEL_NAME = "all-MiniLM-L6-v2"

class Orderer:
    def __init__(self, model_name: str = MODEL_NAME):
        print(f"[blue]Loading embedding model: {model_name}[/blue]")
        self.model = SentenceTransformer(model_name)
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
                print("[green]OpenAI client initialized[/green]")
            else:
                print("[yellow]OPENAI_API_KEY not set - LLM refinement disabled[/yellow]")

    def embed_pages(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for page texts."""
        texts_clean = [t if t and t.strip() else "[empty page]" for t in texts]
        embs = self.model.encode(texts_clean, show_progress_bar=False, convert_to_numpy=True)
        return embs

    def similarity_matrix(self, embs: np.ndarray) -> np.ndarray:
        """Compute cosine similarity matrix for embeddings."""
        sim = cosine_similarity(embs)
        return sim

    def detect_page_numbers(self, texts: List[str]) -> dict:
        """
        Try to detect explicit page numbers in text.
        Returns dict mapping detected page numbers to indices.
        """
        page_map = {}
        
        for idx, text in enumerate(texts):
            if not text:
                continue
            
            # Look for patterns like "-5-", "Page 5", "- 5 -", etc.
            patterns = [
            r'Page\s+(\d+)\s+of\s+\d+',  # Page 5 of 20
            r'Page[:\s]+(\d+)',          # Page: 5
            r'-\s*(\d+)\s*-',
            r'^\s*(\d+)\s*$',
        ]
        m

            
        for pattern in patterns:
            matches = re.findall(pattern, text[-800:], re.IGNORECASE | re.MULTILINE)
            if matches:
                try:
                    page_num = int(matches[0])
                    if 1 <= page_num <= len(texts):
                        page_map[page_num] = idx
                        print(f"[cyan]Detected page {page_num} at index {idx}[/cyan]")
                        break
                except ValueError:
                    continue
    
        return page_map

    def detect_document_start(self, texts: List[str]) -> Optional[int]:
        """
        Try to detect which page is likely the document start.
        Looks for title pages, cover pages, or "AGREEMENT" headers.
        """
        start_indicators = [
            r'LOAN\s+AGREEMENT',
            r'AGREEMENT\s+FOR\s+LOAN',
            r'BETWEEN',
            r'DATED',
            r'BY\s+AND\s+BETWEEN',
            r'MEMORANDUM\s+OF\s+UNDERSTANDING',
            r'THIS\s+DEED',
        ]

        
        scores = []
        for idx, text in enumerate(texts):
            if not text or len(text.strip()) < 50:
                scores.append(0)
                continue
            
            score = 0
            text_upper = text.upper()
            
            # Check for title page indicators
            for pattern in start_indicators:
                if re.search(pattern, text_upper):
                    score += 2
            
            # Title pages often have less text
            if len(text.strip()) < 500:
                score += 1
            
            # Check if starts with common title words
            first_100 = text[:100].upper()
            if any(word in first_100 for word in ['LOAN', 'AGREEMENT', 'CONTRACT', 'DATED']):
                score += 3
            
            scores.append(score)
        
        # Return page with highest score if any
        if max(scores) > 0:
            start_idx = int(np.argmax(scores))
            print(f"[cyan]Detected likely start page at index {start_idx}[/cyan]")
            return start_idx
        
        return None

    def greedy_order(self, sim: np.ndarray, page_texts: List[str] = None) -> Tuple[List[int], List[float]]:
        """
        Return order (list of page indices) and transition confidences.
        Now with improved heuristics for document structure.
        """
        n = sim.shape[0]
        if n == 0:
            return [], []

        # Try to detect explicit page numbers
        page_map = {}
        if page_texts:
            page_map = self.detect_page_numbers(page_texts)
        
        # If we found enough sequential page numbers, use them
        if len(page_map) > n * 0.5:  # If we found more than 50% of pages
            print("[green]Using detected page numbers for ordering[/green]")
            sorted_pages = sorted(page_map.items())
            order = [idx for _, idx in sorted_pages]
            
            # Fill in missing pages by similarity
            used = set(order)
            remaining = [i for i in range(n) if i not in used]
            
            # Insert remaining pages at positions with highest similarity
            for rem_idx in remaining:
                best_pos = 0
                best_sim = -1
                for pos in range(len(order) + 1):
                    # Calculate similarity to neighbors
                    sim_score = 0
                    count = 0
                    if pos > 0:
                        sim_score += sim[rem_idx, order[pos-1]]
                        count += 1
                    if pos < len(order):
                        sim_score += sim[rem_idx, order[pos]]
                        count += 1
                    avg_sim = sim_score / count if count > 0 else 0
                    
                    if avg_sim > best_sim:
                        best_sim = avg_sim
                        best_pos = pos
                
                order.insert(best_pos, rem_idx)
            
            # Calculate confidences
            confidences = [1.0]
            for i in range(1, len(order)):
                conf = float(sim[order[i-1], order[i]])
                confidences.append(conf)
            
            return order, confidences

        # Try to detect document start
        start = None
        if page_texts:
            start = self.detect_document_start(page_texts)
        
        # Fall back to similarity-based start detection
        if start is None:
            mean_sim = sim.mean(axis=1)
            start = int(np.argmin(mean_sim))
            print(f"[cyan]Using similarity-based start at index {start}[/cyan]")
        
        order = [start]
        used = {start}
        confidences = []

        # Greedy algorithm: always pick most similar unused page
        # --- Improved greedy logic: nearest-neighbor on distance matrix --- import distance_matrix

# Convert similarity to distance (higher sim → smaller distance)
        dist = 1 - sim

        order = [start]
        used = {start}
        confidences = [1.0]

        # Greedy nearest-neighbor traversal
        for _ in range(n - 1):
            cur = order[-1]
            remaining = [j for j in range(n) if j not in used]
            if not remaining:
                break
            # Pick next page with smallest distance (most similar)
            next_idx = remaining[np.argmin(dist[cur, remaining])]
            order.append(next_idx)
            confidences.append(float(sim[cur, next_idx]))
            used.add(next_idx)

        print(f"[magenta]Computed page order: {order}[/magenta]")
        return order, confidences


    def refine_with_llm(self, summaries: List[str], initial_order: List[int]) -> Optional[List[int]]:
        """
        Call OpenAI to refine the order with better prompting.
        """
        if not self.openai_client:
            print("[yellow]Skipping LLM refinement (no API key)[/yellow]")
            return None

        try:
            # Build a more detailed prompt
            prompt_lines = [
                "You are analyzing a shuffled legal document (Loan Agreement). Below are summaries of each page in their CURRENT (shuffled) order.",
                "",
                "CURRENT ORDER with page summaries:"
            ]
            
            for position, idx in enumerate(initial_order):
                summary = summaries[idx].strip().replace("\n", " ")[:400]
                prompt_lines.append(f"\nPosition {position} (Original Index {idx}):")
                prompt_lines.append(f"  {summary}")
            
            prompt_lines.extend([
                "",
                "TASK: Analyze the content and determine the CORRECT logical order for a Loan Agreement.",
                "Consider:",
                "- Title pages and cover pages should come first",
                "- Definitions and general conditions typically follow",
                "- Articles should be in numerical order",
                "- Schedules come at the end",
                "- Signature pages are last",
                "",
                "Return ONLY a JSON array of the original indices in the correct order.",
                "Format: [index1, index2, index3, ...]",
                "Example: [9, 3, 6, 0, 4, 19, ...]",
                "",
                "Do NOT include any explanation, just the JSON array."
            ])
            
            prompt = "\n".join(prompt_lines)

            print("[blue]Calling OpenAI for refinement...[/blue]")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a document ordering expert specializing in legal documents. You analyze content and return only valid JSON arrays of page indices."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=300
            )
            
            text = response.choices[0].message.content.strip()
            print(f"[blue]LLM raw response: {text[:200]}...[/blue]")
            
            # Clean up response
            text = text.replace("```json", "").replace("```", "").strip()
            
            # Try to find JSON array in response
            import re
            match = re.search(r'\[[\d,\s]+\]', text)
            if match:
                text = match.group(0)
            
            parsed = json.loads(text)
            
            if isinstance(parsed, list) and len(parsed) == len(summaries):
                # Validate all indices are valid and unique
                if (all(isinstance(x, int) and 0 <= x < len(summaries) for x in parsed) and
                    len(set(parsed)) == len(parsed)):
                    print(f"[green]✓ LLM refined order: {parsed[:10]}...[/green]")
                    return parsed
                else:
                    print("[yellow]LLM returned invalid or duplicate indices[/yellow]")
            else:
                print(f"[yellow]LLM returned incorrect format or length: {len(parsed)} vs {len(summaries)}[/yellow]")
                
        except Exception as e:
            print(f"[red]LLM refine failed: {e}[/red]")
        
        return None