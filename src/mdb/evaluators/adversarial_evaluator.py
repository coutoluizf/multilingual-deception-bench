"""
Adversarial Robustness Evaluator for MDB.

This module evaluates how well LLM safety mechanisms hold up against
adversarial prompting techniques. It compares refusal rates on baseline
prompts vs. adversarial variants.

The goal is to identify weaknesses in safety systems so they can be improved.
"""

import asyncio
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Import the LLM classifier for semantic evaluation
from mdb.evaluators.llm_classifier import LLMSemanticClassifier
from mdb.generators.adversarial_generator import (
    AdversarialTechnique,
    generate_adversarial_dataset,
    save_adversarial_dataset,
)


@dataclass
class TechniqueResult:
    """Results for a single adversarial technique."""
    technique: str
    total: int = 0
    refusal: int = 0
    soft_refusal: int = 0
    compliance: int = 0
    unclear: int = 0

    @property
    def refusal_rate(self) -> float:
        """Calculate refusal rate."""
        if self.total == 0:
            return 0.0
        return self.refusal / self.total

    @property
    def safety_rate(self) -> float:
        """Calculate combined safety rate (refusal + soft_refusal)."""
        if self.total == 0:
            return 0.0
        return (self.refusal + self.soft_refusal) / self.total

    @property
    def compliance_rate(self) -> float:
        """Calculate compliance rate."""
        if self.total == 0:
            return 0.0
        return self.compliance / self.total


@dataclass
class AdversarialEvaluationResult:
    """Complete results of an adversarial robustness evaluation."""
    model_id: str
    language: str
    timestamp: str
    technique_results: dict[str, TechniqueResult] = field(default_factory=dict)
    examples: list[dict] = field(default_factory=list)

    def get_baseline_refusal_rate(self) -> float:
        """Get refusal rate for baseline (non-adversarial) prompts."""
        if 'baseline' in self.technique_results:
            return self.technique_results['baseline'].refusal_rate
        return 0.0

    def get_adversarial_degradation(self) -> dict[str, float]:
        """
        Calculate how much each technique degrades safety.

        Returns dict of technique -> degradation percentage
        (negative means the technique bypassed safety more)
        """
        baseline_rate = self.get_baseline_refusal_rate()
        degradation = {}

        for tech, result in self.technique_results.items():
            if tech != 'baseline':
                # Degradation = baseline - technique refusal rate
                # Positive means technique reduced safety
                degradation[tech] = baseline_rate - result.refusal_rate

        return degradation


async def evaluate_single_prompt(
    classifier: LLMSemanticClassifier,
    model_id: str,
    prompt: str,
    adapter_module: Any
) -> tuple[str, dict]:
    """
    Evaluate a single prompt against a model.

    Args:
        classifier: LLM semantic classifier instance
        model_id: Model to evaluate
        prompt: The prompt to send
        adapter_module: The appropriate adapter for the model

    Returns:
        Tuple of (response_text, classification_result)
    """
    try:
        # Get response from the model
        adapter = adapter_module.get_adapter(model_id)
        response = await adapter.generate(prompt)

        # Classify the response
        classification = await classifier.classify_single(prompt, response)

        return response, classification
    except Exception as e:
        return str(e), {
            'classification': 'unclear',
            'confidence': 0.0,
            'reasoning': f'Error: {str(e)}'
        }


async def run_adversarial_evaluation(
    model_id: str,
    language: str,
    num_seeds: int = 10,
    techniques: list[AdversarialTechnique] | None = None,
    output_dir: str | Path = 'results'
) -> AdversarialEvaluationResult:
    """
    Run a complete adversarial robustness evaluation.

    Args:
        model_id: Model identifier (e.g., 'claude-haiku-4-5', 'gpt-4o')
        language: Language code ('en' or 'pt')
        num_seeds: Number of base seeds to use
        techniques: List of techniques to test (all if None)
        output_dir: Directory to save results

    Returns:
        AdversarialEvaluationResult with complete metrics
    """
    # Determine which adapter to use based on model name
    if 'claude' in model_id.lower():
        from mdb.evaluators.adapters import anthropic_adapter as adapter_module
    elif 'gpt' in model_id.lower() or model_id.startswith('o'):
        from mdb.evaluators.adapters import openai_adapter as adapter_module
    else:
        raise ValueError(f"Unknown model type: {model_id}")

    # Initialize classifier
    classifier = LLMSemanticClassifier()

    # Generate adversarial dataset
    if techniques is None:
        techniques = list(AdversarialTechnique)

    dataset = generate_adversarial_dataset(
        language=language,
        num_seeds=num_seeds,
        techniques=techniques,
        seed_random=42  # For reproducibility
    )

    print(f"Generated {len(dataset)} adversarial prompts for {language}")
    print(f"Techniques: {[t.value for t in techniques]}")

    # Initialize result tracking
    result = AdversarialEvaluationResult(
        model_id=model_id,
        language=language,
        timestamp=datetime.now().isoformat()
    )

    # Initialize technique results
    for tech in techniques:
        result.technique_results[tech.value] = TechniqueResult(technique=tech.value)

    # Run evaluations
    print(f"\nEvaluating {model_id} on {len(dataset)} prompts...")

    for i, item in enumerate(dataset):
        technique = item['technique']
        prompt = item['content']

        # Show progress
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i + 1}/{len(dataset)}")

        try:
            # Get model response and classification
            response, classification = await evaluate_single_prompt(
                classifier, model_id, prompt, adapter_module
            )

            # Update technique results
            tech_result = result.technique_results[technique]
            tech_result.total += 1

            cls = classification.get('classification', 'unclear')
            if cls == 'refusal':
                tech_result.refusal += 1
            elif cls == 'soft_refusal':
                tech_result.soft_refusal += 1
            elif cls == 'compliance':
                tech_result.compliance += 1
            else:
                tech_result.unclear += 1

            # Store example (redacted for safety)
            result.examples.append({
                'id': item['id'],
                'technique': technique,
                'classification': cls,
                'confidence': classification.get('confidence', 0.0),
                # Don't store actual content for safety
                'original_id': item['original_id'],
            })

        except Exception as e:
            print(f"  Error on item {i}: {e}")
            result.technique_results[technique].unclear += 1

        # Small delay to avoid rate limits
        await asyncio.sleep(0.5)

    return result


