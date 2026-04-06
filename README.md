# finops-cost-capitalization-pipeline
End-to-end Analytics Engineering pipeline classifying cloud billing data to identify OPEX and CAPEX (capitalization/amortization) opportunities.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full project plan, including phases,
milestones, issue catalog, architecture, and the ML handoff strategy.

## GitHub Bootstrap

Use the Bash automation scripts to prepare the remote GitHub repository with
labels, milestones, and issues derived from the roadmap.

```bash
bash scripts/setup_labels.sh --repo owner/repo
bash scripts/setup_milestones.sh --repo owner/repo
bash scripts/setup_issues.sh --repo owner/repo
bash scripts/setup_all.sh --repo owner/repo
```

The issue bootstrap reads the issue catalog directly from `ROADMAP.md`, so the
roadmap remains the single source of truth for backlog creation.
