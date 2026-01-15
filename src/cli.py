"""Command-line interface for SSR Market Research Tool."""

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.columns import Columns

from src.pipeline import SSRPipeline
from src.ab_testing import run_ab_test, ABTestResult
from src.reporting.aggregator import format_summary_text
from src.ssr.utils import to_likert_5, to_scale_10


console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="ssr-survey",
        description="Run synthetic market research surveys using SSR methodology.",
    )

    parser.add_argument(
        "--product", "-p",
        type=str,
        help="Product description to evaluate",
    )

    parser.add_argument(
        "--compare", "-c",
        type=str,
        help="Second product for A/B comparison",
    )

    parser.add_argument(
        "--name-a",
        type=str,
        default="Product A",
        help="Name for first product in A/B test",
    )

    parser.add_argument(
        "--name-b",
        type=str,
        default="Product B",
        help="Name for second product in A/B test",
    )

    parser.add_argument(
        "--sample-size", "-n",
        type=int,
        default=20,
        help="Number of synthetic respondents (default: 20)",
    )

    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output CSV file path",
    )

    parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o-mini",
        choices=["gpt-4o-mini", "gpt-5-mini", "gpt-5.2"],
        help="LLM model to use (default: gpt-4o-mini)",
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data (no API calls)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output",
    )

    parser.add_argument(
        "--age-range",
        type=str,
        help="Age range filter, e.g., '25-45'",
    )

    parser.add_argument(
        "--gender",
        type=str,
        nargs="+",
        help="Gender filter, e.g., 'Male Female'",
    )

    parser.add_argument(
        "--income",
        type=str,
        nargs="+",
        help="Income filter, e.g., 'High' 'Very High'",
    )

    return parser


def parse_demographics(args) -> dict | None:
    """Parse demographic filters from args."""
    demographics = {}

    if args.age_range:
        try:
            min_age, max_age = map(int, args.age_range.split("-"))
            demographics["age_range"] = [min_age, max_age]
        except ValueError:
            console.print("[red]Invalid age range format. Use: 25-45[/red]")
            sys.exit(1)

    if args.gender:
        demographics["gender"] = args.gender

    if args.income:
        demographics["income_bracket"] = args.income

    return demographics if demographics else None


