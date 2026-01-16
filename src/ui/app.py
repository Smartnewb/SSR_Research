"""Streamlit web UI for SSR Market Research Tool."""

import io
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pipeline import SSRPipeline
from src.ab_testing import run_ab_test, ABTestResult
from src.personas.templates import TEMPLATES
from src.reporting.aggregator import format_summary_text, get_top_responses
from src.ssr.utils import to_likert_5, to_scale_10


st.set_page_config(
    page_title="SSR Market Research",
    page_icon="📊",
    layout="wide",
)


def init_session_state():
    """Initialize session state variables."""
    if "results" not in st.session_state:
        st.session_state.results = None
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = None
    if "history" not in st.session_state:
        st.session_state.history = []
    if "ab_results" not in st.session_state:
        st.session_state.ab_results = None


def create_sidebar():
    """Create sidebar with settings."""
    st.sidebar.header("⚙️ Settings")

    model = st.sidebar.selectbox(
        "LLM Model",
        ["gpt-5-nano", "gpt-5-mini", "gpt-5.2", "gpt-4o-mini"],
        index=0,
        help="gpt-5-nano is most cost-effective",
    )

    sample_size = st.sidebar.slider(
        "Sample Size",
        min_value=5,
        max_value=200,
        value=20,
        step=5,
        help="Number of synthetic respondents",
    )

    st.sidebar.subheader("Demographic Filters (Optional)")

    use_filters = st.sidebar.checkbox("Enable demographic targeting")

    demographics = None
    if use_filters:
        age_range = st.sidebar.slider(
            "Age Range",
            min_value=18,
            max_value=80,
            value=(25, 55),
        )

        gender_options = st.sidebar.multiselect(
            "Gender",
            options=TEMPLATES["gender"],
            default=TEMPLATES["gender"],
        )

        income_options = st.sidebar.multiselect(
            "Income Bracket",
            options=TEMPLATES["income_bracket"],
            default=TEMPLATES["income_bracket"],
        )

        demographics = {
            "age_range": list(age_range),
            "gender": gender_options if gender_options else None,
            "income_bracket": income_options if income_options else None,
        }
        demographics = {k: v for k, v in demographics.items() if v}

    st.sidebar.divider()
    st.sidebar.caption("💡 Tip: Start with sample size 10-20 for testing")

    return model, sample_size, demographics


def display_results(results):
    """Display survey results."""
    st.header("📊 Results")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Mean Score",
            f"{results.mean_score:.2f}",
            help="Average SSR score (0-1 scale)",
        )

    with col2:
        st.metric(
            "Likert Scale",
            f"{to_likert_5(results.mean_score):.1f}/5",
            help="Converted to 1-5 Likert scale",
        )

    with col3:
        st.metric(
            "Std Dev",
            f"{results.std_dev:.3f}",
            help="Score variance (higher = more diverse opinions)",
        )

    with col4:
        st.metric(
            "Total Cost",
            f"${results.total_cost:.4f}",
            help="API cost for this survey",
        )

    st.subheader("Score Distribution")

    if results.score_distribution:
        dist_df = pd.DataFrame(
            list(results.score_distribution.items()),
            columns=["Score Range", "Count"],
        )
        st.bar_chart(dist_df.set_index("Score Range"))

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("🔝 Top Responses (Highest Intent)")
        top_high = get_top_responses(results.results, n=3, high=True)
        for i, r in enumerate(top_high, 1):
            with st.expander(f"#{i} - Score: {r.ssr_score:.2f}"):
                st.write(f"**Response:** {r.response_text}")
                if r.persona_data:
                    st.caption(
                        f"Persona: {r.persona_data.get('age', '?')}yo "
                        f"{r.persona_data.get('gender', '?')}, "
                        f"{r.persona_data.get('occupation', '?')}"
                    )

    with col_right:
        st.subheader("🔻 Bottom Responses (Lowest Intent)")
        top_low = get_top_responses(results.results, n=3, high=False)
        for i, r in enumerate(top_low, 1):
            with st.expander(f"#{i} - Score: {r.ssr_score:.2f}"):
                st.write(f"**Response:** {r.response_text}")
                if r.persona_data:
                    st.caption(
                        f"Persona: {r.persona_data.get('age', '?')}yo "
                        f"{r.persona_data.get('gender', '?')}, "
                        f"{r.persona_data.get('occupation', '?')}"
                    )

    st.subheader("📋 All Responses")

    all_data = []
    for r in results.results:
        row = {
            "Score": f"{r.ssr_score:.3f}",
            "Response": r.response_text[:100] + "..." if len(r.response_text) > 100 else r.response_text,
        }
        if r.persona_data:
            row["Age"] = r.persona_data.get("age", "")
            row["Gender"] = r.persona_data.get("gender", "")
            row["Occupation"] = r.persona_data.get("occupation", "")
        all_data.append(row)

    df = pd.DataFrame(all_data)
    st.dataframe(df, use_container_width=True)


