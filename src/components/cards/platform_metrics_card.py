from __future__ import annotations

from src.components.cards.common import render_metric_cards


def render_platform_metrics_card(items: list[dict]) -> None:
    render_metric_cards(items)
