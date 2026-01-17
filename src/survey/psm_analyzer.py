"""
Van Westendorp Price Sensitivity Meter (PSM) Analysis.

Implements the classic PSM methodology for determining optimal pricing:
- Too Cheap: Price perceived as too low (quality concerns)
- Cheap: Price perceived as a bargain
- Expensive: Price perceived as high but acceptable
- Too Expensive: Price perceived as unacceptable

The intersection points determine:
- PMC (Point of Marginal Cheapness): Too Cheap = Expensive
- PME (Point of Marginal Expensiveness): Too Expensive = Cheap
- OPP (Optimal Price Point): Too Cheap = Too Expensive
- IDP (Indifference Price Point): Cheap = Expensive
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np
from numpy.typing import NDArray


@dataclass
class PSMQuestion:
    """A single PSM question configuration."""

    question_type: str  # "too_cheap", "cheap", "expensive", "too_expensive"
    question_text: str
    price_points: list[float]


@dataclass
class PSMResponse:
    """Response from a single persona for PSM analysis."""

    persona_id: str
    too_cheap_price: float
    cheap_price: float
    expensive_price: float
    too_expensive_price: float
    persona_data: Optional[dict] = None


@dataclass
class PSMIntersection:
    """Intersection point in PSM analysis."""

    name: str
    price: float
    description: str


@dataclass
class PSMResult:
    """Complete PSM analysis result."""

    optimal_price_point: float  # OPP
    indifference_price_point: float  # IDP
    point_of_marginal_cheapness: float  # PMC
    point_of_marginal_expensiveness: float  # PME
    acceptable_price_range: tuple[float, float]  # PMC to PME
    sample_size: int
    price_range_tested: tuple[float, float]
    curves: dict  # Cumulative distribution data for each curve


PSM_QUESTIONS = {
    "too_cheap": (
        "At what price would you consider this product to be so cheap "
        "that you would question its quality and not consider buying it?"
    ),
    "cheap": (
        "At what price would you consider this product to be a bargain - "
        "a great buy for the money?"
    ),
    "expensive": (
        "At what price would you consider this product to be getting expensive - "
        "not out of the question, but you would have to give it some thought?"
    ),
    "too_expensive": (
        "At what price would you consider this product to be so expensive "
        "that you would not consider buying it?"
    ),
}


def create_psm_prompt(
    product_description: str,
    question_type: str,
    price_range: tuple[float, float],
) -> str:
    """
    Create a PSM survey prompt for LLM.

    Args:
        product_description: Description of the product
        question_type: One of "too_cheap", "cheap", "expensive", "too_expensive"
        price_range: (min_price, max_price) for context

    Returns:
        Formatted prompt string
    """
    question = PSM_QUESTIONS[question_type]
    min_price, max_price = price_range

    return f"""You are evaluating the following product:

{product_description}

Consider prices in the range of ${min_price:.2f} to ${max_price:.2f}.

{question}

