from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card

from components.operational_chart import (
    operational_risk_chart,
    lead_time_chart,
    operational_pressure_chart
)

from scripts.data_loader import (
    operational,
    seasonal_risk
)

register_page(
    __name__,
    path="/operational",
    name="Operational Risk"
)

# DATA PREPARATION

data = operational.copy()

latest = data.iloc[-1]

previous = (
    data.iloc[-2]
    if len(data) > 1
    else latest
)

# LATEST METRICS

stockout = float(
    latest["StockOutRate"]
)

returns = float(
    latest["ReturnRate"]
)

lead_time = float(
    latest["Avg_LeadTime"]
)

inventory_risk = str(
    latest["Inventory_Risk"]
)

# PREVIOUS METRICS

previous_stockout = float(
    previous["StockOutRate"]
)

previous_returns = float(
    previous["ReturnRate"]
)

previous_lead_time = float(
    previous["Avg_LeadTime"]
)

# CHANGE CALCULATIONS

stockout_change = (
    (stockout - previous_stockout)
    * 100
)

return_change = (
    (returns - previous_returns)
    * 100
)

lead_time_change = (
    lead_time - previous_lead_time
)

# HISTORICAL EXTREMES

highest_stockout = (
    data["StockOutRate"]
    .max()
    * 100
)

highest_return = (
    data["ReturnRate"]
    .max()
    * 100
)

highest_lead_time = (
    data["Avg_LeadTime"]
    .max()
)

lowest_lead_time = (
    data["Avg_LeadTime"]
    .min()
)

# RISK COLOUR

risk_lower = inventory_risk.lower()

if risk_lower in [
    "high",
    "high risk",
    "critical"
]:

    risk_colour = "#C0392B"

elif risk_lower in [
    "moderate",
    "moderate risk",
    "medium"
]:

    risk_colour = "#F39C12"

else:

    risk_colour = "#2ECC71"

# TREND HELPER

def trend_text(
    change,
    positive_is_bad=True
):

    if abs(change) < 0.01:

        return "Stable vs previous month"

    if positive_is_bad:

        if change > 0:
            return f"▲ +{change:.2f} vs previous month"

        return f"▼ {change:.2f} vs previous month"

    else:

        if change > 0:
            return f"▲ +{change:.2f} vs previous month"

        return f"▼ {change:.2f} vs previous month"

# TREND COLOURS

stockout_trend_colour = (
    "#C0392B"
    if stockout_change > 0
    else "#2ECC71"
)

return_trend_colour = (
    "#C0392B"
    if return_change > 0
    else "#2ECC71"
)

lead_time_trend_colour = (
    "#C0392B"
    if lead_time_change > 0
    else "#2ECC71"
)

# SEASONAL RISK TABLE

seasonal_columns = [
    "Month_Name",
    "Seasonal_Effect",
    "Strategic_Risk"
]


seasonal_display = seasonal_risk[
    seasonal_columns
].copy()

# FORMAT SEASONAL REVENUE EFFECT

def format_revenue_effect(value):

    value = float(value)

    if value < 0:

        return f"-R{abs(value):,.2f}"

    return f"R{value:,.2f}"

# SEASONAL RISK BADGES

def seasonal_badge(risk):

    value = str(risk).strip()

    lower = value.lower()

    if lower in [
        "high",
        "high risk",
        "critical"
    ]:

        return dbc.Badge(
            value,
            color="danger",
            className="px-3 py-2"
        )

    elif lower in [
        "moderate",
        "moderate risk",
        "medium"
    ]:

        return dbc.Badge(
            value,
            color="warning",
            text_color="dark",
            className="px-3 py-2"
        )

    else:

        return dbc.Badge(
            value,
            color="success",
            className="px-3 py-2"
        )

seasonal_rows = []

for _, row in seasonal_display.iterrows():

    revenue_effect = float(
        row["Seasonal_Effect"]
    )

    revenue_colour = (
        "#C0392B"
        if revenue_effect < 0
        else "#0B6E4F"
    )

    seasonal_rows.append(
        html.Tr(
            [
                html.Td(
                    row["Month_Name"],
                    style={
                        "fontWeight": "600"
                    }
                ),

                html.Td(
                    format_revenue_effect(
                        revenue_effect
                    ),
                    style={
                        "fontWeight": "600",
                        "color": revenue_colour
                    }
                ),

                html.Td(
                    seasonal_badge(
                        row["Strategic_Risk"]
                    )
                )
            ]
        )
    )

