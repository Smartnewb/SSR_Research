"""Main pipeline orchestrating all components."""

from typing import Optional, Callable

import numpy as np
from tqdm import tqdm

from .personas.generator import (
    Persona,
    generate_persona_hybrid,
    generate_personas_targeted,
    generate_personas_stratified,
    persona_to_system_prompt,
)
from .survey.executor import (
    get_purchase_opinion,
    get_purchase_opinion_with_retry,
    CostTracker,
)
from .survey.validator import validate_llm_response
from .embeddings.service import get_embedding, get_embeddings_batch, EmbeddingService
from .embeddings.cache import EmbeddingCache
from .ssr.calculator import SSRCalculator
from .ssr.anchors import POSITIVE_ANCHOR, NEGATIVE_ANCHOR
from .reporting.aggregator import (
    SurveyResult,
    AggregatedResults,
    aggregate_results,
)


class SSRPipeline:
    """
    End-to-end pipeline for SSR-based market research.

    Orchestrates persona generation, LLM survey execution,
    embedding calculation, and SSR scoring.
    """

    def __init__(
        self,
        llm_model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        enable_caching: bool = True,
        llm_client: Optional["openai.OpenAI"] = None,
    ):
        """
        Initialize pipeline.

        Args:
            llm_model: Model for text generation
            embedding_model: Model for embeddings
            enable_caching: Whether to cache embeddings
            llm_client: Optional OpenAI client
        """
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.enable_caching = enable_caching
        self._client = llm_client

        self.embedding_service: Optional[EmbeddingService] = None
        self.embedding_cache: Optional[EmbeddingCache] = None
        self.ssr_calculator: Optional[SSRCalculator] = None
        self.cost_tracker = CostTracker()

        self._initialized = False

    @property
    def client(self):
        """Lazy-load OpenAI client."""
        if self._client is None:
            import openai
            self._client = openai.OpenAI()
        return self._client

    def initialize(self) -> None:
        """Initialize pipeline components."""
        if self.enable_caching:
            self.embedding_cache = EmbeddingCache(model=self.embedding_model)
            embedding_fn = lambda text, model=self.embedding_model: self.embedding_cache.get(text, model)
        else:
            self.embedding_service = EmbeddingService(
                model=self.embedding_model,
                client=self.client,
            )
            embedding_fn = lambda text, model=None: self.embedding_service.embed(text)

        def embed_text(text: str) -> np.ndarray:
            return embedding_fn(text)

        self.ssr_calculator = SSRCalculator(
            pos_anchor=POSITIVE_ANCHOR,
            neg_anchor=NEGATIVE_ANCHOR,
            embedding_fn=embed_text,
        )
        self.ssr_calculator.initialize_anchors()

        self._initialized = True

    def _ensure_initialized(self) -> None:
        """Ensure pipeline is initialized."""
        if not self._initialized:
            self.initialize()

    def run_survey(
        self,
        product_description: str,
        sample_size: int = 100,
        target_demographics: Optional[dict] = None,
        use_stratified: bool = True,
        show_progress: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> AggregatedResults:
        """
        Run full survey pipeline.

        Args:
            product_description: Product concept to evaluate
            sample_size: Number of synthetic respondents
            target_demographics: Optional demographic filters
            use_stratified: Whether to use stratified sampling
            show_progress: Whether to display progress bar
            progress_callback: Optional callback for custom progress handling

        Returns:
            Aggregated survey results
        """
        self._ensure_initialized()

        if target_demographics:
            personas = generate_personas_targeted(
                sample_size=sample_size,
                target_demographics=target_demographics,
            )
        elif use_stratified:
            personas = generate_personas_stratified(sample_size=sample_size)
        else:
            personas = [generate_persona_hybrid() for _ in range(sample_size)]

        results = []
        response_texts = []

        persona_iter = tqdm(
            personas,
            desc="Surveying personas",
            disable=not show_progress,
            unit="persona",
        )

        for i, persona in enumerate(persona_iter):
            system_prompt = persona_to_system_prompt(persona)

            response = get_purchase_opinion_with_retry(
                persona_system_prompt=system_prompt,
                product_description=product_description,
                model=self.llm_model,
                client=self.client,
            )

            if response:
                self.cost_tracker.record_call(
                    self.llm_model,
                    response.get("usage", {}),
                    response["cost"],
                )

                result = SurveyResult(
                    persona_id=persona.persona_id,
                    response_text=response["response_text"],
                    ssr_score=0.0,
                    persona_data=persona.to_dict(),
                    tokens_used=response["tokens_used"],
                    cost=response["cost"],
                    latency_ms=response["latency_ms"],
                )
                results.append(result)
                response_texts.append(response["response_text"])

            if progress_callback:
                progress_callback(i + 1, sample_size)

        if response_texts:
            if self.embedding_cache:
                embeddings = np.array([
                    self.embedding_cache.get(text) for text in response_texts
                ])
            else:
                embeddings = get_embeddings_batch(
                    response_texts,
                    model=self.embedding_model,
                    client=self.client,
                )

            scores = self.ssr_calculator.calculate_batch(embeddings)

            for i, result in enumerate(results):
                result.ssr_score = float(scores[i])

        return aggregate_results(results)

    def run_survey_mock(
        self,
        product_description: str,
        sample_size: int = 10,
        mock_responses: Optional[list[str]] = None,
        mock_embedding_fn: Optional[callable] = None,
        show_progress: bool = False,
    ) -> AggregatedResults:
        """
        Run survey with mock data (for testing without API calls).

        Args:
            product_description: Product description
            sample_size: Number of respondents
            mock_responses: Optional list of mock response texts
            mock_embedding_fn: Optional mock embedding function
            show_progress: Whether to display progress bar

        Returns:
            Aggregated results
        """
        if mock_embedding_fn is None:
            def mock_embedding_fn(text: str) -> np.ndarray:
                np.random.seed(hash(text) % (2**32))
                vec = np.random.randn(1536)
                return vec / np.linalg.norm(vec)

        self.ssr_calculator = SSRCalculator(
            pos_anchor=POSITIVE_ANCHOR,
            neg_anchor=NEGATIVE_ANCHOR,
            embedding_fn=mock_embedding_fn,
        )
        self.ssr_calculator.initialize_anchors()
        self._initialized = True

        personas = generate_personas_stratified(sample_size=sample_size)

        if mock_responses is None:
            mock_responses = [
                "I really like this product, it fits my needs perfectly.",
                "This seems overpriced for what it offers.",
                "Interesting concept, but I'm not sure I need it.",
                "This is exactly what I've been looking for!",
                "Not for me, but I can see others liking it.",
            ]

        results = []
        persona_iter = tqdm(
            enumerate(personas),
            total=len(personas),
            desc="Processing personas",
            disable=not show_progress,
            unit="persona",
        )

        for i, persona in persona_iter:
            response_text = mock_responses[i % len(mock_responses)]
            embedding = mock_embedding_fn(response_text)
            score = self.ssr_calculator.calculate_simple(embedding)

            result = SurveyResult(
                persona_id=persona.persona_id,
                response_text=response_text,
                ssr_score=score,
                persona_data=persona.to_dict(),
            )
            results.append(result)

        return aggregate_results(results)

    @property
    def stats(self) -> dict:
        """Get pipeline statistics."""
        stats = {
            "cost_summary": self.cost_tracker.summary(),
            "initialized": self._initialized,
        }

        if self.embedding_cache:
            stats["embedding_cache"] = self.embedding_cache.stats

        return stats

    def reset(self) -> None:
        """Reset pipeline state."""
        self.cost_tracker.reset()
        if self.embedding_cache:
            self.embedding_cache.reset_stats()


from dataclasses import dataclass


@dataclass
class ABTestResults:
    """Results from A/B test comparison."""

    product_a_description: str
    product_b_description: str
    results_a: AggregatedResults
    results_b: AggregatedResults
    sample_size: int
    winner: str
    score_difference: float
    statistical_significance: float

    @property
    def summary(self) -> dict:
        """Get summary of A/B test results."""
        return {
            "product_a": {
                "description": self.product_a_description[:50] + "...",
                "mean_score": self.results_a.mean_score,
                "std_dev": self.results_a.std_dev,
            },
            "product_b": {
                "description": self.product_b_description[:50] + "...",
                "mean_score": self.results_b.mean_score,
                "std_dev": self.results_b.std_dev,
            },
            "winner": self.winner,
            "score_difference": self.score_difference,
            "statistical_significance": self.statistical_significance,
        }


def run_survey(
    product_description: str,
    sample_size: int = 100,
    demographics: Optional[dict] = None,
    llm_model: str = "gpt-4o-mini",
) -> AggregatedResults:
    """
    Convenience function to run a survey.

    Args:
        product_description: Product concept to evaluate
        sample_size: Number of respondents
        demographics: Optional demographic filters
        llm_model: LLM model to use

    Returns:
        Aggregated results
    """
    pipeline = SSRPipeline(llm_model=llm_model)
    return pipeline.run_survey(
        product_description=product_description,
        sample_size=sample_size,
        target_demographics=demographics,
    )


def run_ab_test(
    product_a: str,
    product_b: str,
    sample_size: int = 50,
    demographics: Optional[dict] = None,
    llm_model: str = "gpt-4o-mini",
    show_progress: bool = True,
) -> ABTestResults:
    """
    Run A/B test comparing two product concepts.

    Uses the same set of personas for both products to ensure fair comparison.

    Args:
        product_a: First product description
        product_b: Second product description
        sample_size: Number of respondents per product
        demographics: Optional demographic filters
        llm_model: LLM model to use
        show_progress: Whether to show progress bar

    Returns:
        ABTestResults with comparison data
    """
    pipeline = SSRPipeline(llm_model=llm_model)
    pipeline.initialize()

    if demographics:
        personas = generate_personas_targeted(
            sample_size=sample_size,
            target_demographics=demographics,
        )
    else:
        personas = generate_personas_stratified(sample_size=sample_size)

    results_a_list = []
    results_b_list = []
    response_texts_a = []
    response_texts_b = []

    persona_iter = tqdm(
        personas,
        desc="A/B Testing",
        disable=not show_progress,
        unit="persona",
    )

    for persona in persona_iter:
        system_prompt = persona_to_system_prompt(persona)

        response_a = get_purchase_opinion_with_retry(
            persona_system_prompt=system_prompt,
            product_description=product_a,
            model=llm_model,
            client=pipeline.client,
        )

        response_b = get_purchase_opinion_with_retry(
            persona_system_prompt=system_prompt,
            product_description=product_b,
            model=llm_model,
            client=pipeline.client,
        )

        if response_a:
            pipeline.cost_tracker.record_call(
                llm_model, response_a.get("usage", {}), response_a["cost"]
            )
            results_a_list.append(SurveyResult(
                persona_id=persona.persona_id,
                response_text=response_a["response_text"],
                ssr_score=0.0,
                persona_data=persona.to_dict(),
                tokens_used=response_a["tokens_used"],
                cost=response_a["cost"],
                latency_ms=response_a["latency_ms"],
            ))
            response_texts_a.append(response_a["response_text"])

        if response_b:
            pipeline.cost_tracker.record_call(
                llm_model, response_b.get("usage", {}), response_b["cost"]
            )
            results_b_list.append(SurveyResult(
                persona_id=persona.persona_id,
                response_text=response_b["response_text"],
                ssr_score=0.0,
                persona_data=persona.to_dict(),
                tokens_used=response_b["tokens_used"],
                cost=response_b["cost"],
                latency_ms=response_b["latency_ms"],
            ))
            response_texts_b.append(response_b["response_text"])

    if response_texts_a:
        if pipeline.embedding_cache:
            embeddings_a = np.array([
                pipeline.embedding_cache.get(text) for text in response_texts_a
            ])
        else:
            embeddings_a = get_embeddings_batch(
                response_texts_a,
                model=pipeline.embedding_model,
                client=pipeline.client,
            )
        scores_a = pipeline.ssr_calculator.calculate_batch(embeddings_a)
        for i, result in enumerate(results_a_list):
            result.ssr_score = float(scores_a[i])

    if response_texts_b:
        if pipeline.embedding_cache:
            embeddings_b = np.array([
                pipeline.embedding_cache.get(text) for text in response_texts_b
            ])
        else:
            embeddings_b = get_embeddings_batch(
                response_texts_b,
                model=pipeline.embedding_model,
                client=pipeline.client,
            )
        scores_b = pipeline.ssr_calculator.calculate_batch(embeddings_b)
        for i, result in enumerate(results_b_list):
            result.ssr_score = float(scores_b[i])

    agg_a = aggregate_results(results_a_list)
    agg_b = aggregate_results(results_b_list)

    score_diff = agg_a.mean_score - agg_b.mean_score
    if abs(score_diff) < 0.01:
        winner = "Tie"
    elif score_diff > 0:
        winner = "A"
    else:
        winner = "B"

    pooled_std = np.sqrt((agg_a.std_dev**2 + agg_b.std_dev**2) / 2)
    if pooled_std > 0 and sample_size > 1:
        t_stat = abs(score_diff) / (pooled_std * np.sqrt(2 / sample_size))
        from scipy import stats
        p_value = 2 * (1 - stats.t.cdf(t_stat, df=2*sample_size - 2))
        significance = 1 - p_value
    else:
        significance = 0.0

    return ABTestResults(
        product_a_description=product_a,
        product_b_description=product_b,
        results_a=agg_a,
        results_b=agg_b,
        sample_size=sample_size,
        winner=winner,
        score_difference=abs(score_diff),
        statistical_significance=significance,
    )


def run_ab_test_mock(
    product_a: str,
    product_b: str,
    sample_size: int = 10,
) -> ABTestResults:
    """
    Run A/B test with mock data (for testing without API calls).

    Args:
        product_a: First product description
        product_b: Second product description
        sample_size: Number of respondents per product

    Returns:
        ABTestResults with mock comparison data
    """
    pipeline = SSRPipeline()

    def mock_embedding_fn(text: str) -> np.ndarray:
        np.random.seed(hash(text) % (2**32))
        vec = np.random.randn(1536)
        return vec / np.linalg.norm(vec)

    pipeline.ssr_calculator = SSRCalculator(
        pos_anchor=POSITIVE_ANCHOR,
        neg_anchor=NEGATIVE_ANCHOR,
        embedding_fn=mock_embedding_fn,
    )
    pipeline.ssr_calculator.initialize_anchors()
    pipeline._initialized = True

    personas = generate_personas_stratified(sample_size=sample_size)

    mock_responses_a = [
        "I really like this product, it fits my needs perfectly.",
        "This seems overpriced for what it offers.",
        "Interesting concept, but I'm not sure I need it.",
        "This is exactly what I've been looking for!",
        "Not for me, but I can see others liking it.",
    ]

    mock_responses_b = [
        "This product seems okay but nothing special.",
        "I would consider buying this.",
        "Not really what I'm looking for.",
        "Could be useful for some people.",
        "The price seems fair for what you get.",
    ]

    results_a = []
    results_b = []

    for i, persona in enumerate(personas):
        text_a = mock_responses_a[i % len(mock_responses_a)]
        text_b = mock_responses_b[i % len(mock_responses_b)]

        emb_a = mock_embedding_fn(text_a)
        emb_b = mock_embedding_fn(text_b)

        score_a = pipeline.ssr_calculator.calculate_simple(emb_a)
        score_b = pipeline.ssr_calculator.calculate_simple(emb_b)

        results_a.append(SurveyResult(
            persona_id=persona.persona_id,
            response_text=text_a,
            ssr_score=score_a,
            persona_data=persona.to_dict(),
        ))
        results_b.append(SurveyResult(
            persona_id=persona.persona_id,
            response_text=text_b,
            ssr_score=score_b,
            persona_data=persona.to_dict(),
        ))

    agg_a = aggregate_results(results_a)
    agg_b = aggregate_results(results_b)

    score_diff = agg_a.mean_score - agg_b.mean_score
    if abs(score_diff) < 0.01:
        winner = "Tie"
    elif score_diff > 0:
        winner = "A"
    else:
        winner = "B"

    return ABTestResults(
        product_a_description=product_a,
        product_b_description=product_b,
        results_a=agg_a,
        results_b=agg_b,
        sample_size=sample_size,
        winner=winner,
        score_difference=abs(score_diff),
        statistical_significance=0.0,
    )
