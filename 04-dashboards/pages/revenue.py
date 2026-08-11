from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.charts import revenue_chart

from scripts.data_loader import monthly, forecast
from scripts.utils import format_currency


register_page(
    __name__,
    path="/revenue",
    name="Revenue"
)


# ==========================================================
# DATA PREPARATION
# ==========================================================

data = monthly.copy()

latest = data.iloc[-1]

previous = (
    data.iloc[-2]
    if len(data) > 1
    else latest
)

forecast_next = forecast.iloc[0]


# ==========================================================
# CURRENT METRICS
# ==========================================================

revenue = float(
    latest["Revenue"]
)

profit = float(
    latest["Profit"]
)

margin = float(
    latest["Avg_Margin"]
)

forecast_revenue = float(
    forecast_next["Revenue_Forecast"]
)


# ==========================================================
# PREVIOUS METRICS
# ==========================================================

previous_revenue = float(
    previous["Revenue"]
)

previous_profit = float(
    previous["Profit"]
)

previous_margin = float(
    previous["Avg_Margin"]
)


# ==========================================================
# GROWTH CALCULATIONS
# ==========================================================

if previous_revenue != 0:

    growth = (
        (revenue - previous_revenue)
        / previous_revenue
    ) * 100

else:

    growth = 0


if previous_profit != 0:

    profit_change = (
        (profit - previous_profit)
        / abs(previous_profit)
    ) * 100

else:

    profit_change = 0


margin_change = (
    margin - previous_margin
) * 100


# ==========================================================
# FORECAST ANALYSIS
# ==========================================================

if revenue != 0:

    forecast_growth = (
        (forecast_revenue - revenue)
        / revenue
    ) * 100

else:

    forecast_growth = 0


# ==========================================================
# HISTORICAL REVENUE METRICS
# ==========================================================

historical_high = float(
    data["Revenue"].max()
)

historical_low = float(
    data["Revenue"].min()
)

average_monthly_revenue = float(
    data["Revenue"].mean()
)

average_monthly_profit = float(
    data["Profit"].mean()
)


# ==========================================================
# PROFITABILITY METRICS
# ==========================================================

total_revenue = float(
    data["Revenue"].sum()
)

total_profit = float(
    data["Profit"].sum()
)


# ==========================================================
# DYNAMIC COLOURS
# ==========================================================

profit_colour = (
    "#2ECC71"
    if profit >= 0
    else "#C0392B"
)

growth_colour = (
    "#2ECC71"
    if growth >= 0
    else "#C0392B"
)

forecast_colour = (
    "#2ECC71"
    if forecast_growth >= 0
    else "#C0392B"
)

margin_colour = (
    "#2ECC71"
    if margin >= 0
    else "#C0392B"
)


# ==========================================================
# TREND TEXT HELPER
# ==========================================================

def change_text(
    change,
    positive_is_good=True
):

    if abs(change) < 0.01:

        return "Stable vs previous month"

    if positive_is_good:

        if change > 0:

            return (
                f"▲ +{change:.2f}% "
                "vs previous month"
            )

        return (
            f"▼ {change:.2f}% "
            "vs previous month"
        )

    else:

        if change > 0:

            return (
                f"▲ +{change:.2f}% "
                "vs previous month"
            )

        return (
            f"▼ {change:.2f}% "
            "vs previous month"
        )


# ==========================================================
# FORECAST INTERPRETATION
# ==========================================================

if forecast_growth > 5:

    forecast_message = (
        "The next-month forecast indicates strong "
        "revenue expansion relative to the current month."
    )

elif forecast_growth > 0:

    forecast_message = (
        "The next-month forecast indicates moderate "
        "revenue growth relative to the current month."
    )

elif forecast_growth < -5:

    forecast_message = (
        "The next-month forecast indicates a material "
        "revenue decline and should receive management attention."
    )

else:

    forecast_message = (
        "The next-month forecast indicates relatively "
        "stable revenue performance."
    )


# ==========================================================
# PERFORMANCE INTERPRETATION
# ==========================================================

if growth > 0 and profit > 0:

    performance_message = (
        "Revenue is growing while the business remains profitable, "
        "indicating positive current financial momentum."
    )

elif growth > 0 and profit < 0:

    performance_message = (
        "Revenue is increasing, but the latest month remains "
        "loss-making. Growth should therefore be assessed "
        "alongside cost and margin performance."
    )

elif growth < 0 and profit > 0:

    performance_message = (
        "Revenue has declined from the previous month, although "
        "the business remains profitable."
    )

else:

    performance_message = (
        "Both revenue growth and profitability require attention "
        "in the latest month."
    )


# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(
    [

        # ==================================================
        # HEADER
        # ==================================================

        html.H1(
            "Revenue Intelligence",
            className="mb-1"
        ),

        html.P(
            "Revenue performance, profitability, growth trends and forward-looking revenue expectations.",
            className="text-muted"
        ),

        html.Br(),


        # ==================================================
        # KPI CARDS
        # ==================================================

        dbc.Row(
            [

                # LATEST REVENUE

                dbc.Col(
                    kpi_card(
                        "Latest Revenue",
                        format_currency(
                            revenue
                        ),
                        "Current Month",
                        "#1479D2"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),


                # PROFIT

                dbc.Col(
                    kpi_card(
                        "Profit",
                        format_currency(
                            profit
                        ),
                        "Current Month",
                        profit_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),


                # MARGIN

                dbc.Col(
                    kpi_card(
                        "Profit Margin",
                        f"{margin * 100:.2f}%",
                        "Current Month",
                        margin_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),


                # GROWTH

                dbc.Col(
                    kpi_card(
                        "Revenue Growth",
                        f"{growth:.2f}%",
                        "Month-on-Month",
                        growth_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                )

            ],

            className="g-4"
        ),

        html.Br(),


        # ==================================================
        # SECONDARY KPI ROW
        # ==================================================

        dbc.Row(
            [

                # FORECAST

                dbc.Col(
                    kpi_card(
                        "Next-Month Forecast",
                        format_currency(
                            forecast_revenue
                        ),
                        f"{forecast_growth:+.2f}% vs Current",
                        forecast_colour
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),


                # AVERAGE REVENUE

                dbc.Col(
                    kpi_card(
                        "Average Monthly Revenue",
                        format_currency(
                            average_monthly_revenue
                        ),
                        "Historical Average",
                        "#2467A5"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),


                # HISTORICAL HIGH

                dbc.Col(
                    kpi_card(
                        "Revenue High",
                        format_currency(
                            historical_high
                        ),
                        "Historical Peak",
                        "#2EAD76"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                ),


                # HISTORICAL LOW

                dbc.Col(
                    kpi_card(
                        "Revenue Low",
                        format_currency(
                            historical_low
                        ),
                        "Historical Minimum",
                        "#E97A4A"
                    ),

                    xs=12,
                    sm=6,
                    lg=3
                )

            ],

            className="g-4"
        ),

        html.Br(),


        # ==================================================
        # REVENUE + FORECAST CHART
        # ==================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H4(
                        "Revenue Trend & Forecast",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Historical revenue performance with the forward revenue forecast.",
                        className="mb-3 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dcc.Graph(
                        id="revenue-intelligence-chart",

                        figure=revenue_chart(
                            monthly,
                            forecast
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


        # ==================================================
        # CURRENT PERFORMANCE + FORECAST OUTLOOK
        # ==================================================

        dbc.Row(
            [

                # CURRENT PERFORMANCE

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [

                                html.H4(
                                    "Current Revenue Performance",
                                    className="mb-1",
                                    style={
                                        "color": "#061A35",
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    "Latest financial movement compared with the previous month.",
                                    className="mb-3 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.Div(
                                    [
                                        html.Small(
                                            "Revenue Movement",
                                            className="text-muted"
                                        ),

                                        html.Div(
                                            change_text(
                                                growth,
                                                positive_is_good=True
                                            ),
                                            style={
                                                "fontWeight": "700",
                                                "color": growth_colour
                                            }
                                        )
                                    ],

                                    className="mb-3"
                                ),

                                html.Div(
                                    [
                                        html.Small(
                                            "Profit Movement",
                                            className="text-muted"
                                        ),

                                        html.Div(
                                            change_text(
                                                profit_change,
                                                positive_is_good=True
                                            ),
                                            style={
                                                "fontWeight": "700",
                                                "color": (
                                                    "#2ECC71"
                                                    if profit_change >= 0
                                                    else "#C0392B"
                                                )
                                            }
                                        )
                                    ],

                                    className="mb-3"
                                ),

                                html.Div(
                                    [
                                        html.Small(
                                            "Margin Movement",
                                            className="text-muted"
                                        ),

                                        html.Div(
                                            (
                                                f"▲ +{margin_change:.2f} "
                                                "percentage points"
                                                if margin_change > 0
                                                else
                                                f"▼ {margin_change:.2f} "
                                                "percentage points"
                                            )
                                            if abs(margin_change) >= 0.01
                                            else
                                            "Stable vs previous month",

                                            style={
                                                "fontWeight": "700",
                                                "color": (
                                                    "#2ECC71"
                                                    if margin_change >= 0
                                                    else "#C0392B"
                                                )
                                            }
                                        )
                                    ],

                                    className="mb-3"
                                ),

                                html.Hr(),

                                html.P(
                                    performance_message,
                                    className="mb-0"
                                )

                            ]
                        ),

                        className="shadow-sm h-100"
                    ),

                    xs=12,
                    lg=6
                ),


                # FORECAST OUTLOOK

                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [

                                html.H4(
                                    "Forecast Outlook",
                                    className="mb-1",
                                    style={
                                        "color": "#061A35",
                                        "fontWeight": "700"
                                    }
                                ),

                                html.P(
                                    "Forward-looking revenue expectation based on the forecasting model.",
                                    className="mb-3 fst-italic",
                                    style={
                                        "color": "#000000"
                                    }
                                ),

                                html.Div(
                                    [
                                        html.Small(
                                            "Current Revenue",
                                            className="text-muted"
                                        ),

                                        html.H5(
                                            format_currency(
                                                revenue
                                            ),
                                            className="mb-3"
                                        )
                                    ]
                                ),

                                html.Div(
                                    [
                                        html.Small(
                                            "Forecast Revenue",
                                            className="text-muted"
                                        ),

                                        html.H4(
                                            format_currency(
                                                forecast_revenue
                                            ),
                                            style={
                                                "color": forecast_colour,
                                                "fontWeight": "700"
                                            }
                                        )
                                    ]
                                ),

                                html.Hr(),

                                html.Div(
                                    [
                                        html.Small(
                                            "Forecast Movement",
                                            className="text-muted"
                                        ),

                                        html.Div(
                                            (
                                                f"▲ +{forecast_growth:.2f}%"
                                                if forecast_growth >= 0
                                                else
                                                f"▼ {forecast_growth:.2f}%"
                                            ),

                                            style={
                                                "fontWeight": "700",
                                                "color": forecast_colour
                                            }
                                        )
                                    ],

                                    className="mb-3"
                                ),

                                html.P(
                                    forecast_message,
                                    className="mb-0"
                                )

                            ]
                        ),

                        className="shadow-sm h-100"
                    ),

                    xs=12,
                    lg=6
                )

            ],

            className="g-4"
        ),

        html.Br(),


        # ==================================================
        # HISTORICAL REVENUE POSITION
        # ==================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H4(
                        "Historical Revenue Position",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Current revenue compared with the historical performance range.",
                        className="mb-4 fst-italic",
                        style={
                            "color": "#000000"
                        }
                    ),

                    dbc.Row(
                        [

                            dbc.Col(
                                [
                                    html.Small(
                                        "Current Revenue",
                                        className="text-muted"
                                    ),

                                    html.H4(
                                        format_currency(
                                            revenue
                                        ),
                                        style={
                                            "color": "#1479D2",
                                            "fontWeight": "700"
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [
                                    html.Small(
                                        "Historical High",
                                        className="text-muted"
                                    ),

                                    html.H4(
                                        format_currency(
                                            historical_high
                                        ),
                                        style={
                                            "color": "#2ECC71",
                                            "fontWeight": "700"
                                        }
                                    )
                                ],

                                xs=12,
                                md=4
                            ),

                            dbc.Col(
                                [
                                    html.Small(
                                        "Historical Low",
                                        className="text-muted"
                                    ),

                                    html.H4(
                                        format_currency(
                                            historical_low
                                        ),
                                        style={
                                            "color": "#E97A4A",
                                            "fontWeight": "700"
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


        # ==================================================
        # MANAGEMENT INTERPRETATION
        # ==================================================

        dbc.Card(
            dbc.CardBody(
                [

                    html.H4(
                        "Revenue Interpretation",
                        className="mb-1",
                        style={
                            "color": "#061A35",
                            "fontWeight": "700"
                        }
                    ),

                    html.P(
                        "Executive interpretation of the current revenue position.",
                        className="mb-3 fst-italic"
                    ),

                    html.P(
                        (
                            f"The business generated "
                            f"{format_currency(revenue)} in the latest month, "
                            f"representing a {growth:.2f}% change from the "
                            f"previous month."
                        ),

                        className="mb-2"
                    ),

                    html.P(
                        (
                            f"Current profit is "
                            f"{format_currency(profit)}, with a reported "
                            f"margin of {margin * 100:.2f}%."
                        ),

                        className="mb-2"
                    ),

                    html.P(
                        (
                            f"The next-month forecast is "
                            f"{format_currency(forecast_revenue)}, which is "
                            f"{forecast_growth:+.2f}% relative to current "
                            f"revenue."
                        ),

                        className="mb-2"
                    ),

                    html.P(
                        (
                            "Management should evaluate revenue growth "
                            "together with profitability and margin rather "
                            "than relying on revenue growth alone."
                        ),

                        className="mb-0"
                    )

                ]
            ),

            className="shadow-sm"
        )

    ],

    fluid=True
)