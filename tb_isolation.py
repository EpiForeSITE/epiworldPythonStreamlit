from decimal import Decimal, ROUND_HALF_EVEN, getcontext

def run_model(params: dict) -> str:
    """
    TB Isolation simulation
    """

    #Decimal setup
    getcontext().prec = 28
    ONE = Decimal("1")
    CENT = Decimal("0.01")
    TWO_DP = Decimal("0.01")

    def q2(x: Decimal) -> Decimal:
        return x.quantize(CENT, rounding=ROUND_HALF_EVEN)

    def q2n(x: Decimal) -> Decimal:
        """Quantize numbers (counts/probabilities) to 2 dp."""
        return x.quantize(TWO_DP, rounding=ROUND_HALF_EVEN)

    #helper method to tolerate label variants from YAML, returning Decimal
    def getp(default, *names) -> Decimal:
        for n in names:
            if n in params and params[n] != "":
                try:
                    return Decimal(str(params[n]))
                except Exception:
                    pass
        return Decimal(str(default))

    #Extract parameters
    contacts_per_case = getp(0, "Number of contacts for each released TB case")
    prob_latent_if_14day = getp(0, "Probability that contact develops latent TB if 14-day isolation")
    infectiousness_multiplier = getp(1.0, "Multiplier for infectiousness with 5-day vs. 14-day isolation")
    workday_ratio = getp(0.714, "Ratio of workdays to total days")

    prob_latent_to_active_2yr = getp(
        0, "First 2 years (prob_latent_to_active_2yr)", "First 2 years"
    )
    prob_latent_to_active_lifetime = getp(
        0, "Rest of lifetime (prob_latent_to_active_lifetime)",
        "Rest of lifetime if don’t become active in 1st 2 years"
    )

    cost_latent = getp(0, "Cost of latent TB infection (cost_latent)", "Cost of latent TB infection")
    cost_active = getp(0, "Cost of active TB infection (cost_active)", "Cost of active TB infection")
    isolation_cost = getp(0, "Daily isolation cost (isolation_cost)", "Isolation cost", "Direct medical cost of a day of isolation")
    hourly_wage_worker = getp(0, "Hourly wage of worker (hourly_wage_worker)", "Hourly wage for worker")

    discount_rate = getp(0.0, "Discount rate", "discount_rate")
    remaining_years = int(getp(40, "Remaining years", "Remaining years of life", "remaining_years"))

    #Core counts
    latent_14_day = q2n(contacts_per_case * prob_latent_if_14day)
    latent_5_day  = q2n(latent_14_day * infectiousness_multiplier)

    active_14_day = q2n(
        latent_14_day * prob_latent_to_active_2yr
        + latent_14_day * (ONE - prob_latent_to_active_2yr) * prob_latent_to_active_lifetime
    )
    active_5_day = q2n(
        latent_5_day * prob_latent_to_active_2yr
        + latent_5_day * (ONE - prob_latent_to_active_2yr) * prob_latent_to_active_lifetime
    )

    #Costs
    direct_cost_14_day = q2(isolation_cost * Decimal(14))
    direct_cost_5_day  = q2(isolation_cost * Decimal(5))

    productivity_loss_14_day = q2(Decimal(14) * workday_ratio * hourly_wage_worker * Decimal(8))
    productivity_loss_5_day  = q2(Decimal(5)  * workday_ratio * hourly_wage_worker * Decimal(8))

    base = ONE + discount_rate
    discounted_2yr = (prob_latent_to_active_2yr / Decimal(2)) / (base ** 1) \
                   + (prob_latent_to_active_2yr / Decimal(2)) / (base ** 2)
    discounted_lifetime = sum(
        (prob_latent_to_active_lifetime / Decimal(remaining_years)) / (base ** y)
        for y in range(3, remaining_years + 1)
    )

    # per-latent cost
    secondary_infection_cost_per_latent = q2(
        cost_latent + cost_active * (discounted_2yr + discounted_lifetime)
    )

    # totals
    secondary_cost_14_day = q2(latent_14_day * secondary_infection_cost_per_latent)
    secondary_cost_5_day  = q2(latent_5_day  * secondary_infection_cost_per_latent)

    total_14_day = q2(direct_cost_14_day + productivity_loss_14_day + secondary_cost_14_day)
    total_5_day  = q2(direct_cost_5_day  + productivity_loss_5_day  + secondary_cost_5_day)


    #Waiting params
    direct_med_cost = getp(0, "Direct medical cost of a day of isolation")
    cost_motel_room = getp(0, "Cost of motel room per day")
    hourly_wage_nurse = getp(0, "Hourly wage for nurse")
    time_nurse_checkin = getp(0, "Time for nurse to check in w/ pt in motel or home (hrs)")
    hourly_wage_health_worker = getp(0, "Hourly wage for public health worker")
    isolation_type = getp(0, "Isolation type (1=hospital,2=motel,3=home)")

    #HTML table
    def fm(x: Decimal) -> str:
        return f"{x:,.2f}"

    html = f"""
    <style>
        table {{ width: 100%; border-collapse: collapse; font-size: 0.95rem; color: #ffffff; }}
        th {{ background-color: #222; color: #ffffff; text-align: left; padding: 8px; }}
        td {{ padding: 6px 10px; border-top: 1px solid #555555; color: #f0f0f0; }}
        tr.section-header td {{ background-color: #444444; font-weight: bold; color: #ffffff; }}
        tr.indent td:first-child {{ padding-left: 30px; }}
        tr.total td {{ font-weight: bold; border-top: 2px solid #777777; color: #ffffff; }}
    </style>
    <table>
        <thead>
            <tr><th>Outcome</th><th>14-day isolation</th><th>5-day isolation</th></tr>
        </thead>
        <tbody>
            <tr class="section-header"><td colspan="3">Number of secondary infections</td></tr>
            <tr class="indent"><td>Latent</td><td>{fm(latent_14_day)}</td><td>{fm(latent_5_day)}</td></tr>
            <tr class="indent"><td>Active</td><td>{fm(active_14_day)}</td><td>{fm(active_5_day)}</td></tr>

            <tr class="section-header"><td colspan="3">Costs</td></tr>
            <tr class="indent"><td>Direct cost of isolation</td><td>${fm(direct_cost_14_day)}</td><td>${fm(direct_cost_5_day)}</td></tr>
            <tr class="indent"><td>Lost productivity for index case</td><td>${fm(productivity_loss_14_day)}</td><td>${fm(productivity_loss_5_day)}</td></tr>
            <tr class="indent"><td>Cost of secondary infections</td><td>${fm(secondary_cost_14_day)}</td><td>${fm(secondary_cost_5_day)}</td></tr>
            <tr class="indent total"><td>Total cost</td><td>${fm(total_14_day)}</td><td>${fm(total_5_day)}</td></tr>
        </tbody>
    </table>
    """
    return html
