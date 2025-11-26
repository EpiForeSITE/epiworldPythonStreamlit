from decimal import Decimal, ROUND_HALF_EVEN, getcontext
import pandas as pd

"""
Measles outbreak simulation
"""

model_title = "Measles Outbreak Cost Estimation"
model_description = "Estimates hospitalization, tracing, and productivity costs for measles outbreaks."

def run_model(params):

    # Decimal precision
    getcontext().prec = 28
    CENT = Decimal("0.01")

    def q2(x: Decimal) -> Decimal:
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

    # EXTRACT PARAMETERS
    cost_hosp    = getp(0, "Cost of measles hospitalization")
    prop_hosp    = getp(0, "Proportion of cases hospitalized")

    missed_ratio = getp(1.0, "Proportion of quarantine days that would be a missed day of work")
    wage_worker  = getp(0, "Hourly wage of worker (hourly_wage_worker)", "Hourly wage for worker")

    wage_tracer  = getp(0, "Hourly wage for contract tracer")
    hrs_tracing  = getp(0, "Hours of contact tracing per contact")

    contacts     = getp(0, "Number of contacts per case")
    vacc_rate    = getp(0, "Vaccination rate in community")
    quarantine   = int(getp(21, "Length of quarantine (days)"))

    # CORE CALCULATIONS

    # Hospitalizations
    hosp_22  = q2(22  * prop_hosp * cost_hosp)
    hosp_100 = q2(100 * prop_hosp * cost_hosp)
    hosp_803 = q2(803 * prop_hosp * cost_hosp)

    # Lost productivity
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

    # Contact tracing cost
    trace_22 = q2(22  * contacts * hrs_tracing * wage_tracer)
    trace_100 = q2(100 * contacts * hrs_tracing * wage_tracer)
    trace_803 = q2(803 * contacts * hrs_tracing * wage_tracer)

    # Totals
    total_22  = q2(hosp_22 + lost_22 + trace_22)
    total_100 = q2(hosp_100 + lost_100 + trace_100)
    total_803 = q2(hosp_803 + lost_803 + trace_803)

    # DATAFRAME

    df_costs = pd.DataFrame({
        "Cost Type": [
            "Hospitalization",
            "Lost productivity",
            "Contact tracing",
            "TOTAL"
        ],
        "22 Cases":  [
            hosp_22, lost_22, trace_22, total_22
        ],
        "100 Cases": [
            hosp_100, lost_100, trace_100, total_100
        ],
        "803 Cases": [
            hosp_803, lost_803, trace_803, total_803
        ]
    })

    return {
        "df_costs": df_costs
    }

#  BUILD SECTIONS (UI structure)
def build_sections(results):

    df_costs = results["df_costs"]

    sections = [
        {
            "title": "Measles Outbreak Costs",
            "content": [df_costs]
        }
    ]
    return sections
