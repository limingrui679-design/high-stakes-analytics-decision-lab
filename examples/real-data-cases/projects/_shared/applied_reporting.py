"""Case-specific diagnostics, decision thresholds and public research artifacts."""

from applied_metrics import figure
from portfolio_core import sha256, write_json


def markdown_table(columns, rows):
    def fmt(v):
        if v is None:
            return "Not observed"
        if isinstance(v, float):
            return f"{v:,.3f}"
        return str(v)

    return [
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
        *["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows],
        "",
    ]


def extra_evidence(number, result):
    a = result["audit"]
    if number == 16:
        rows = []
        for band, values in a["age_group_crossings_at_130_pct"].items():
            for direction, rec in values.items():
                rows.append((band, direction, rec["estimate"], *rec["normal_95"]))
        return [
            "At 130 mmHg, the following percentages use each age group as its own denominator. Design-based intervals preserve all strata and sampling units.",
            "",
            *markdown_table(["Age", "Direction", "Weighted %", "95% lower", "95% upper"], rows),
        ]
    if number == 17:
        g = a["groups"]["External WESAD"]["coverage_and_error_by_activity"]
        return [
            "The external activity groups share one frozen development threshold. Error is subject-averaged among readable reference windows. Large-error rates count windows with error over 10 bpm.",
            "",
            *markdown_table(
                ["WESAD activity", "Eligible", "Reported %", "MAE (bpm)", "Large error %"],
                [
                    (k, v["eligible"], v["coverage_pct"], v["mae"], v["error_over_10bpm_pct"])
                    for k, v in g.items()
                ],
            ),
        ]
    if number == 18:
        return [
            "The validation period selects a staffing scale using waiting and abandonment jointly. Time from the largest observed half-hour backlog to the first empty boundary is observable only on the days shown.",
            "",
            *markdown_table(
                [
                    "Dispatch",
                    "Two-minute waits among answered (%)",
                    "Median minutes from peak to empty",
                    "Days observed",
                ],
                [
                    (
                        k,
                        a["answered_wait_at_least_120s_pct"][k],
                        v["median_minutes"],
                        v["observable_days"],
                    )
                    for k, v in a["peak_to_empty_minutes"].items()
                ],
            ),
        ]
    if number == 19:
        groups = a["jurisdiction_review"]
        examples = sorted(groups, key=lambda s: (-groups[s]["First release"]["displaced"], s))[:8]
        return [
            "The target is membership in the next published list. The two official columns use different state reporting conventions. Each missed state is charged the actual number of calendar days to the next publication.",
            "",
            *markdown_table(
                [
                    "State/territory",
                    "First-release alerts",
                    "First-release displaced",
                    "Adjusted displaced",
                    "Adjusted missed",
                ],
                [
                    (
                        k,
                        groups[k]["First release"]["raised"],
                        groups[k]["First release"]["displaced"],
                        groups[k]["Shrunk revisions"]["displaced"],
                        groups[k]["Shrunk revisions"]["missed"],
                    )
                    for k in examples
                ],
            ),
        ]
    if number == 20:
        return [
            "Every cached result was checked against a full connection scan and a separately implemented time-dependent label-setting search. A newly boardable connection outside the cached route can improve an arrival. An edited connection invalidates the time prefix from the earliest affected departure.",
            "",
            *markdown_table(
                ["Feed", "Changed labels", "Earliest changed second", "Checkpoint visits"],
                [
                    (
                        k,
                        v["changed_arrival_times"],
                        v["earliest_affected_second"],
                        v["work"].get("Prefix repair", 0),
                    )
                    for k, v in a["versions"].items()
                ],
            ),
        ]
    if number == 21:
        return [
            "For the first arrival of each chosen UTC hour, the table gives the estimated expected gain needed to spend one slot. The values are marginal inventory prices under the learned arrival and score distributions.",
            "",
            *markdown_table(
                ["Hour", "One slot remaining", "Two slots", "Three slots"],
                [
                    (
                        h,
                        *a["reservation_price_by_hour_and_slots"][
                            str(h) if str(h) in a["reservation_price_by_hour_and_slots"] else h
                        ],
                    )
                    for h in (0, 6, 12, 18, 23)
                ],
            ),
        ]
    if number == 22:
        return [
            f"The modeled carrier-to-seller effectiveness threshold at equal unit cost was {a['carrier_to_seller_effectiveness_break_even_at_equal_cost']:.3f}. A trial can measure how often each intervention actually prevents a late delivery. Eligible training labels matured before each quarter.",
            "",
            *markdown_table(
                [
                    "Quarter",
                    "Mature training orders",
                    "Eligible orders",
                    "Slots",
                    "Highest-priority carrier lane",
                ],
                [
                    (
                        r["quarter"],
                        r["mature_training_orders"],
                        r["held_out_orders"],
                        r["slots"],
                        " → ".join(r["priority_lanes"][0]),
                    )
                    for r in a["quarter_splits"]
                ],
            ),
        ]
    if number == 23:
        models = sorted(
            a["by_hardware_model"],
            key=lambda m: -a["by_hardware_model"][m]["Monitored fallback"]["at_risk_device_days"],
        )[:6]
        return [
            f"The model-family holdout was {a['held_out_model']}. The delayed performance gate was active on {len(a['gated_dates'])} dates. The row-level missing-feature fallback was applied on {a['missing_feature_fallback_selections']} selected alerts.",
            "",
            *markdown_table(
                [
                    "Hardware model",
                    "Failure events",
                    "Slots used",
                    "Recall %",
                    "False episodes / 1,000 days",
                    "Median warning days",
                ],
                [
                    (
                        m,
                        *[
                            a["by_hardware_model"][m]["Monitored fallback"][k]
                            for k in (
                                "observable_failures",
                                "alert_slots",
                                "recall_pct",
                                "false_per_1000_device_days",
                                "median_lead_days",
                            )
                        ],
                    )
                    for m in models
                ],
            ),
        ]
    if number == 24:
        return [
            f"An independent OR-Tools {a['solver_version']} VRPTW baseline and a timed relocation search each received {a['seconds_per_method_route']} seconds per route. The stored orders are checked against every stop, service time, window, and return requirement on each offline run.",
            "",
            *markdown_table(
                ["Timed method", "Routes with verified nonnegative slack"],
                a["equal_wall_budget_counts"].items(),
            ),
            "The route audit also records the binding stop or depot return, the best witnessed lower bound, and a separate valid upper bound. An open interval is a candidate for more search. The deterministic comparison uses an equal number of candidate moves.",
            "",
        ]
    if number == 25:
        return [
            "Logged-subset timing compares alternative visit orders on the same historical inspection dates with labels held fixed. The effect of carrying out a different visit schedule would need a prospective evaluation.",
            "",
            *markdown_table(
                [
                    "Rule",
                    "Mean days earlier for critical results",
                    "Full-roster lower %",
                    "Full-roster upper %",
                ],
                [
                    (n, t, a["all_roster_lower_pct"][n], a["all_roster_upper_pct"][n])
                    for n, t in a["mean_days_earlier_logged_critical"].items()
                ],
            ),
        ]
    if number == 26:
        plan = a["planned_experiment"]
        return [
            a["teaching_example"],
            "",
            f"The CSEDM rows cover {a['learners']} learners and {a['public_evaluation_problems']} problems. A first correct attempt with no hint anywhere in the problem is an observable, conservative indicator. The corresponding F1 on the matched records was {a['indicator_no_hint_and_first_correct_f1']:.3f}. The separate Refactory trace supplies the example used in the feedback prototypes.",
            "",
            f"The proposed trial randomizes learners within starting-skill strata. Both variants receive the same 60-second study period and unaided transfer item. The primary outcome is first-attempt transfer accuracy. The illustrative design requires {plan['independent_learners_per_arm']} learners per arm under the specified baseline and target effect, before any recruitment allowance.",
            "",
        ]
    if number == 27:
        return [
            "Gilchrist–Zakrajšek monthly corporate spreads and H.15 Treasury yields classify historical stress months after the fact. Trades use only lagged prices.",
            "",
            *markdown_table(
                [
                    "Observed monthly stress",
                    "Weeks",
                    "Cut-credit return (bp/week)",
                    "Hedge return (bp/week)",
                ],
                [
                    (
                        k,
                        v["Cut credit"]["weeks"],
                        v["Cut credit"]["mean_net_weekly_bps"],
                        v["Hedge rates"]["mean_net_weekly_bps"],
                    )
                    for k, v in a["monthly_regime_returns"].items()
                ],
            ),
        ]
    if number == 28:
        bad = a["excluded_source_days"]
        return [
            f"The raw historical mean was {a['raw_unscreened_pp']:.2f} pp on {a['raw_common_windows']:,} windows. A common gross-error rule excludes an authority-day from both forecasts when any input exceeds {a['gross_error_screen_mw']:,} MW. There were {len(bad)} flagged records. The affected observed and lagged dates remain traceable.",
            "",
            *markdown_table(
                ["Authority", "Date", "Largest hourly MW", "Unscreened paired loss (pp)"],
                [
                    (x["authority"], x["day"], x["max_input_MW"], x["unfiltered_difference_pp"])
                    for x in bad
                ],
            ),
            *markdown_table(
                ["Interval method", "Lower (pp)", "Upper (pp)"],
                [(k, *v) for k, v in a["intervals"].items()],
            ),
        ]
    if number == 29:
        val = a["valuation"]
        return [
            a["audited_note"],
            "",
            *markdown_table(
                ["Next-year earnings model", "MAE (% of opening assets)"],
                a["earnings_target_mae_pct"].items(),
            ),
            f"The Apple valuation uses filing {val['accession']}. A one-time trade-receivable loss is charged in year one and discounted at 10%. The baseline fixes book value under full payout with residual-income persistence of 0.6.",
            "",
            *markdown_table(
                ["Uncollected fraction", "Scenario equity value (USD millions)"],
                val["collection_sensitivity_usd_m"].items(),
            ),
        ]
    return [
        f"The reverse index required {a['indexed_recomputes']:,} geometry evaluations versus {a['full_recomputes']:,} under full reconstruction. {a['geometry_row_writes']} actual changed geometries were written to version history. A separate database reader held the previous version through {a['pinned_reader_checks']} commits. A writer process was also terminated with its transaction open and the last committed sequence verified.",
        "",
    ]


def decision_figures(number, r):
    a = r["audit"]

    def chart(title, units, vals, reason):
        return figure(title, units, vals, reason)

    if number == 18:
        return [
            chart(
                "Flexible reserve starts and stops",
                "Mean switches per morning",
                a["switches"],
                "Each policy pays for the same reserve time. Frequent changes carry additional organizational cost.",
            ),
            chart(
                "Peak-load stress with a switching charge",
                "Loss in abandonment percentage-point equivalents",
                {
                    m: v["0.25"]
                    for m, v in a["stress_loss_abandonment_pp_plus_cost_per_switch"]["1.3"].items()
                },
                "30% more arrivals in each sampled day's busiest period; each switch costs 0.25 percentage-point equivalents.",
            ),
        ]
    if number == 21:
        stats = a["policy_totals"]
        n = a["days"] * a["capacity"]
        return [
            chart(
                "Slots left idle at close",
                "Slots",
                {m: n - v["spent"] for m, v in stats.items()},
                "The committed calendar offers the same daily ceiling to every rule.",
            ),
            chart(
                "Gap to the score-aware hindsight ranking",
                "Captured events relative to hindsight",
                {
                    m: v["hits"] - stats["Future scores"]["hits"]
                    for m, v in stats.items()
                    if not m.startswith("Future")
                },
                "Score hindsight knows future scores but has no access to realized labels when ranking.",
            ),
        ]
    if number == 22:
        return [
            chart(
                "Historical stages of delivery delay",
                "Single-item orders",
                a["quadrants"],
                "Carrier handoff deadline and promised delivery date define the four cells.",
            ),
            chart(
                "Where the reviewed late orders occurred",
                "Late orders in the same fixed budget",
                {m: v["end"] for m, v in a["policies"].items()},
                "These are retrospectively covered late orders; intervention efficacy is a separate quantity.",
            ),
        ]
    if number == 24:
        return [
            chart(
                "Independent depot check",
                "Witnessed nonnegative routes",
                a["station_witness_counts"],
                "The DBO3 depot is held out of design choices.",
            ),
            chart(
                "Independent time-budget comparison",
                "Witnessed nonnegative routes",
                a["equal_wall_budget_counts"],
                "Wall-clock budget per method and route is fixed; each returned order is replayed offline.",
            ),
        ]
    if number == 25:
        return [
            chart(
                "Finding critical violations earlier on the logged subset",
                "Mean days earlier than historical",
                a["mean_days_earlier_logged_critical"],
                "Historical time slots and outcomes are held fixed in this comparison.",
            ),
            chart(
                "Minimum possible full-roster critical yield",
                "Percent of selected inspections",
                a["all_roster_lower_pct"],
                "Treat all unobserved outcomes as negative for the lower bound. The accompanying evidence report provides upper bounds.",
            ),
        ]
    if number == 27:
        return [
            chart(
                "Implementation cost exposure",
                "Annual one-way absolute traded weight",
                a["annualized_one_way_turnover"],
                "The explicit one-way trading cost is applied to the absolute change in each leg.",
            ),
            chart(
                "Risk-off performance during the credit crisis",
                "Net percent over the stated window",
                a["regimes"]["Credit crisis"],
                "Reported on the common historical calendar for all three portfolios.",
            ),
        ]
    return []


def decision_brief(project, d, r, render):
    charts = decision_figures(d["number"], r)
    if not charts:
        return
    root = project / "outputs/decision/report"
    figs = root / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    config = {
        "owner": d["owner"],
        "decision_status": d["endpoint"],
        "observed_evidence": r["conclusion"],
        "conditional_action": r["next_decision"],
        "claim_boundary": d["boundary"],
        "analytical_results_sha256": sha256(project / "outputs/results.json"),
    }
    write_json(root / "decision-results.json", config)
    lines = [
        "# " + d["title"],
        "",
        "## Decision brief",
        "",
        f"**For the {d['owner'].lower()}.** {r['next_decision']}",
        "",
        r["conclusion"],
        "",
    ]
    cmap = []
    for i, ch in enumerate(charts, 1):
        name = f"decision-{i}.svg"
        (figs / name).write_text(render(ch))
        lines.extend(
            [
                f"## {ch['title']}",
                "",
                ch["note"],
                "",
                f"![{ch['title']}](figures/{name})",
                "",
                *markdown_table(["Comparison", ch["unit"]], ch["values"].items()),
            ]
        )
        cmap.append(
            dict(
                path="figures/" + name,
                question=ch["title"],
                supported_finding=ch["note"],
                interpretation_boundary=d["boundary"],
            )
        )
    lines.extend(
        [
            d["boundary"],
            "",
            "[Evaluation report](../../report.md) · [Decision record](decision-results.json)",
            "",
        ]
    )
    (root / "decision-report.md").write_text("\n".join(lines))
    write_json(figs / "chart-map.json", {"charts": cmap})