# LAYOUT

layout = dbc.Container(
    [
        # PAGE HEADER

        html.H1(
            "Operational Risk",
            className="mb-1"
        ),

        html.P(
            "Monitoring inventory availability, returns, supplier lead times and operational pressure.",
            className="text-muted"
        ),

        html.Br(),

        # KPI CARDS

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Stock-Out Rate",
                        f"{stockout * 100:.2f}%",
                        "Latest Month",
                        "#C0392B"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),

                dbc.Col(
                    kpi_card(
                        "Return Rate",
                        f"{returns * 100:.2f}%",
                        "Latest Month",
                        "#F39C12"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),
                dbc.Col(
                    kpi_card(
                        "Average Lead Time",
                        f"{lead_time:.2f} days",
                        "Latest Month",
                        "#1479D2"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),
                dbc.Col(
                    kpi_card(
                        "Inventory Risk",
                        inventory_risk,
                        "Latest Month",
                        risk_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # TREND INSIGHT STRIP

        dbc.Card(
            dbc.CardBody(
                [
                    html.H5(
                        "Latest Operational Movement",
                        className="mb-3",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html.Small(
                                        "Stock-Out Movement",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        trend_text(
                                            stockout_change
                                        ),
                                        style={
                                            "fontWeight": "600",
                                            "color":
                                                stockout_trend_colour
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [
                                    html.Small(
                                        "Return Movement",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        trend_text(
                                            return_change
                                        ),
                                        style={
                                            "fontWeight": "600",
                                            "color":
                                                return_trend_colour
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),
                            dbc.Col(
                                [
                                    html.Small(
                                        "Lead Time Movement",
                                        className="text-muted"
                                    ),

                                    html.Div(
                                        trend_text(
                                            lead_time_change
                                        ),
                                        style={
                                            "fontWeight": "600",
                                            "color":
                                                lead_time_trend_colour
                                        }
                                    )
                                ],
                                xs=12,
                                md=4
                            )
                        ],

                        className="g-4"
                    )
                ]
            ),
            className="shadow-sm"
        ),

        html.Br(),

        # OPERATIONAL RISK TRENDS

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Operational Risk Trends",
                        className="mb-1",
                        style={
                            "color": "#000000"
                        }
                    ),

                    html.P(
                        "Tracking stock-outs and product returns over time.",
                        className="mb-3 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dcc.Graph(

                        id="operational-risk-chart",

                        figure=operational_risk_chart(
                            operational
                        ),

                        config={
                            "displayModeBar": True,
                            "displaylogo": False,
                            "responsive": True
                        }
                    )
                ]
            ),

            className="shadow-sm"
        ),

        html.Br(),

        # LEAD TIME + OPERATIONAL PRESSURE

        dbc.Row(
            [
                # LEAD TIME

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Supplier Lead Time",
                                    className="mb-1",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.P(
                                    "Movement in average supplier delivery time.",
                                    className="mb-2 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                dcc.Graph(
                                    id="lead-time-chart",
                                    figure=lead_time_chart(
                                        operational
                                    ),

                                    config={
                                        "displayModeBar": True,
                                        "displaylogo": False,
                                        "responsive": True
                                    }
                                )
                            ]
                        ),

                        className="shadow-sm"
                    ),

                    xs=12,
                    lg=6
                ),

                # OPERATIONAL PRESSURE

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4(
                                    "Operational Pressure",
                                    className="mb-1",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.P(
                                    "Relative pressure from stock-outs, returns and supplier lead times.",
                                    className="mb-2 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                dcc.Graph(

                                    id="operational-pressure-chart",

                                    figure=operational_pressure_chart(
                                        operational
                                    ),

                                    config={
                                        "displayModeBar": True,
                                        "displaylogo": False,
                                        "responsive": True
                                    }
                                )
                            ]
                        ),

                        className="shadow-sm"
                    ),

                    xs=12,
                    lg=6
                )
            ],

            className="g-4"
        ),

        html.Br(),

        # OPERATIONAL RISK POSITION

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Operational Risk Position",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Current operating conditions compared with the historical range in the dataset.",
                        className="mb-4 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dbc.Row(
                        [
                            # CURRENT STOCK-OUT

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Current Stock-Out Rate",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{stockout * 100:.2f}%",
                                                style={
                                                    "color": "#C0392B"
                                                }
                                            ),

                                            html.P(
                                                f"Historical peak: "
                                                f"{highest_stockout:.2f}%",
                                                className="mb-0",
                                                style={
                                                    "color": "#000000"
                                                }
                                            )
                                        ]
                                    ),

                                    className="border-0 shadow-sm"
                                ),

                                xs=12,
                                md=4
                            ),

                            # CURRENT RETURNS

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Current Return Rate",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{returns * 100:.2f}%",
                                                style={
                                                    "color": "#F39C12"
                                                }
                                            ),

                                            html.P(
                                                f"Historical peak: "
                                                f"{highest_return:.2f}%",
                                                className="mb-0",
                                                style={
                                                    "color": "#000000"
                                                }
                                            )
                                        ]
                                    ),

                                    className="border-0 shadow-sm"
                                ),

                                xs=12,
                                md=4
                            ),

                            # LEAD TIME

                            dbc.Col(
                                dbc.Card(
                                    dbc.CardBody(
                                        [
                                            html.H6(
                                                "Current Lead Time",
                                                style={
                                                    "color": "#061A35"
                                                }
                                            ),

                                            html.H3(
                                                f"{lead_time:.2f} days",
                                                style={
                                                    "color": "#1479D2"
                                                }
                                            ),

                                            html.P(
                                                f"Historical range: "
                                                f"{lowest_lead_time:.2f}–"
                                                f"{highest_lead_time:.2f} days",
                                                className="mb-0",
                                                style={
                                                    "color": "#000000"
                                                }
                                            )
                                        ]
                                    ),

                                    className="border-0 shadow-sm"
                                ),

                                xs=12,
                                md=4
                            )
                        ],

                        className="g-3"
                    )
                ]
            ),

            className="shadow-sm"
        ),

        html.Br(),

        # RISK INTERPRETATION

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Risk Interpretation",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Executive interpretation of the current operating position.",
                        className="mb-3 fst-italic"
                    ),

                    html.Div(
                        [
                            html.Span(
                                "Inventory Risk: ",
                                style={
                                    "fontWeight": "700"
                                }
                            ),

                            html.Span(
                                inventory_risk,
                                style={
                                    "fontWeight": "700",
                                    "color": risk_colour
                                }
                            )
                        ],

                        className="mb-2"
                    ),

                    html.P(
                        (
                            "The current stock-out rate is "
                            f"{stockout * 100:.2f}%, while the return "
                            f"rate is {returns * 100:.2f}%. "
                            f"Average supplier lead time is "
                            f"{lead_time:.2f} days."
                        ),

                        className="mb-2"
                    ),

                    html.P(
                        (
                            "Management attention should focus on "
                            "inventory availability, supplier delivery "
                            "reliability and recurring return patterns "
                            "where these indicators remain elevated."
                        ),

                        className="mb-0"
                    )
                ]
            ),

            className="shadow-sm"
        ),

        html.Br(),

        # SEASONAL RISK

        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Seasonal Risk",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Seasonal patterns that may influence operational planning and inventory decisions.",
                        className="mb-3 fst-italic"
                    ),

                    dbc.Table(
                        [
                            html.Thead(
                                html.Tr(
                                    [
                                        html.Th(
                                            "Month"
                                        ),

                                        html.Th(
                                            "Revenue Effect"
                                        ),

                                        html.Th(
                                            "Strategic Risk"
                                        )
                                    ]
                                )
                            ),
                            html.Tbody(
                                seasonal_rows
                            )
                        ],
                        striped=True,
                        hover=True,
                        bordered=False,
                        responsive=True,
                        size="sm",
                        className="align-middle"
                    )
                ]
            ),

            className="shadow-sm"
        )
    ],

    fluid=True

)