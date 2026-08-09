from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.charts import revenue_chart
from components.executive_insights import executive_insights
from components.recommended_actions import recommended_actions_panel

from scripts.data_loader import (
    monthly,
    forecast,
    operational_summary,
    strategic_findings,
    recommended_actions,
    needs_attention,
)

from scripts.utils import format_currency

register_page(
    __name__,
    path="/",
    name="Executive",
)

# ==========================================================
# METRICS
# ==========================================================

latest = monthly.iloc[-1]

revenue = latest["Revenue"]
profit = latest["Profit"]
margin = latest["Avg_Margin"]
stockout = latest["StockOutRate"]
returns = latest["ReturnRate"]

forecast_revenue = forecast.iloc[0]["Revenue_Forecast"]

profit_colour = "#2EAD76" if profit >= 0 else "#D84D5A"
margin_colour = "#2EAD76" if margin >= 0 else "#D84D5A"

# ==========================================================
# NEEDS ATTENTION PANEL
# ==========================================================

def needs_attention_panel(items):

    cards = []
    for _, row in items.head(3).iterrows():

        description = row["Description"] if "Description" in row and row["Description"] else None

        card_body_children = [
            html.Div(
                str(int(row["Count"])),
                style={
                    "fontSize": "1.75rem",
                    "fontWeight": "800",
                    "color": "#1479D2",
                    "lineHeight": "1.1",
                },
            ),

            html.Div(
                str(row["Area"]),
                style={
                    "fontSize": "0.95rem",
                    "fontWeight": "600",
                    "marginTop": "4px",
                    "marginBottom": "4px",
                },
            ),
        ]

        if description:
            card_body_children.append(
                html.Div(
                    description,
                    style={
                        "fontSize": "0.75rem",
                        "color": "#8A97A8",
                        "marginBottom": "10px",
                    },
                )
            )

        else:
            card_body_children.append(
                html.Div(
                    style={"marginBottom": "10px"},
                )
            )

        card_body_children.append(
            dcc.Link(
                dbc.Button(
                    "View details",
                    size="sm",
                    outline=True,
                    color="primary",
                    className="mt-auto",
                    style={
                        "fontSize": "0.75rem",
                        "fontWeight": "600",
                    },
                ),

                href=str(row["Route"]),
                style={"textDecoration": "none"},
            )
        )

        cards.append(
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        card_body_children,
                        className="d-flex flex-column",
                        style={"height": "100%"},
                    ),

                    style={
                        "backgroundColor": "#F4F7FB",
                        "border": "1px solid #E2EDF8",
                        "borderRadius": "10px",
                        "height": "100%",
                    },
                ),

                xs=12,
                md=4,
            )
        )

    return html.Div(
        [
            html.H5(
                "Needs Attention",
                className="mb-1",
                style={"color": "#FFFFFF"},
            ),

            html.Small(
                "Items requiring follow-up",
                className="text-muted d-block mb-3",
            ),

            dbc.Row(
                cards,
                className="g-3",
            ),
        ]
    )

# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(
    [
        html.H1(
            "Executive Dashboard",
            className="mb-0",
        ),

        html.P(
            "Financial performance, forecast outlook and the actions that need leadership attention.",
            className="text-muted mb-3",
        ),

        # ==================================================
        # KPI CARDS
        # ==================================================

        dbc.Row(
            [
                dbc.Col(
                    kpi_card(
                        "Revenue",
                        format_currency(revenue),
                        "Latest Month",
                        "#1479D2",
                    ),
                    xs=6,
                    lg=2,
                ),

                dbc.Col(
                    kpi_card(
                        "Profit",
                        format_currency(profit),
                        "Latest Month",
                        profit_colour,
                    ),
                    xs=6,
                    lg=2,
                ),

                dbc.Col(
                    kpi_card(
                        "Margin",
                        f"{margin:.1f}%",
                        "Latest Month",
                        margin_colour,
                    ),
                    xs=6,
                    lg=2,
                ),

                dbc.Col(
                    kpi_card(
                        "Forecast",
                        format_currency(forecast_revenue),
                        "Next Month",
                        "#2467A5",
                    ),
                    xs=6,
                    lg=2,
                ),

                dbc.Col(
                    kpi_card(
                        "Stock-Out Rate",
                        f"{stockout * 100:.1f}%",
                        "Latest Month",
                        "#E97A4A",
                    ),
                    xs=6,
                    lg=2,
                ),

                dbc.Col(
                    kpi_card(
                        "Returns Rate",
                        f"{returns * 100:.1f}%",
                        "Latest Month",
                        "#D84D5A",
                    ),
                    xs=6,
                    lg=2,
                ),
            ],

            className="g-3 mb-3",
        ),

        # ==================================================
        # FORECAST CHART + STRATEGIC FINDINGS
        # ==================================================

        dbc.Row(
            [
                # Aligns with KPI cards 1–4
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            dcc.Graph(
                                figure=revenue_chart(
                                    monthly,
                                    forecast,
                                ),

                                config={
                                    "displayModeBar": True,
                                    "displaylogo": False,
                                    "responsive": True,
                                },

                                style={
                                    "height": "100%",
                                },
                            ),

                            style={
                                "height": "100%",
                            },
                        ),

                        className="shadow-sm h-100",
                    ),
                    lg=8,
                ),

                # Aligns with KPI cards 5–6
                dbc.Col(
                    executive_insights(
                        strategic_findings.head(3)
                    ),

                    lg=4,
                    className="h-100",
                ),
            ],

            className="g-3 mb-3",
        ),

        # ==================================================
        # NEEDS ATTENTION 
        # ==================================================

        dbc.Row(
            dbc.Col(
                needs_attention_panel(
                    needs_attention
                ),
                lg=12,
            ),

            className="g-3 mb-3",
        ),

        # ==================================================
        # RECOMMENDED ACTIONS
        # ==================================================

        recommended_actions_panel(

            recommended_actions[
                recommended_actions["Audience"] == "SME"
            ]
        ),
    ],

    fluid=True,
)