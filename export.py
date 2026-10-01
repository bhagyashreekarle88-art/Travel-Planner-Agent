"""Export a finished plan as a Markdown document the traveller can download."""


def plan_to_markdown(r: dict) -> str:
    s, p, w, it = r["spec"], r["plan"], r["weather"], r["itinerary"]
    c = p["cost"]
    L = [f"# {s['nights']}-night trip to {s['destination']}",
         f"**{s['start_date']:%d %b %Y} to {s['end_date']:%d %b %Y}** | {s['travellers']} traveller(s) | "
         f"{s['style']} | from {s['origin']}", "", r["summary"], "",
         "## Flights",
         f"- Outbound: {p['outbound']['airline']} {p['outbound']['flight_no']}, {p['outbound']['date']} "
         f"{p['outbound']['depart']} -> {p['outbound']['arrive']} ({'non-stop' if not p['outbound']['stops'] else '1 stop'})",
         f"- Return: {p['return']['airline']} {p['return']['flight_no']}, {p['return']['date']} "
         f"{p['return']['depart']} -> {p['return']['arrive']} ({'non-stop' if not p['return']['stops'] else '1 stop'})",
         "", "## Hotel",
         f"- {p['hotel']['name']} ({p['hotel']['stars']} star, rated {p['hotel']['rating']}), {p['hotel']['area']} - "
         f"{p['hotel']['rooms']} room(s) x {p['hotel']['nights']} nights",
         "", "## Budget (INR)", "| Item | Amount |", "|---|---:|"]
    for k, label in [("flights", "Flights"), ("hotel", "Hotel"), ("food_local_transport", "Food & local transport"),
                     ("activities", "Activities & entry fees"), ("contingency", "Contingency (5%)"), ("total", "**Total**")]:
        L.append(f"| {label} | {c[k]:,} |")
    L.append(f"| Budget | {s['budget_inr']:,} |")
    L += ["", f"## Weather outlook ({w['source']})"]
    for d in w["days"]:
        L.append(f"- {d['date']}: {d['condition']}, {d['low_c']}-{d['high_c']} C - {d['advice']}")
    L += ["", "## Day-by-day itinerary"]
    for d in it["days"]:
        L.append(f"### Day {d['day']} - {d['date']} - {d['theme']}")
        for x in d["items"]:
            L.append(f"- **{x['time']}**: {x['activity']}" + (f" - {x['note']}" if x.get("note") else ""))
    if it.get("local_tips"):
        L += ["", "## Local tips"] + [f"- {t}" for t in it["local_tips"]]
    if r.get("suggestions"):
        L += ["", "## How to fit the budget"] + [f"- {t}" for t in r["suggestions"]]
    L += ["", "---", f"_{r['disclaimer']}_"]
    return "\n".join(L)
