from decimal import Decimal, ROUND_HALF_EVEN, getcontext
import pandas as pd

"""
Measles outbreak simulation
"""

model_title = "Measles Outbreak Cost Estimation"
model_description = "Estimates hospitalization, tracing, and productivity costs for measles outbreaks."

SCENARIO_LABELS = {
    "22_cases": "22 Cases",
    "100_cases": "100 Cases",
    "803_cases": "803 Cases"
}


def run_model(params, label_overrides: dict = None):
    getcontext().prec = 28
    ONE = Decimal("1")
    CENT = Decimal("0.01")

    if label_overrides is None:
        label_overrides = {}

    lbl_22 = label_overrides.get("22_cases", SCENARIO_LABELS["22_cases"])
    lbl_100 = label_overrides.get("100_cases", SCENARIO_LABELS["100_cases"])
    lbl_803 = label_overrides.get("803_cases", SCENARIO_LABELS["803_cases"])

    def q2(x: Decimal) -> Decimal:
        """
        Conditional rounding:
        - If absolute value > 10, round to whole number (0 decimal places).
        - Otherwise, round to 2 decimal places.
        """
        if abs(x) > 10:
            return x.quantize(ONE, rounding=ROUND_HALF_EVEN)
        return x.quantize(CENT, rounding=ROUND_HALF_EVEN)

    def getp(default, *names):
        """
        Helper that searches for alternative parameter labels.
        Returns Decimal.
        """
        for n in names:
            if n in params and params[n] != "":
                try:
                    return Decimal(str(params[n]))
                except:
                    pass
        return Decimal(str(default))

    # extract parameters
    cost_hosp = getp(0, "Cost of measles hospitalization")
    prop_hosp = getp(0, "Proportion of cases hospitalized")

    missed_ratio = getp(1.0, "Proportion of quarantine days that would be a missed day of work")
    wage_worker = getp(0, "Hourly wage of worker (hourly_wage_worker)", "Hourly wage for worker")

    wage_tracer = getp(0, "Hourly wage for contract tracer")
    hrs_tracing = getp(0, "Hours of contact tracing per contact")

    contacts = getp(0, "Number of contacts per case")
    vacc_rate = getp(0, "Vaccination rate in community")
    quarantine = int(getp(21, "Length of quarantine (days)"))

    # core calculations

    # hospitalizations
    hosp_22 = q2(22 * prop_hosp * cost_hosp)
    hosp_100 = q2(100 * prop_hosp * cost_hosp)
    hosp_803 = q2(803 * prop_hosp * cost_hosp)

    # lost productivity
    lost_22 = q2(
        22 * contacts * (1 - vacc_rate) * quarantine *
        missed_ratio * wage_worker
    )
    lost_100 = q2(
        100 * contacts * (1 - vacc_rate) * quarantine *
        missed_ratio * wage_worker
    )
    lost_803 = q2(
        803 * contacts * (1 - vacc_rate) * quarantine *
        missed_ratio * wage_worker
    )

    # contact tracing cost
    trace_22 = q2(22 * contacts * hrs_tracing * wage_tracer)
    trace_100 = q2(100 * contacts * hrs_tracing * wage_tracer)
    trace_803 = q2(803 * contacts * hrs_tracing * wage_tracer)

    # totals
    total_22 = q2(hosp_22 + lost_22 + trace_22)
    total_100 = q2(hosp_100 + lost_100 + trace_100)
    total_803 = q2(hosp_803 + lost_803 + trace_803)

    # dataframe
    df_costs = pd.DataFrame({
        "Cost Type": [
            "Hospitalization",
            "Lost productivity",
            "Contact tracing",
            "TOTAL"
        ],
        lbl_22: [
            hosp_22, lost_22, trace_22, total_22
        ],
        lbl_100: [
            hosp_100, lost_100, trace_100, total_100
        ],
        lbl_803: [
            hosp_803, lost_803, trace_803, total_803
        ]
    })

    return {
        "df_costs": df_costs
    }


# ui
def build_sections(results):
    df_costs = results["df_costs"]

    sections = [
        {
            "title": "Measles Outbreak Costs",
            "content": [df_costs]
        }
    ]
    return sections
