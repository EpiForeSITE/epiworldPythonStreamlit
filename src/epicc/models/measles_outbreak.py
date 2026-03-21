import importlib.resources
from decimal import ROUND_HALF_EVEN, Decimal, getcontext
from typing import Any

import pandas as pd
from ruamel.yaml import YAML

from epicc.model.base import BaseSimulationModel


class MeaslesOutbreakModel(BaseSimulationModel):
    def human_name(self) -> str:
        return "Measles Outbreak"

    @property
    def model_title(self) -> str:
        return "Measles Outbreak Cost Estimation"

    @property
    def model_description(self) -> str:
        return "Estimates hospitalization, tracing, and productivity costs for measles outbreaks."

    @property
    def scenario_labels(self) -> dict[str, str]:
        return {
            "22_cases": "22 Cases",
            "100_cases": "100 Cases",
            "803_cases": "803 Cases",
        }

    def default_params(self) -> dict[str, Any]:
        with (
            importlib.resources.files("epicc.models")
            .joinpath("measles_outbreak.yaml")
            .open("rb") as f
        ):
            return dict(YAML().load(f))

    def run(
        self,
        params: dict[str, Any],
        label_overrides: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        getcontext().prec = 28
        one = Decimal("1")
        cent = Decimal("0.01")

        if label_overrides is None:
            label_overrides = {}

        lbl_22 = label_overrides.get("22_cases", self.scenario_labels["22_cases"])
        lbl_100 = label_overrides.get("100_cases", self.scenario_labels["100_cases"])
        lbl_803 = label_overrides.get("803_cases", self.scenario_labels["803_cases"])

        def q2(x: Decimal) -> Decimal:
            if abs(x) > 10:
                return x.quantize(one, rounding=ROUND_HALF_EVEN)
            return x.quantize(cent, rounding=ROUND_HALF_EVEN)

        def getp(default: float | int, *names: str) -> Decimal:
            for n in names:
                if n in params and params[n] != "":
                    try:
                        return Decimal(str(params[n]))
                    except Exception:
                        pass
            return Decimal(str(default))

        cost_hosp = getp(0, "Cost of measles hospitalization")
        prop_hosp = getp(0, "Proportion of cases hospitalized")
        missed_ratio = getp(
            1.0,
            "Proportion of quarantine days that would be a missed day of work",
        )
        wage_worker = getp(
            0,
            "Hourly wage of worker (hourly_wage_worker)",
            "Hourly wage for worker",
        )
        wage_tracer = getp(0, "Hourly wage for contract tracer")
        hrs_tracing = getp(0, "Hours of contact tracing per contact")
        contacts = getp(0, "Number of contacts per case")
        vacc_rate = getp(0, "Vaccination rate in community")
        quarantine = int(getp(21, "Length of quarantine (days)"))

        hosp_22 = q2(22 * prop_hosp * cost_hosp)
        hosp_100 = q2(100 * prop_hosp * cost_hosp)
        hosp_803 = q2(803 * prop_hosp * cost_hosp)

        lost_22 = q2(
            22 * contacts * (1 - vacc_rate) * quarantine * missed_ratio * wage_worker
        )
        lost_100 = q2(
            100 * contacts * (1 - vacc_rate) * quarantine * missed_ratio * wage_worker
        )
        lost_803 = q2(
            803 * contacts * (1 - vacc_rate) * quarantine * missed_ratio * wage_worker
        )

        trace_22 = q2(22 * contacts * hrs_tracing * wage_tracer)
        trace_100 = q2(100 * contacts * hrs_tracing * wage_tracer)
        trace_803 = q2(803 * contacts * hrs_tracing * wage_tracer)

        total_22 = q2(hosp_22 + lost_22 + trace_22)
        total_100 = q2(hosp_100 + lost_100 + trace_100)
        total_803 = q2(hosp_803 + lost_803 + trace_803)

        df_costs = pd.DataFrame(
            {
                "Cost Type": [
                    "Hospitalization",
                    "Lost productivity",
                    "Contact tracing",
                    "TOTAL",
                ],
                lbl_22: [hosp_22, lost_22, trace_22, total_22],
                lbl_100: [hosp_100, lost_100, trace_100, total_100],
                lbl_803: [hosp_803, lost_803, trace_803, total_803],
            }
        )

        return {"df_costs": df_costs}

    def build_sections(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"title": "Measles Outbreak Costs", "content": [results["df_costs"]]}]
