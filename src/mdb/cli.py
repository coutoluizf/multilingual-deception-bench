"""
MDB Command Line Interface
==========================

This module provides the CLI for the Multilingual Deception Bench.
It enables dataset validation, model evaluation, and report generation.

Commands:
- mdb validate: Validate dataset integrity
- mdb evaluate: Run evaluation on a model
- mdb report: Generate comparison reports
- mdb models: List available models

Example usage:
    # Validate the dataset
    $ mdb validate --data data/samples/starter_samples.jsonl

    # Run evaluation on Claude
    $ mdb evaluate --model claude-3-5-sonnet --data data/samples/starter_samples.jsonl

    # Generate a report
    $ mdb report --input results/ --output reports/comparison.html
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv

# Load environment variables from .env file (for API keys)
load_dotenv()
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

# =============================================================================
# Console Setup
# =============================================================================

# Rich console for beautiful output
console = Console()

# =============================================================================
# CLI Group
# =============================================================================


@click.group()
@click.version_option(version="0.1.0", prog_name="mdb")
def cli() -> None:
    """
    Multilingual Deception Bench (MDB) - AI Safety Benchmark CLI

    A benchmark for measuring AI-enabled social engineering risk across languages.
    """
    pass


# =============================================================================
# Validate Command
# =============================================================================


@cli.command()
@click.option(
    "--data",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the JSONL dataset file to validate.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Show detailed validation output.",
)
def validate(data: Path, verbose: bool) -> None:
    """
    Validate dataset integrity and schema compliance.

    Checks that all examples in the dataset:
    - Conform to the MDB schema
    - Have proper redaction applied
    - Contain required safety metadata
    - Have valid locale and attack type values

    Example:
        mdb validate --data data/samples/starter_samples.jsonl
    """
    console.print(Panel.fit(
        "[bold blue]MDB Dataset Validator[/bold blue]\n"
        f"Validating: {data}",
        border_style="blue"
    ))

    # Import schema for validation
    try:
        from mdb.schema import AttackExample
    except ImportError:
        console.print("[red]Error: Could not import MDB schema. Is the package installed?[/red]")
        sys.exit(1)

    # Track validation results
    total = 0
    valid = 0
    errors: list[tuple[int, str, str]] = []  # (line_num, example_id, error)

    # Language and attack type distribution
    language_counts: dict[str, int] = {}
    attack_type_counts: dict[str, int] = {}

    # Read and validate each line
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # Count total lines first
        with open(data, "r", encoding="utf-8") as f:
            lines = f.readlines()

        task = progress.add_task("Validating examples...", total=len(lines))

        for line_num, line in enumerate(lines, start=1):
            total += 1
            line = line.strip()
            if not line:
                progress.advance(task)
                continue

            try:
                # Parse JSON
                example_data = json.loads(line)

                # Validate against schema
                example = AttackExample.model_validate(example_data)

                # Track distributions - handle both enum and string values
                lang = str(example.language.value if hasattr(example.language, 'value') else example.language)
                language_counts[lang] = language_counts.get(lang, 0) + 1
                attack_type_str = str(example.attack_type.value if hasattr(example.attack_type, 'value') else example.attack_type)
                attack_type_counts[attack_type_str] = attack_type_counts.get(attack_type_str, 0) + 1

                valid += 1

            except json.JSONDecodeError as e:
                errors.append((line_num, "N/A", f"Invalid JSON: {e}"))
            except Exception as e:
                example_id = example_data.get("id", "unknown") if isinstance(example_data, dict) else "unknown"
                errors.append((line_num, example_id, str(e)))

            progress.advance(task)

    # Display results
    console.print()

    # Summary table
    summary_table = Table(title="Validation Summary", show_header=True, header_style="bold")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Examples", str(total))
    summary_table.add_row("Valid Examples", str(valid))
    summary_table.add_row("Invalid Examples", str(len(errors)))
    summary_table.add_row("Validation Rate", f"{(valid/total)*100:.1f}%" if total > 0 else "N/A")

    console.print(summary_table)
    console.print()

    # Language distribution
    if language_counts:
        lang_table = Table(title="Language Distribution", show_header=True, header_style="bold")
        lang_table.add_column("Language", style="cyan")
        lang_table.add_column("Count", style="green")
        lang_table.add_column("Percentage", style="yellow")

        for lang, count in sorted(language_counts.items()):
            pct = (count / valid) * 100 if valid > 0 else 0
            lang_table.add_row(lang.upper(), str(count), f"{pct:.1f}%")

        console.print(lang_table)
        console.print()

    # Attack type distribution
    if attack_type_counts:
        attack_table = Table(title="Attack Type Distribution", show_header=True, header_style="bold")
        attack_table.add_column("Attack Type", style="cyan")
        attack_table.add_column("Count", style="green")
        attack_table.add_column("Percentage", style="yellow")

        for attack_type, count in sorted(attack_type_counts.items()):
            pct = (count / valid) * 100 if valid > 0 else 0
            attack_table.add_row(attack_type, str(count), f"{pct:.1f}%")

        console.print(attack_table)
        console.print()

    # Show errors if any
    if errors:
        console.print("[bold red]Validation Errors:[/bold red]")
        error_table = Table(show_header=True, header_style="bold red")
        error_table.add_column("Line", style="red")
        error_table.add_column("Example ID", style="yellow")
        error_table.add_column("Error", style="white")

        for line_num, example_id, error in errors[:10]:  # Show first 10 errors
            error_table.add_row(str(line_num), example_id, error[:100])

        console.print(error_table)

        if len(errors) > 10:
            console.print(f"[dim]... and {len(errors) - 10} more errors[/dim]")

        sys.exit(1)
    else:
        console.print("[bold green]✓ All examples are valid![/bold green]")
        sys.exit(0)


# =============================================================================
# Models Command
# =============================================================================


@cli.command()
def models() -> None:
    """
    List available model adapters and their supported models.

    Shows all configured model adapters along with their
    supported model IDs and required environment variables.

    Example:
        mdb models
    """
    console.print(Panel.fit(
        "[bold blue]MDB Available Models[/bold blue]",
        border_style="blue"
    ))

    # Define available models with their metadata
    models_data = [
        {
            "provider": "Anthropic",
            "models": [
                "claude-sonnet-4-20250514",
                "claude-haiku-4-5-20251001",
                "claude-opus-4-5-20251101",
                "claude-sonnet-4-5-20250514",
            ],
            "env_var": "ANTHROPIC_API_KEY",
            "package": "anthropic",
        },
        {
            "provider": "OpenAI",
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "o1",
                "o1-mini",
            ],
            "env_var": "OPENAI_API_KEY",
            "package": "openai",
        },
        {
            "provider": "Google",
            "models": [
                "gemini-2.0-flash-exp",
                "gemini-exp-1206",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
            ],
            "env_var": "GOOGLE_API_KEY",
            "package": "google-generativeai",
        },
    ]

    for provider_data in models_data:
        table = Table(
            title=f"{provider_data['provider']} Models",
            show_header=True,
            header_style="bold"
        )
        table.add_column("Model ID", style="cyan")
        table.add_column("Status", style="green")

        # Check if API key is configured
        import os
        api_key_set = bool(os.environ.get(provider_data["env_var"]))

        for model_id in provider_data["models"]:
            status = "✓ Ready" if api_key_set else "✗ API Key Missing"
            style = "green" if api_key_set else "red"
            table.add_row(model_id, f"[{style}]{status}[/{style}]")

        console.print(table)
        console.print(f"[dim]Env var: {provider_data['env_var']} | Package: {provider_data['package']}[/dim]")
        console.print()


# =============================================================================
# Evaluate Command
# =============================================================================


@cli.command()
@click.option(
    "--model",
    "-m",
    type=str,
    required=True,
    help="Model ID to evaluate (e.g., claude-3-5-sonnet-20241022).",
)
@click.option(
    "--data",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the JSONL dataset file.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default=None,
    help="Output path for results JSON (default: results/<model>_<timestamp>.json).",
)
@click.option(
    "--languages",
    "-l",
    type=str,
    default=None,
    help="Comma-separated list of languages to evaluate (e.g., pt,es,en).",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=5,
    help="Maximum concurrent API requests (default: 5).",
)
@click.option(
    "--limit",
    type=int,
    default=None,
    help="Limit number of examples to evaluate (for testing).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate setup without making API calls.",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Show detailed output for each evaluation.",
)
@click.option(
    "--llm-classifier",
    is_flag=True,
    help="Use LLM-based semantic classifier instead of keyword matching (more accurate but slower).",
)
def evaluate(
    model: str,
    data: Path,
    output: Path | None,
    languages: str | None,
    max_concurrent: int,
    limit: int | None,
    dry_run: bool,
    verbose: bool,
    llm_classifier: bool,
) -> None:
    """
    Run evaluation on a model using the MDB benchmark.

    Evaluates a language model on the deception benchmark examples,
    measuring safety metrics like refusal rate, compliance, and more.

    IMPORTANT: Raw model outputs are scored in memory and NEVER stored.
    Only aggregate scores and metadata are saved.

    Example:
        mdb evaluate --model claude-3-5-sonnet-20241022 --data data/samples/starter_samples.jsonl
    """
    console.print(Panel.fit(
        "[bold blue]MDB Model Evaluation[/bold blue]\n"
        f"Model: {model}\n"
        f"Data: {data}",
        border_style="blue"
    ))

    # Parse languages filter
    language_filter = None
    if languages:
        language_filter = set(lang.strip().lower() for lang in languages.split(","))
        console.print(f"[dim]Filtering to languages: {', '.join(language_filter)}[/dim]")

    # Set up output path
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        output = results_dir / f"{model.replace('/', '_')}_{timestamp}.json"

    # Determine which adapter to use based on model ID
    adapter_class = None
    provider = None

    if model.startswith("claude"):
        provider = "anthropic"
    elif model.startswith("gpt") or model.startswith("o1"):
        provider = "openai"
    elif model.startswith("gemini"):
        provider = "google"
    elif model.startswith("grok"):
        provider = "xai"
    else:
        console.print(f"[red]Error: Unknown model provider for model '{model}'[/red]")
        console.print("[dim]Supported prefixes: claude, gpt, o1, gemini, grok[/dim]")
        sys.exit(1)

    console.print(f"[dim]Provider detected: {provider}[/dim]")

    if dry_run:
        console.print("\n[yellow]DRY RUN MODE - No API calls will be made[/yellow]")
        console.print("[green]✓ Configuration validated successfully[/green]")
        sys.exit(0)

    # Run async evaluation
    try:
        asyncio.run(_run_evaluation(
            model=model,
            provider=provider,
            data_path=data,
            output_path=output,
            language_filter=language_filter,
            max_concurrent=max_concurrent,
            limit=limit,
            verbose=verbose,
            use_llm_classifier=llm_classifier,
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]Evaluation interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error during evaluation: {e}[/red]")
        sys.exit(1)


async def _run_evaluation(
    model: str,
    provider: str,
    data_path: Path,
    output_path: Path,
    language_filter: set[str] | None,
    max_concurrent: int,
    limit: int | None,
    verbose: bool = False,
    use_llm_classifier: bool = False,
) -> None:
    """
    Run the async evaluation pipeline.

    Args:
        model: Model ID to evaluate
        provider: Provider name (anthropic, openai, google)
        data_path: Path to dataset file
        output_path: Path to save results
        language_filter: Optional set of languages to include
        max_concurrent: Max concurrent requests
        limit: Optional limit on examples to evaluate
        verbose: Whether to print detailed output for each evaluation
        use_llm_classifier: Use LLM-based semantic classifier instead of keywords
    """
    # Import required modules
    from mdb.evaluators.adapters import (
        AdapterConfig,
        AnthropicAdapter,
        GoogleAdapter,
        OpenAIAdapter,
        XAIAdapter,
    )
    from mdb.evaluators.metrics import MetricsEvaluator, ResponseClassification
    from mdb.schema import AttackExample

    # Import LLM classifier if needed
    llm_classifier = None
    if use_llm_classifier:
        from mdb.evaluators.llm_classifier import AsyncLLMClassifier
        llm_classifier = AsyncLLMClassifier(provider="anthropic")
        console.print("[cyan]Using LLM-based semantic classifier[/cyan]")

    # Create adapter based on provider
    config = AdapterConfig(model_id=model)

    if provider == "anthropic":
        adapter = AnthropicAdapter(config)
    elif provider == "openai":
        adapter = OpenAIAdapter(config)
    elif provider == "google":
        adapter = GoogleAdapter(config)
    elif provider == "xai":
        adapter = XAIAdapter(config)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    # Health check
    console.print("\n[dim]Checking API connectivity...[/dim]")
    is_healthy = await adapter.health_check()
    if not is_healthy:
        console.print("[red]Error: API health check failed. Check your API key and connectivity.[/red]")
        sys.exit(1)
    console.print("[green]✓ API connection verified[/green]")

    # Load examples
    console.print(f"\n[dim]Loading examples from {data_path}...[/dim]")
    examples: list[AttackExample] = []

    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            example_data = json.loads(line)
            example = AttackExample.model_validate(example_data)

            # Apply language filter
            if language_filter:
                lang = example.language.value if hasattr(example.language, 'value') else str(example.language)
                if lang not in language_filter:
                    continue

            examples.append(example)

            # Apply limit
            if limit and len(examples) >= limit:
                break

    console.print(f"[green]✓ Loaded {len(examples)} examples[/green]")

    # Create metrics evaluator
    metrics_evaluator = MetricsEvaluator(model_id=model)

    # Run evaluation with progress bar
    console.print(f"\n[bold]Running evaluation with {max_concurrent} concurrent requests...[/bold]")

    results: list[dict[str, Any]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Evaluating examples...", total=len(examples))

        # Process examples in batches
        for i in range(0, len(examples), max_concurrent):
            batch = examples[i:i + max_concurrent]
            prompts = [example.content for example in batch]

            # Generate responses
            responses = await adapter.generate_batch(prompts, max_concurrent=max_concurrent)

            # Evaluate each response
            # If using LLM classifier, prepare batch classification
            llm_classifications = {}
            if llm_classifier:
                # Classify all responses in batch using LLM
                items_to_classify = [
                    (example.content, response.content)
                    for example, response in zip(batch, responses)
                ]
                llm_results = await llm_classifier.classify_batch(
                    items_to_classify,
                    max_concurrent=max_concurrent
                )
                for idx, (example, llm_result) in enumerate(zip(batch, llm_results)):
                    llm_classifications[example.id] = llm_result

            for example, response in zip(batch, responses):
                # Get language and attack_type as strings
                lang = example.language.value if hasattr(example.language, 'value') else str(example.language)
                attack = example.attack_type.value if hasattr(example.attack_type, 'value') else str(example.attack_type)

                # Evaluate metrics (raw output scored in memory, never stored)
                evaluation = metrics_evaluator.evaluate_response(
                    response=response.content,
                    example_id=example.id,
                    language=lang,
                    attack_type=attack,
                    latency_ms=response.latency_ms,
                )

                # Override classification if using LLM classifier
                classification_value = evaluation.classification.value
                llm_reasoning = None
                if llm_classifier and example.id in llm_classifications:
                    llm_result = llm_classifications[example.id]
                    classification_value = llm_result.classification
                    llm_reasoning = llm_result.reasoning
                    # Also update the evaluation object for aggregation
                    evaluation.classification = ResponseClassification(classification_value)

                # Store only metadata and metrics (NOT the raw output)
                result = {
                    "example_id": example.id,
                    "language": lang,
                    "attack_type": attack,
                    "classification": classification_value,
                    "metrics": {name: m.value for name, m in evaluation.metrics.items()},
                    "latency_ms": response.latency_ms,
                    "status": response.status.value,
                    "token_usage": {
                        "input": response.token_usage.input_tokens,
                        "output": response.token_usage.output_tokens,
                    },
                }
                # Add LLM reasoning if available
                if llm_reasoning:
                    result["llm_classification_reasoning"] = llm_reasoning
                results.append(result)

                # Verbose output for debugging
                if verbose:
                    classification = evaluation.classification.value
                    # Color code by classification
                    if classification == "refusal":
                        color = "green"
                        icon = "🛡️"
                    elif classification == "soft_refusal":
                        color = "yellow"
                        icon = "⚠️"
                    else:
                        color = "red"
                        icon = "❌"

                    console.print(
                        f"[dim]{len(results):4d}[/dim] {icon} "
                        f"[{color}]{classification:12s}[/{color}] "
                        f"[cyan]{attack:24s}[/cyan] "
                        f"[dim]{response.latency_ms:5.0f}ms[/dim] "
                        f"[dim]{example.id}[/dim]"
                    )

                progress.advance(task)

    # Get aggregated metrics
    aggregated = metrics_evaluator.get_aggregated_results()

    # Build final output
    output_data = {
        "metadata": {
            "model_id": model,
            "provider": provider,
            "timestamp": datetime.utcnow().isoformat(),
            "total_examples": len(results),
            "data_source": str(data_path),
        },
        "aggregated_metrics": {
            "overall": aggregated.overall,
            "by_language": aggregated.by_language,
            "by_attack_type": aggregated.by_attack_type,
        },
        "token_usage": {
            "total_input_tokens": adapter.total_tokens.input_tokens,
            "total_output_tokens": adapter.total_tokens.output_tokens,
            "total_requests": adapter.request_count,
            "error_count": adapter.error_count,
        },
        "individual_results": results,
    }

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, default=str)

    console.print(f"\n[green]✓ Results saved to {output_path}[/green]")

    # Display summary
    console.print()
    summary_table = Table(title="Evaluation Summary", show_header=True, header_style="bold")
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")

    overall = aggregated.overall
    summary_table.add_row("Total Examples", str(len(results)))
    summary_table.add_row("Refusal Rate", f"{overall.get('refusal_rate', 0)*100:.1f}%")
    summary_table.add_row("Soft Refusal Rate", f"{overall.get('soft_refusal_rate', 0)*100:.1f}%")
    summary_table.add_row("Compliance Rate", f"{overall.get('compliance_rate', 0)*100:.1f}%")
    summary_table.add_row("Avg Latency", f"{overall.get('avg_latency_ms', 0):.0f}ms")

    console.print(summary_table)


# =============================================================================
# Report Command
# =============================================================================


@cli.command()
@click.option(
    "--input",
    "-i",
    "input_dir",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Directory containing result JSON files.",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="reports/comparison.html",
    help="Output path for the HTML report.",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["html", "json", "csv"]),
    default="html",
    help="Output format (default: html).",
)
def report(input_dir: Path, output: Path, output_format: str) -> None:
    """
    Generate comparison reports from evaluation results.

    Reads evaluation results from the input directory and generates
    a comparison report showing how different models performed.

    Example:
        mdb report --input results/ --output reports/comparison.html
    """
    console.print(Panel.fit(
        "[bold blue]MDB Report Generator[/bold blue]\n"
        f"Input: {input_dir}\n"
        f"Output: {output}",
        border_style="blue"
    ))

    # Find all result files
    result_files = list(input_dir.glob("*.json"))
    if not result_files:
        console.print(f"[red]Error: No JSON result files found in {input_dir}[/red]")
        sys.exit(1)

    console.print(f"[dim]Found {len(result_files)} result files[/dim]")

    # Load all results
    all_results: list[dict[str, Any]] = []
    for result_file in result_files:
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_results.append(data)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load {result_file}: {e}[/yellow]")

    if not all_results:
        console.print("[red]Error: No valid result files could be loaded[/red]")
        sys.exit(1)

    # Generate comparison table
    comparison_table = Table(
        title="Model Comparison",
        show_header=True,
        header_style="bold"
    )
    comparison_table.add_column("Model", style="cyan")
    comparison_table.add_column("Refusal Rate", style="green")
    comparison_table.add_column("Soft Refusal", style="yellow")
    comparison_table.add_column("Compliance", style="red")
    comparison_table.add_column("Avg Latency", style="blue")
    comparison_table.add_column("Examples", style="dim")

    for result in all_results:
        metadata = result.get("metadata", {})
        metrics = result.get("aggregated_metrics", {}).get("overall", {})

        model_id = metadata.get("model_id", "Unknown")
        total = metadata.get("total_examples", 0)
        refusal = metrics.get("refusal_rate", 0) * 100
        soft_refusal = metrics.get("soft_refusal_rate", 0) * 100
        compliance = metrics.get("compliance_rate", 0) * 100
        latency = metrics.get("avg_latency_ms", 0)

        comparison_table.add_row(
            model_id,
            f"{refusal:.1f}%",
            f"{soft_refusal:.1f}%",
            f"{compliance:.1f}%",
            f"{latency:.0f}ms",
            str(total),
        )

    console.print(comparison_table)

    # Generate output based on format
    output.parent.mkdir(parents=True, exist_ok=True)

    if output_format == "json":
        # JSON output
        comparison_data = {
            "generated_at": datetime.utcnow().isoformat(),
            "models": [
                {
                    "model_id": r.get("metadata", {}).get("model_id"),
                    "provider": r.get("metadata", {}).get("provider"),
                    "metrics": r.get("aggregated_metrics", {}).get("overall", {}),
                    "by_language": r.get("aggregated_metrics", {}).get("by_language", {}),
                    "by_attack_type": r.get("aggregated_metrics", {}).get("by_attack_type", {}),
                }
                for r in all_results
            ],
        }
        with open(output, "w", encoding="utf-8") as f:
            json.dump(comparison_data, f, indent=2)
        console.print(f"\n[green]✓ JSON report saved to {output}[/green]")

    elif output_format == "csv":
        # CSV output
        import csv
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "model_id", "provider", "refusal_rate", "soft_refusal_rate",
                "compliance_rate", "avg_latency_ms", "total_examples"
            ])
            for r in all_results:
                metadata = r.get("metadata", {})
                metrics = r.get("aggregated_metrics", {}).get("overall", {})
                writer.writerow([
                    metadata.get("model_id", ""),
                    metadata.get("provider", ""),
                    metrics.get("refusal_rate", 0),
                    metrics.get("soft_refusal_rate", 0),
                    metrics.get("compliance_rate", 0),
                    metrics.get("avg_latency_ms", 0),
                    metadata.get("total_examples", 0),
                ])
        console.print(f"\n[green]✓ CSV report saved to {output}[/green]")

    else:
        # HTML output
        html_content = _generate_html_report(all_results)
        with open(output, "w", encoding="utf-8") as f:
            f.write(html_content)
        console.print(f"\n[green]✓ HTML report saved to {output}[/green]")


def _generate_html_report(results: list[dict[str, Any]]) -> str:
    """
    Generate an HTML comparison report.

    Args:
        results: List of evaluation result dictionaries

    Returns:
        HTML string for the report
    """
    # Build model rows
    model_rows = ""
    for r in results:
        metadata = r.get("metadata", {})
        metrics = r.get("aggregated_metrics", {}).get("overall", {})

        model_id = metadata.get("model_id", "Unknown")
        provider = metadata.get("provider", "")
        refusal = metrics.get("refusal_rate", 0) * 100
        soft_refusal = metrics.get("soft_refusal_rate", 0) * 100
        compliance = metrics.get("compliance_rate", 0) * 100
        latency = metrics.get("avg_latency_ms", 0)
        total = metadata.get("total_examples", 0)

        # Color code compliance (lower is better for safety)
        compliance_color = "green" if compliance < 20 else "orange" if compliance < 50 else "red"

        model_rows += f"""
        <tr>
            <td><strong>{model_id}</strong><br><small>{provider}</small></td>
            <td style="color: green">{refusal:.1f}%</td>
            <td style="color: orange">{soft_refusal:.1f}%</td>
            <td style="color: {compliance_color}">{compliance:.1f}%</td>
            <td>{latency:.0f}ms</td>
            <td>{total}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MDB Model Comparison Report</title>
    <style>
        :root {{
            --bg-color: #0f172a;
            --card-bg: #1e293b;
            --text-color: #e2e8f0;
            --border-color: #334155;
            --accent-color: #3b82f6;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 2rem;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: var(--accent-color);
            margin-bottom: 0.5rem;
        }}
        .subtitle {{
            color: #94a3b8;
            margin-bottom: 2rem;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background-color: var(--card-bg);
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background-color: #334155;
            font-weight: 600;
        }}
        tr:hover {{
            background-color: #334155;
        }}
        .metric-explanation {{
            margin-top: 2rem;
            padding: 1rem;
            background-color: var(--card-bg);
            border-radius: 8px;
        }}
        .metric-explanation h3 {{
            color: var(--accent-color);
            margin-top: 0;
        }}
        .metric-explanation ul {{
            padding-left: 1.5rem;
        }}
        .metric-explanation li {{
            margin-bottom: 0.5rem;
        }}
        .footer {{
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border-color);
            color: #64748b;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Multilingual Deception Bench</h1>
        <p class="subtitle">Model Comparison Report - Generated {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</p>

        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Refusal Rate</th>
                    <th>Soft Refusal</th>
                    <th>Compliance</th>
                    <th>Avg Latency</th>
                    <th>Examples</th>
                </tr>
            </thead>
            <tbody>
                {model_rows}
            </tbody>
        </table>

        <div class="metric-explanation">
            <h3>Metric Explanations</h3>
            <ul>
                <li><strong>Refusal Rate:</strong> Percentage of prompts where the model clearly refused to comply. Higher is better for safety.</li>
                <li><strong>Soft Refusal:</strong> Percentage where the model added warnings but still provided some content. Indicates partial safety awareness.</li>
                <li><strong>Compliance:</strong> Percentage where the model fully complied with the social engineering request. Lower is better for safety.</li>
                <li><strong>Avg Latency:</strong> Average response time in milliseconds.</li>
            </ul>
        </div>

        <div class="footer">
            <p>Generated by the Multilingual Deception Bench (MDB) CLI</p>
            <p>For more information, visit the project documentation.</p>
        </div>
    </div>
</body>
</html>
"""
    return html


# =============================================================================
# Generate Command
# =============================================================================


@cli.command()
@click.option(
    "--seeds",
    "-s",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to the seeds JSON file (default: data/seeds/pt-br-seeds.json).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="data/generated/pt-br-synthetic.jsonl",
    help="Output path for generated JSONL file.",
)
@click.option(
    "--count",
    "-n",
    type=int,
    default=1000,
    help="Number of examples to generate (default: 1000).",
)
@click.option(
    "--variations",
    "-v",
    type=int,
    default=5,
    help="Variations per seed (default: 5).",
)
@click.option(
    "--random-seed",
    type=int,
    default=None,
    help="Random seed for reproducibility.",
)
def generate(
    seeds: Path | None,
    output: Path,
    count: int,
    variations: int,
    random_seed: int | None,
) -> None:
    """
    Generate synthetic examples from seed patterns.

    Uses the collected seed patterns to generate synthetic attack examples
    for the benchmark. All generated content is properly redacted.

    Example:
        mdb generate --count 1000 --output data/generated/pt-br-synthetic.jsonl
    """
    console.print(Panel.fit(
        "[bold blue]MDB Synthetic Generator[/bold blue]\n"
        f"Count: {count}\n"
        f"Output: {output}",
        border_style="blue"
    ))

    # Import the generator
    try:
        from mdb.generators import SeedBasedGenerator
    except ImportError as e:
        console.print(f"[red]Error importing generator: {e}[/red]")
        sys.exit(1)

    # Find seeds file if not specified
    if seeds is None:
        # Try common locations
        possible_paths = [
            Path("data/seeds/pt-br-seeds.json"),
            Path("../data/seeds/pt-br-seeds.json"),
            Path(__file__).parent.parent.parent / "data" / "seeds" / "pt-br-seeds.json",
        ]
        for path in possible_paths:
            if path.exists():
                seeds = path
                break

        if seeds is None:
            console.print("[red]Error: Could not find seeds file. Use --seeds to specify path.[/red]")
            sys.exit(1)

    console.print(f"[dim]Using seeds from: {seeds}[/dim]")

    # Create generator
    try:
        generator = SeedBasedGenerator(seeds_path=seeds, random_seed=random_seed)
    except Exception as e:
        console.print(f"[red]Error creating generator: {e}[/red]")
        sys.exit(1)

    # Show stats
    stats = generator.get_stats()
    console.print(f"[dim]Loaded {stats['total_seeds']} seeds (v{stats['metadata_version']})[/dim]")

    # Create output directory
    output.parent.mkdir(parents=True, exist_ok=True)

    # Generate examples with progress bar
    generated_count = 0
    valid_count = 0
    errors: list[str] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Generating examples...", total=count)

        with open(output, "w", encoding="utf-8") as f:
            for example in generator.generate(count=count, variations_per_seed=variations):
                try:
                    # Serialize to JSON
                    example_dict = example.model_dump(mode="json")
                    json_line = json.dumps(example_dict, ensure_ascii=False)
                    f.write(json_line + "\n")
                    valid_count += 1
                except Exception as e:
                    errors.append(str(e))

                generated_count += 1
                progress.advance(task)

    # Show results
    console.print()

    results_table = Table(title="Generation Results", show_header=True, header_style="bold")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value", style="green")

    results_table.add_row("Examples Generated", str(generated_count))
    results_table.add_row("Valid Examples", str(valid_count))
    results_table.add_row("Errors", str(len(errors)))
    results_table.add_row("Output File", str(output))
    results_table.add_row("File Size", f"{output.stat().st_size / 1024:.1f} KB")

    console.print(results_table)

    if errors:
        console.print(f"\n[yellow]Warning: {len(errors)} examples had errors[/yellow]")
        if len(errors) <= 5:
            for err in errors:
                console.print(f"[dim]  - {err[:80]}[/dim]")

    console.print(f"\n[green]✓ Generated {valid_count} examples to {output}[/green]")


# =============================================================================
# Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
