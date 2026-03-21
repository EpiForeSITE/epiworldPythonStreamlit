import importlib.resources
from decimal import ROUND_HALF_EVEN, Decimal, getcontext
from typing import Any

import pandas as pd
from ruamel.yaml import YAML

from epicc.model.base import BaseSimulationModel


class TBIsolationModel(BaseSimulationModel):
    def human_name(self) -> str:
        return "TB Isolation"

    @property
    def model_title(self) -> str:
        return "TB Isolation Cost Calculator"

    @property
    def model_description(self) -> str:
        return "Estimates hospitalization, tracing, and productivity costs for TB isolation scenarios."

    @property
    def scenario_labels(self) -> dict[str, str]:
        return {
            "14_day": "14-day Isolation",
            "5_day": "5-day Isolation",
        }

    def default_params(self) -> dict[str, Any]:
        with (
            importlib.resources.files("epicc.models")
            .joinpath("tb_isolation.yaml")
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

        lbl_14 = label_overrides.get("14_day", self.scenario_labels["14_day"])
        lbl_5 = label_overrides.get("5_day", self.scenario_labels["5_day"])

        def q2(x: Decimal) -> Decimal:
            if abs(x) > 10:
                return x.quantize(one, rounding=ROUND_HALF_EVEN)
            return x.quantize(cent, rounding=ROUND_HALF_EVEN)

        def q2n(x: Decimal) -> Decimal:
            return x.quantize(cent, rounding=ROUND_HALF_EVEN)

        def getp(default: float | int, *names: str) -> Decimal:
            normalized_params = {k.lower(): v for k, v in params.items()}

            for n in names:
                n_lower = n.lower()

                if n_lower in normalized_params and normalized_params[n_lower] != "":
                    return Decimal(str(normalized_params[n_lower]))

                for key, val in normalized_params.items():
                    if f"({n_lower})" in key and val != "":
                        return Decimal(str(val))
            return Decimal(str(default))

        contacts_per_case = getp(0, "Number of contacts for each released TB case")
        prob_latent_if_14day = getp(
            0,
            "Probability that contact develops latent TB if 14-day isolation",
        )
        infectiousness_multiplier = getp(
            1.5,
            "Multiplier for infectiousness with 5-day vs. 14-day isolation",
        )
        workday_ratio = getp(0.714, "Ratio of workdays to total days")

        prob_latent_to_active_2yr = getp(
            0, "prob_latent_to_active_2yr", "First 2 years"
        )
        prob_latent_to_active_lifetime = getp(
            0,
            "prob_latent_to_active_lifetime",
            "Rest of lifetime",
        )

        cost_latent = getp(0, "cost_latent", "Cost of latent TB infection")
        cost_active = getp(0, "cost_active", "Cost of active TB infection")

        isolation_type = int(
            getp(3, "isolation_type", "Isolation type (1=hospital,2=motel,3=home)")
        )
        daily_hosp_cost = getp(0, "isolation_cost", "Daily isolation cost")
        direct_med_cost_day = getp(0, "Direct medical cost of a day of isolation")

        cost_motel_room = getp(0, "Cost of motel room per day")
        hourly_wage_nurse = getp(0, "Hourly wage for nurse")
        time_nurse_checkin = getp(
            0, "Time for nurse to check in w/ pt in motel or home (hrs)"
        )
        hourly_wage_worker = getp(0, "Hourly wage for worker")

        discount_rate = getp(0, "discount_rate", "Discount rate")
        remaining_years = int(getp(40, "remaining_years", "Remaining years of life"))

        if isolation_type == 1:
            daily_cost = (
                direct_med_cost_day if direct_med_cost_day > 0 else daily_hosp_cost
            )
        elif isolation_type == 2:
            daily_cost = cost_motel_room + (hourly_wage_nurse * time_nurse_checkin)
        else:
            daily_cost = hourly_wage_nurse * time_nurse_checkin

        latent_14_day = q2n(contacts_per_case * prob_latent_if_14day)
        latent_5_day = q2n(latent_14_day * infectiousness_multiplier)

        active_14_day = q2n(
            latent_14_day * prob_latent_to_active_2yr
            + latent_14_day
            * (one - prob_latent_to_active_2yr)
            * prob_latent_to_active_lifetime
        )
        active_5_day = q2n(
            latent_5_day * prob_latent_to_active_2yr
            + latent_5_day
            * (one - prob_latent_to_active_2yr)
            * prob_latent_to_active_lifetime
        )

        df_infections = pd.DataFrame(
            {
                "Outcome": ["Latent TB infections", "Active TB disease"],
                lbl_14: [latent_14_day, active_14_day],
                lbl_5: [latent_5_day, active_5_day],
            }
        )

        direct_cost_14_day = q2(daily_cost * Decimal(14))
        direct_cost_5_day = q2(daily_cost * Decimal(5))

        productivity_loss_14_day = q2(
            Decimal(14) * workday_ratio * hourly_wage_worker * Decimal(8)
        )
        productivity_loss_5_day = q2(
            Decimal(5) * workday_ratio * hourly_wage_worker * Decimal(8)
        )

        base = one + discount_rate
        discounted_2yr = (prob_latent_to_active_2yr / Decimal(2)) / (base**1) + (
            (prob_latent_to_active_2yr / Decimal(2)) / (base**2)
        )
        discounted_lifetime = sum(
            (prob_latent_to_active_lifetime / Decimal(remaining_years)) / (base**y)
            for y in range(3, remaining_years + 1)
        )

        sec_cost_per_latent = q2(
            cost_latent + cost_active * (discounted_2yr + discounted_lifetime)
        )

        secondary_cost_14_day = q2(latent_14_day * sec_cost_per_latent)
        secondary_cost_5_day = q2(latent_5_day * sec_cost_per_latent)

        total_14_day = q2(
            direct_cost_14_day + productivity_loss_14_day + secondary_cost_14_day
        )
        total_5_day = q2(
            direct_cost_5_day + productivity_loss_5_day + secondary_cost_5_day
        )

        df_costs = pd.DataFrame(
            {
                "Cost Type": [
                    "Direct cost of isolation",
                    "Lost productivity for index case",
                    "Cost of secondary infections",
                    "Total cost",
                ],
                lbl_14: [
                    direct_cost_14_day,
                    productivity_loss_14_day,
                    secondary_cost_14_day,
                    total_14_day,
                ],
                lbl_5: [
                    direct_cost_5_day,
                    productivity_loss_5_day,
                    secondary_cost_5_day,
                    total_5_day,
                ],
            }
        )

        return {
            "df_infections": df_infections,
            "df_costs": df_costs,
        }

    def build_sections(self, results: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "title": "Number of Secondary Infections",
                "content": [results["df_infections"]],
            },
            {"title": "Costs", "content": [results["df_costs"]]},
        ]
