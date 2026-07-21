# Architecture Decision Records

Each ADR captures one significant, hard-to-reverse architectural
decision made during the NIFTY Guardian v2 rebuild (`feature/nifty-guardian-v2`),
the context that drove it, and its consequences. They are written after
the fact, once a decision has proven itself across multiple phases -
not proposed speculatively.

| ADR | Title |
| --- | --- |
| [0001](0001-layered-trading-domain-architecture.md) | Layered trading domain architecture |
| [0002](0002-no-buy-sell-or-confidence-scoring-until-the-decision-engine.md) | No BUY/SELL or confidence scoring until the Decision Engine |
| [0003](0003-broker-isolation-via-protocol-seams.md) | Broker isolation via Protocol seams |
| [0004](0004-plugin-architecture-for-strategies.md) | Plugin architecture for strategies |
| [0005](0005-risk-evaluated-independently-of-strategy-validity.md) | Risk evaluated independently of strategy validity |
| [0006](0006-immutable-frozen-domain-models.md) | Immutable, frozen domain models everywhere |
| [0007](0007-minimal-flagged-gap-fixes-to-approved-phases.md) | Minimal, flagged gap-fixes to already-approved phases |
