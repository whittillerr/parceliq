from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.solver.models import (
    BindingConstraint,
    DevelopmentEnvelope,
    ScenarioOutput,
    SolverInput,
)


class BaseSolverEngine(ABC):

    @abstractmethod
    def calculate_envelope(
        self, district_data: Dict[str, Any], solver_input: SolverInput
    ) -> DevelopmentEnvelope:
        ...

    @abstractmethod
    def calculate_scenarios(
        self, envelope: DevelopmentEnvelope, solver_input: SolverInput
    ) -> List[ScenarioOutput]:
        ...

    @abstractmethod
    def identify_binding_constraints(
        self, envelope: DevelopmentEnvelope, solver_input: SolverInput
    ) -> List[BindingConstraint]:
        ...
