"""Tag generation helpers for synthetic cloud billing records."""

from __future__ import annotations

from dataclasses import dataclass
from random import Random

TEAM_CATALOG = [
    {
        "owner_team": "payments-platform",
        "cost_center": "CC-1001",
        "product_line": "payments",
        "default_environment": "prod",
        "initiative_prefix": "PAY",
    },
    {
        "owner_team": "core-infra",
        "cost_center": "CC-1002",
        "product_line": "platform",
        "default_environment": "prod",
        "initiative_prefix": "INF",
    },
    {
        "owner_team": "growth-engineering",
        "cost_center": "CC-1003",
        "product_line": "growth",
        "default_environment": "staging",
        "initiative_prefix": "GRO",
    },
    {
        "owner_team": "data-platform",
        "cost_center": "CC-1004",
        "product_line": "analytics",
        "default_environment": "prod",
        "initiative_prefix": "DAT",
    },
]

ENVIRONMENTS = ["prod", "staging", "test", "sandbox"]
INITIATIVE_STAGES = ["discovery", "build", "implementation", "operate", "support"]
ASSET_LIFECYCLES = ["prototype", "construction", "production", "maintenance"]


@dataclass(frozen=True)
class TagBundle:
    """Represents generated infrastructure and accounting tags."""

    cost_center: str | None
    owner_team: str | None
    environment: str | None
    product_line: str | None
    capitalization_candidate: str | None
    initiative_id: str | None
    initiative_stage: str | None
    asset_lifecycle: str | None


def generate_tag_bundle(
    rng: Random,
    imperfect_tag_rate: float,
    account_index: int,
) -> TagBundle:
    """Generate a tag bundle with a controlled rate of imperfect metadata."""

    team = TEAM_CATALOG[account_index % len(TEAM_CATALOG)]
    environment = rng.choices(
        population=ENVIRONMENTS,
        weights=[0.58, 0.18, 0.16, 0.08],
        k=1,
    )[0]
    initiative_stage = rng.choices(
        population=INITIATIVE_STAGES,
        weights=[0.08, 0.24, 0.18, 0.34, 0.16],
        k=1,
    )[0]
    asset_lifecycle = rng.choices(
        population=ASSET_LIFECYCLES,
        weights=[0.12, 0.23, 0.49, 0.16],
        k=1,
    )[0]

    capitalization_candidate = (
        "true" if initiative_stage in {"build", "implementation"} else "false"
    )
    initiative_suffix = rng.randint(100, 999)
    initiative_id = f"{team['initiative_prefix']}-{initiative_suffix}"

    bundle = TagBundle(
        cost_center=team["cost_center"],
        owner_team=team["owner_team"],
        environment=environment,
        product_line=team["product_line"],
        capitalization_candidate=capitalization_candidate,
        initiative_id=initiative_id,
        initiative_stage=initiative_stage,
        asset_lifecycle=asset_lifecycle,
    )

    if rng.random() >= imperfect_tag_rate:
        return bundle

    scenario = rng.choice(
        ["missing_initiative", "missing_owner", "invalid_capex", "null_environment"]
    )

    if scenario == "missing_initiative":
        return TagBundle(
            cost_center=bundle.cost_center,
            owner_team=bundle.owner_team,
            environment=bundle.environment,
            product_line=bundle.product_line,
            capitalization_candidate=bundle.capitalization_candidate,
            initiative_id=None,
            initiative_stage=bundle.initiative_stage,
            asset_lifecycle=bundle.asset_lifecycle,
        )
    if scenario == "missing_owner":
        return TagBundle(
            cost_center=bundle.cost_center,
            owner_team=None,
            environment=bundle.environment,
            product_line=bundle.product_line,
            capitalization_candidate=bundle.capitalization_candidate,
            initiative_id=bundle.initiative_id,
            initiative_stage=bundle.initiative_stage,
            asset_lifecycle=bundle.asset_lifecycle,
        )
    if scenario == "invalid_capex":
        return TagBundle(
            cost_center=bundle.cost_center,
            owner_team=bundle.owner_team,
            environment=bundle.environment,
            product_line=bundle.product_line,
            capitalization_candidate="unknown",
            initiative_id=bundle.initiative_id,
            initiative_stage=bundle.initiative_stage,
            asset_lifecycle=bundle.asset_lifecycle,
        )

    return TagBundle(
        cost_center=bundle.cost_center,
        owner_team=bundle.owner_team,
        environment=None,
        product_line=bundle.product_line,
        capitalization_candidate=bundle.capitalization_candidate,
        initiative_id=bundle.initiative_id,
        initiative_stage=bundle.initiative_stage,
        asset_lifecycle=bundle.asset_lifecycle,
    )