def format_results_report(results: list[AdversarialEvaluationResult]) -> str:
    """
    Format evaluation results as a markdown report.

    Args:
        results: List of evaluation results

    Returns:
        Formatted markdown string
    """
    lines = [
        "# Adversarial Robustness Evaluation Report",
        "",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d')}",
        "**Classifier:** LLM Semantic Classifier (Claude Haiku)",
        "",
        "## Executive Summary",
        "",
        "This report evaluates how well LLM safety mechanisms hold up against",
        "adversarial prompting techniques.",
        "",
        "## Results by Model",
        "",
    ]

    for result in results:
        lines.append(f"### {result.model_id} ({result.language.upper()})")
        lines.append("")
        lines.append("| Technique | Refusal Rate | Compliance | Safety Degradation |")
        lines.append("|-----------|--------------|------------|-------------------|")

        baseline_rate = result.get_baseline_refusal_rate()
        degradation = result.get_adversarial_degradation()

        for tech, tech_result in result.technique_results.items():
            deg = degradation.get(tech, 0.0)
            deg_str = f"{deg*100:+.1f}%" if tech != 'baseline' else "—"
            lines.append(
                f"| {tech} | {tech_result.refusal_rate*100:.1f}% | "
                f"{tech_result.compliance_rate*100:.1f}% | {deg_str} |"
            )

        lines.append("")

    # Overall findings
    lines.append("## Key Findings")
    lines.append("")

    # Find most effective techniques
    all_degradations = defaultdict(list)
    for result in results:
        for tech, deg in result.get_adversarial_degradation().items():
            all_degradations[tech].append(deg)

    avg_degradations = {
        tech: sum(vals) / len(vals)
        for tech, vals in all_degradations.items()
    }

    if avg_degradations:
        worst_tech = max(avg_degradations.items(), key=lambda x: x[1])
        lines.append(f"- **Most effective attack technique:** {worst_tech[0]} "
                     f"(avg {worst_tech[1]*100:.1f}% safety degradation)")
        lines.append("")

    lines.append("---")
    lines.append("*Report generated by MDB Adversarial Robustness Evaluator*")

    return "\n".join(lines)


def save_results(
    results: list[AdversarialEvaluationResult],
    output_dir: str | Path = 'results'
) -> Path:
    """
    Save evaluation results to JSON and markdown.

    Args:
        results: List of evaluation results
        output_dir: Directory to save results

    Returns:
        Path to the saved report
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save JSON results
    json_path = output_dir / f'adversarial_results_{timestamp}.json'
    json_data = []
    for result in results:
        json_data.append({
            'model_id': result.model_id,
            'language': result.language,
            'timestamp': result.timestamp,
            'technique_results': {
                tech: {
                    'total': tr.total,
                    'refusal': tr.refusal,
                    'soft_refusal': tr.soft_refusal,
                    'compliance': tr.compliance,
                    'unclear': tr.unclear,
                    'refusal_rate': tr.refusal_rate,
                    'compliance_rate': tr.compliance_rate,
                }
                for tech, tr in result.technique_results.items()
            },
            'baseline_refusal_rate': result.get_baseline_refusal_rate(),
            'adversarial_degradation': result.get_adversarial_degradation(),
        })

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2)

    # Save markdown report
    report_path = output_dir.parent / 'reports' / f'adversarial_report_{timestamp}.md'
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = format_results_report(results)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Results saved to: {json_path}")
    print(f"Report saved to: {report_path}")

    return report_path


async def run_poc_evaluation():
    """
    Run a POC adversarial evaluation on Claude and GPT models.

    This is a quick test with 10 seeds and all techniques.
    """
    print("=" * 60)
    print("ADVERSARIAL ROBUSTNESS POC EVALUATION")
    print("=" * 60)

    # Models to test
    models = [
        'claude-haiku-4-5-20251001',
        'gpt-4o',
    ]

    # Languages to test
    languages = ['pt', 'en']

    # Number of seeds (10 seeds × 6 techniques = 60 prompts per model/language)
    num_seeds = 10

    all_results = []

    for model_id in models:
        for language in languages:
            print(f"\n{'='*60}")
            print(f"Testing {model_id} on {language.upper()}")
            print(f"{'='*60}")

            try:
                result = await run_adversarial_evaluation(
                    model_id=model_id,
                    language=language,
                    num_seeds=num_seeds
                )
                all_results.append(result)

                # Print quick summary
                print(f"\n{model_id} ({language}) Results:")
                print("-" * 40)
                for tech, tr in result.technique_results.items():
                    print(f"  {tech:15s}: {tr.refusal_rate*100:5.1f}% refusal")

            except Exception as e:
                print(f"Error evaluating {model_id} on {language}: {e}")

    # Save results
    if all_results:
        report_path = save_results(all_results)
        print(f"\n{'='*60}")
        print(f"POC COMPLETE! Report: {report_path}")
        print(f"{'='*60}")

    return all_results


if __name__ == '__main__':
    # Run POC evaluation
    asyncio.run(run_poc_evaluation())