Respond with ONLY a single number representing the price in dollars.
Do not include any explanation, just the number.
Example response: 29.99"""


def parse_price_response(response: str) -> Optional[float]:
    """
    Parse price from LLM response.

    Args:
        response: Raw LLM response

    Returns:
        Parsed price or None if parsing fails
    """
    import re

    cleaned = response.strip().replace("$", "").replace(",", "")

    match = re.search(r"(\d+(?:\.\d{1,2})?)", cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return None
    return None


def validate_psm_response(response: PSMResponse) -> tuple[bool, str]:
    """
    Validate PSM response for logical consistency.

    Valid responses must satisfy:
    too_cheap <= cheap <= expensive <= too_expensive

    Args:
        response: PSM response to validate

    Returns:
        (is_valid, error_message)
    """
    prices = [
        response.too_cheap_price,
        response.cheap_price,
        response.expensive_price,
        response.too_expensive_price,
    ]

    if any(p <= 0 for p in prices):
        return False, "All prices must be positive"

    if not (
        response.too_cheap_price
        <= response.cheap_price
        <= response.expensive_price
        <= response.too_expensive_price
    ):
        return False, (
            "Price order violation: "
            f"too_cheap({response.too_cheap_price}) <= "
            f"cheap({response.cheap_price}) <= "
            f"expensive({response.expensive_price}) <= "
            f"too_expensive({response.too_expensive_price})"
        )

    return True, ""


def _find_intersection(
    x: NDArray[np.float64],
    y1: NDArray[np.float64],
    y2: NDArray[np.float64],
) -> Optional[float]:
    """
    Find intersection point of two curves.

    Args:
        x: X values (prices)
        y1: First curve Y values
        y2: Second curve Y values

    Returns:
        X value of intersection or None
    """
    diff = y1 - y2
    sign_changes = np.where(np.diff(np.sign(diff)))[0]

    if len(sign_changes) == 0:
        return None

    idx = sign_changes[0]
    x1, x2 = x[idx], x[idx + 1]
    y1_1, y1_2 = y1[idx], y1[idx + 1]
    y2_1, y2_2 = y2[idx], y2[idx + 1]

    slope1 = (y1_2 - y1_1) / (x2 - x1) if x2 != x1 else 0
    slope2 = (y2_2 - y2_1) / (x2 - x1) if x2 != x1 else 0

    if slope1 == slope2:
        return x1

    intersection_x = x1 + (y2_1 - y1_1) / (slope1 - slope2)
    return float(intersection_x)


def analyze_psm(
    responses: list[PSMResponse],
    price_points: Optional[list[float]] = None,
    num_points: int = 100,
) -> PSMResult:
    """
    Perform Van Westendorp PSM analysis.

    Computes cumulative distribution curves and finds intersection points
    to determine optimal pricing.

    Args:
        responses: List of PSM responses from personas
        price_points: Optional specific price points to analyze
        num_points: Number of points for curve generation

    Returns:
        PSMResult with optimal pricing insights
    """
    if not responses:
        raise ValueError("No responses provided for PSM analysis")

    too_cheap = np.array([r.too_cheap_price for r in responses])
    cheap = np.array([r.cheap_price for r in responses])
    expensive = np.array([r.expensive_price for r in responses])
    too_expensive = np.array([r.too_expensive_price for r in responses])

    if price_points is None:
        min_price = min(too_cheap.min(), cheap.min())
        max_price = max(expensive.max(), too_expensive.max())
        price_points = np.linspace(min_price * 0.8, max_price * 1.2, num_points)
    else:
        price_points = np.array(price_points)

    def cumulative_above(data: NDArray, prices: NDArray) -> NDArray:
        """% of respondents who gave a price >= each price point."""
        return np.array([np.mean(data >= p) for p in prices])

    def cumulative_below(data: NDArray, prices: NDArray) -> NDArray:
        """% of respondents who gave a price <= each price point."""
        return np.array([np.mean(data <= p) for p in prices])

    too_cheap_curve = cumulative_below(too_cheap, price_points)
    cheap_curve = cumulative_below(cheap, price_points)
    expensive_curve = cumulative_above(expensive, price_points)
    too_expensive_curve = cumulative_above(too_expensive, price_points)

    not_too_cheap = 1 - too_cheap_curve
    not_too_expensive = 1 - too_expensive_curve

    opp = _find_intersection(price_points, not_too_cheap, not_too_expensive)
    idp = _find_intersection(price_points, cheap_curve, expensive_curve)
    pmc = _find_intersection(price_points, not_too_cheap, expensive_curve)
    pme = _find_intersection(price_points, cheap_curve, not_too_expensive)

    opp = opp if opp else float(np.median(cheap))
    idp = idp if idp else float(np.median(expensive))
    pmc = pmc if pmc else float(np.percentile(too_cheap, 75))
    pme = pme if pme else float(np.percentile(too_expensive, 25))

    return PSMResult(
        optimal_price_point=opp,
        indifference_price_point=idp,
        point_of_marginal_cheapness=pmc,
        point_of_marginal_expensiveness=pme,
        acceptable_price_range=(pmc, pme),
        sample_size=len(responses),
        price_range_tested=(float(price_points.min()), float(price_points.max())),
        curves={
            "prices": price_points.tolist(),
            "too_cheap": too_cheap_curve.tolist(),
            "cheap": cheap_curve.tolist(),
            "expensive": expensive_curve.tolist(),
            "too_expensive": too_expensive_curve.tolist(),
            "not_too_cheap": not_too_cheap.tolist(),
            "not_too_expensive": not_too_expensive.tolist(),
        },
    )


def format_psm_result(result: PSMResult) -> str:
    """
    Format PSM result as human-readable text.

    Args:
        result: PSM analysis result

    Returns:
        Formatted text summary
    """
    lines = [
        "Van Westendorp Price Sensitivity Analysis",
        "=" * 50,
        "",
        f"Sample Size: {result.sample_size}",
        f"Price Range Tested: ${result.price_range_tested[0]:.2f} - ${result.price_range_tested[1]:.2f}",
        "",
        "Key Price Points:",
        "-" * 30,
        f"  Optimal Price Point (OPP):     ${result.optimal_price_point:.2f}",
        f"  Indifference Price (IDP):      ${result.indifference_price_point:.2f}",
        f"  Marginal Cheapness (PMC):      ${result.point_of_marginal_cheapness:.2f}",
        f"  Marginal Expensiveness (PME):  ${result.point_of_marginal_expensiveness:.2f}",
        "",
        "Acceptable Price Range:",
        f"  ${result.acceptable_price_range[0]:.2f} - ${result.acceptable_price_range[1]:.2f}",
        "",
        "Interpretation:",
        f"  - Set price near ${result.optimal_price_point:.2f} for maximum acceptance",
        f"  - Prices below ${result.point_of_marginal_cheapness:.2f} may raise quality concerns",
        f"  - Prices above ${result.point_of_marginal_expensiveness:.2f} face strong resistance",
    ]
    return "\n".join(lines)
