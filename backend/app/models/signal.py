from dataclasses import dataclass, field


@dataclass
class Signal:
    action: str
    confidence: int

    reasons: list[str] = field(default_factory=list)

    entry: float = 0
    stop_loss: float = 0
    target1: float = 0
    target2: float = 0