def display_results(results, quiet: bool = False):
    """Display results using rich formatting."""
    if quiet:
        console.print(f"Mean: {results.mean_score:.2f} | Std: {results.std_dev:.3f}")
        return

    panel = Panel(
        f"[bold]Mean Score:[/bold] {results.mean_score:.2f} ({to_likert_5(results.mean_score):.1f}/5)\n"
        f"[bold]Median:[/bold] {results.median_score:.2f}\n"
        f"[bold]Std Dev:[/bold] {results.std_dev:.3f}\n"
        f"[bold]Range:[/bold] {results.min_score:.2f} - {results.max_score:.2f}\n"
        f"[bold]Sample Size:[/bold] {results.sample_size}\n"
        f"[bold]Total Cost:[/bold] ${results.total_cost:.4f}",
        title="Survey Results",
        border_style="green",
    )
    console.print(panel)

    if results.score_distribution:
        table = Table(title="Score Distribution")
        table.add_column("Range", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Bar", style="green")

        max_count = max(results.score_distribution.values()) if results.score_distribution else 1
        for score_range, count in sorted(results.score_distribution.items()):
            bar_width = int((count / max_count) * 20)
            bar = "█" * bar_width
            table.add_row(score_range, str(count), bar)

        console.print(table)

    console.print("\n[bold]Top 3 Responses (Highest Intent):[/bold]")
    sorted_results = sorted(results.results, key=lambda x: x.ssr_score, reverse=True)
    for i, r in enumerate(sorted_results[:3], 1):
        console.print(f"  {i}. [cyan]Score: {r.ssr_score:.2f}[/cyan]")
        console.print(f"     {r.response_text[:100]}...")


def export_csv(results, output_path: str):
    """Export results to CSV."""
    import pandas as pd

    rows = []
    for r in results.results:
        row = {
            "persona_id": r.persona_id,
            "ssr_score": r.ssr_score,
            "likert_5": to_likert_5(r.ssr_score),
            "scale_10": to_scale_10(r.ssr_score),
            "response_text": r.response_text,
        }
        if r.persona_data:
            row.update({
                "age": r.persona_data.get("age"),
                "gender": r.persona_data.get("gender"),
                "occupation": r.persona_data.get("occupation"),
            })
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    console.print(f"[green]Results exported to {output_path}[/green]")


def export_json(results) -> str:
    """Export results as JSON."""
    data = {
        "summary": {
            "mean_score": results.mean_score,
            "median_score": results.median_score,
            "std_dev": results.std_dev,
            "min_score": results.min_score,
            "max_score": results.max_score,
            "sample_size": results.sample_size,
            "total_cost": results.total_cost,
        },
        "distribution": results.score_distribution,
        "results": [
            {
                "persona_id": r.persona_id,
                "ssr_score": r.ssr_score,
                "response_text": r.response_text,
                "persona": r.persona_data,
            }
            for r in results.results
        ],
    }
    return json.dumps(data, indent=2)


def display_ab_results(ab_result: ABTestResult, quiet: bool = False):
    """Display A/B test results using rich formatting."""
    if quiet:
        winner_str = ab_result.winner if ab_result.winner else "No winner"
        console.print(
            f"{ab_result.product_a_name}: {ab_result.results_a.mean_score:.2f} | "
            f"{ab_result.product_b_name}: {ab_result.results_b.mean_score:.2f} | "
            f"p={ab_result.p_value:.4f} | Winner: {winner_str}"
        )
        return

    panel_a = Panel(
        f"[bold]Mean Score:[/bold] {ab_result.results_a.mean_score:.3f}\n"
        f"[bold]Likert:[/bold] {to_likert_5(ab_result.results_a.mean_score):.1f}/5\n"
        f"[bold]Std Dev:[/bold] {ab_result.results_a.std_dev:.3f}\n"
        f"[bold]Sample:[/bold] {ab_result.results_a.sample_size}",
        title=f"[cyan]{ab_result.product_a_name}[/cyan]",
        border_style="cyan",
    )

    panel_b = Panel(
        f"[bold]Mean Score:[/bold] {ab_result.results_b.mean_score:.3f}\n"
        f"[bold]Likert:[/bold] {to_likert_5(ab_result.results_b.mean_score):.1f}/5\n"
        f"[bold]Std Dev:[/bold] {ab_result.results_b.std_dev:.3f}\n"
        f"[bold]Sample:[/bold] {ab_result.results_b.sample_size}",
        title=f"[magenta]{ab_result.product_b_name}[/magenta]",
        border_style="magenta",
    )

    console.print(Columns([panel_a, panel_b]))

    table = Table(title="Statistical Analysis")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Mean Difference (A - B)", f"{ab_result.mean_difference:+.3f}")
    table.add_row("Relative Difference", f"{ab_result.relative_difference:+.1%}")
    table.add_row("Effect Size (Cohen's d)", f"{ab_result.effect_size:.3f}")
    table.add_row("t-statistic", f"{ab_result.t_statistic:.3f}")
    table.add_row("p-value", f"{ab_result.p_value:.4f}")
    table.add_row(
        "95% Confidence Interval",
        f"[{ab_result.confidence_interval[0]:.3f}, {ab_result.confidence_interval[1]:.3f}]"
    )

    console.print(table)

    if ab_result.significant:
        console.print(
            f"\n[bold green]WINNER: {ab_result.winner}[/bold green] "
            f"(statistically significant, p < 0.05)"
        )
    else:
        console.print(
            "\n[yellow]No statistically significant difference detected.[/yellow]"
        )


def main():
    """Main CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.product:
        console.print("[red]Error: --product is required[/red]")
        sys.exit(1)

    demographics = parse_demographics(args)

    if args.compare:
        if not args.quiet:
            console.print("[bold]A/B Test Mode[/bold]")
            console.print(f"[bold]{args.name_a}:[/bold] {args.product[:60]}...")
            console.print(f"[bold]{args.name_b}:[/bold] {args.compare[:60]}...")
            console.print(f"[bold]Sample Size:[/bold] {args.sample_size} per product")
            console.print(f"[bold]Model:[/bold] {args.model}")
            if args.mock:
                console.print("[yellow]Using mock data (no API calls)[/yellow]")
            console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=args.quiet,
        ) as progress:
            progress.add_task("Running A/B test...", total=None)

            ab_result = run_ab_test(
                product_a=args.product,
                product_b=args.compare,
                sample_size=args.sample_size,
                product_a_name=args.name_a,
                product_b_name=args.name_b,
                llm_model=args.model,
                target_demographics=demographics,
                use_mock=args.mock,
                show_progress=False,
            )

        if args.json:
            print(json.dumps(ab_result.to_dict(), indent=2))
        else:
            display_ab_results(ab_result, quiet=args.quiet)

        return

    pipeline = SSRPipeline(llm_model=args.model)

    if not args.quiet:
        console.print(f"[bold]Product:[/bold] {args.product[:80]}...")
        console.print(f"[bold]Sample Size:[/bold] {args.sample_size}")
        console.print(f"[bold]Model:[/bold] {args.model}")
        if args.mock:
            console.print("[yellow]Using mock data (no API calls)[/yellow]")
        console.print()

    if args.mock:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            disable=args.quiet,
        ) as progress:
            progress.add_task("Generating mock responses...", total=None)
            results = pipeline.run_survey_mock(
                product_description=args.product,
                sample_size=args.sample_size,
            )
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console,
            disable=args.quiet,
        ) as progress:
            task = progress.add_task(
                "Surveying respondents",
                total=args.sample_size,
            )

            def update_progress(current: int, total: int) -> None:
                progress.update(task, completed=current)

            results = pipeline.run_survey(
                product_description=args.product,
                sample_size=args.sample_size,
                target_demographics=demographics,
                show_progress=False,
                progress_callback=update_progress,
            )

    if args.json:
        print(export_json(results))
    else:
        display_results(results, quiet=args.quiet)

    if args.output:
        export_csv(results, args.output)


if __name__ == "__main__":
    main()