def export_results(results, product_description):
    """Create CSV export of results."""
    rows = []
    for r in results.results:
        row = {
            "persona_id": r.persona_id,
            "ssr_score": r.ssr_score,
            "likert_5": to_likert_5(r.ssr_score),
            "scale_10": to_scale_10(r.ssr_score),
            "response_text": r.response_text,
            "tokens_used": r.tokens_used,
            "cost": r.cost,
            "latency_ms": r.latency_ms,
        }
        if r.persona_data:
            row.update({
                "age": r.persona_data.get("age"),
                "gender": r.persona_data.get("gender"),
                "occupation": r.persona_data.get("occupation"),
                "location": r.persona_data.get("location"),
                "income_bracket": r.persona_data.get("income_bracket"),
            })
        rows.append(row)

    df = pd.DataFrame(rows)

    summary = {
        "product_description": product_description,
        "sample_size": results.sample_size,
        "mean_score": results.mean_score,
        "median_score": results.median_score,
        "std_dev": results.std_dev,
        "total_cost": results.total_cost,
    }

    return df, summary


def display_ab_results(ab_result: ABTestResult):
    """Display A/B test results."""
    st.header("🔄 A/B Test Results")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(f"📦 {ab_result.product_a_name}")
        st.metric("Mean Score", f"{ab_result.results_a.mean_score:.3f}")
        st.metric("Likert Scale", f"{to_likert_5(ab_result.results_a.mean_score):.1f}/5")
        st.metric("Std Dev", f"{ab_result.results_a.std_dev:.3f}")
        st.caption(f"Sample Size: {ab_result.results_a.sample_size}")

    with col2:
        st.subheader(f"📦 {ab_result.product_b_name}")
        st.metric("Mean Score", f"{ab_result.results_b.mean_score:.3f}")
        st.metric("Likert Scale", f"{to_likert_5(ab_result.results_b.mean_score):.1f}/5")
        st.metric("Std Dev", f"{ab_result.results_b.std_dev:.3f}")
        st.caption(f"Sample Size: {ab_result.results_b.sample_size}")

    st.subheader("📈 Statistical Analysis")

    stats_col1, stats_col2, stats_col3 = st.columns(3)

    with stats_col1:
        st.metric(
            "Mean Difference (A - B)",
            f"{ab_result.mean_difference:+.3f}",
            help="Positive = A is better, Negative = B is better",
        )

    with stats_col2:
        st.metric(
            "Effect Size (Cohen's d)",
            f"{ab_result.effect_size:.3f}",
            help="Small: 0.2, Medium: 0.5, Large: 0.8",
        )

    with stats_col3:
        st.metric(
            "p-value",
            f"{ab_result.p_value:.4f}",
            help="< 0.05 = statistically significant",
        )

    st.divider()

    if ab_result.significant:
        st.success(
            f"🏆 **Winner: {ab_result.winner}** "
            f"(statistically significant, p < 0.05)"
        )
    else:
        st.warning("⚖️ No statistically significant difference detected.")

    with st.expander("📊 Detailed Statistics"):
        st.json({
            "mean_difference": ab_result.mean_difference,
            "relative_difference": f"{ab_result.relative_difference:.1%}",
            "effect_size": ab_result.effect_size,
            "t_statistic": ab_result.t_statistic,
            "p_value": ab_result.p_value,
            "confidence_interval_95": list(ab_result.confidence_interval),
            "significant": ab_result.significant,
            "winner": ab_result.winner,
        })


def main():
    """Main application."""
    init_session_state()

    st.title("📊 SSR Market Research Tool")
    st.markdown(
        "Generate synthetic purchase intent data using the "
        "[Semantic Similarity Rating](https://arxiv.org/html/2510.08338v3) method."
    )

    model, sample_size, demographics = create_sidebar()

    tab1, tab2 = st.tabs(["📋 Single Survey", "🔄 A/B Testing"])

    with tab1:
        st.header("🛍️ Product Concept")

        product_description = st.text_area(
            "Describe your product concept",
            placeholder="Example: A smart coffee mug that keeps your drink at the perfect temperature all day. Connects to your phone via Bluetooth and learns your preferences over time. Price: $79.",
            height=150,
            key="single_product",
        )

        col1, col2 = st.columns([1, 3])

        with col1:
            use_mock = st.checkbox(
                "Use mock data (no API)",
                value=True,
                help="Test without API calls (free)",
                key="single_mock",
            )

        with col2:
            run_button = st.button(
                "🚀 Run Survey",
                type="primary",
                disabled=not product_description.strip(),
                key="single_run",
            )

        if run_button and product_description.strip():
            with st.spinner(f"Surveying {sample_size} synthetic respondents..."):
                pipeline = SSRPipeline(llm_model=model)

                if use_mock:
                    results = pipeline.run_survey_mock(
                        product_description=product_description,
                        sample_size=sample_size,
                    )
                else:
                    results = pipeline.run_survey(
                        product_description=product_description,
                        sample_size=sample_size,
                        target_demographics=demographics,
                    )

                st.session_state.results = results
                st.session_state.pipeline = pipeline
                st.session_state.history.append({
                    "product": product_description[:50] + "...",
                    "mean_score": results.mean_score,
                    "sample_size": results.sample_size,
                })

        if st.session_state.results:
            results = st.session_state.results

            display_results(results)

            st.divider()

            df, summary = export_results(results, product_description)

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv_data,
                file_name="ssr_results.csv",
                mime="text/csv",
            )

            with st.expander("📊 Summary JSON"):
                st.json(summary)

    with tab2:
        st.header("🔄 A/B Test Comparison")
        st.markdown("Compare two product concepts side-by-side.")

        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Product A")
            product_a_name = st.text_input("Name", value="Product A", key="ab_name_a")
            product_a = st.text_area(
                "Description",
                placeholder="First product concept...",
                height=100,
                key="ab_product_a",
            )

        with col_b:
            st.subheader("Product B")
            product_b_name = st.text_input("Name", value="Product B", key="ab_name_b")
            product_b = st.text_area(
                "Description",
                placeholder="Second product concept...",
                height=100,
                key="ab_product_b",
            )

        col1, col2 = st.columns([1, 3])

        with col1:
            ab_use_mock = st.checkbox(
                "Use mock data (no API)",
                value=True,
                help="Test without API calls (free)",
                key="ab_mock",
            )

        with col2:
            ab_run_button = st.button(
                "🔬 Run A/B Test",
                type="primary",
                disabled=not (product_a.strip() and product_b.strip()),
                key="ab_run",
            )

        if ab_run_button and product_a.strip() and product_b.strip():
            with st.spinner(f"Running A/B test with {sample_size} respondents per product..."):
                ab_result = run_ab_test(
                    product_a=product_a,
                    product_b=product_b,
                    sample_size=sample_size,
                    product_a_name=product_a_name,
                    product_b_name=product_b_name,
                    llm_model=model,
                    target_demographics=demographics,
                    use_mock=ab_use_mock,
                    show_progress=False,
                )
                st.session_state.ab_results = ab_result

        if st.session_state.ab_results:
            display_ab_results(st.session_state.ab_results)

    if st.session_state.history:
        st.sidebar.divider()
        st.sidebar.subheader("📜 History")
        for i, h in enumerate(reversed(st.session_state.history[-5:])):
            st.sidebar.caption(
                f"{h['product']} → {h['mean_score']:.2f} (n={h['sample_size']})"
            )


if __name__ == "__main__":
    main()
