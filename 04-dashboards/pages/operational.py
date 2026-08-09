from dash import html, dcc, register_page
import dash_bootstrap_components as dbc

from components.cards import kpi_card
from components.operational_chart import (
    operational_risk_chart,
    lead_time_chart
)

from scripts.data_loader import operational, seasonal_risk


register_page(
    __name__,
    path="/operational",
    name="Operational Risk"
)


# ==========================================================
# METRICS
# ==========================================================

latest = operational.iloc[-1]

stockout = latest["StockOutRate"]

returns = latest["ReturnRate"]

lead_time = latest["Avg_LeadTime"]

inventory_risk = latest["Inventory_Risk"]


# ==========================================================
# LAYOUT
# ==========================================================

layout = dbc.Container(

    [

        html.H1(
            "Operational Risk",
            className="mb-1"
        ),

        html.P(
            "Monitoring inventory, returns, supplier lead times and operational risk.",
            className="text-muted"
        ),

        html.Br(),

        # ==================================================
        # KPI CARDS
        # ==================================================

        dbc.Row(

            [

                dbc.Col(

                    kpi_card(
                        "Stock-Out Rate",
                        f"{stockout * 100:.1f}%",
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
                        f"{returns * 100:.1f}%",
                        "Latest Month",
                        "#E67E22"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Average Lead Time",
                        f"{lead_time:.1f}",
                        "Latest Month",
                        "#2E86DE"
                    ),

                    xs=12,
                    sm=6,
                    lg=3

                ),

                dbc.Col(

                    kpi_card(
                        "Inventory Risk",
                        str(inventory_risk),
                        "Latest Month",
                        "#8E44AD"
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
        # OPERATIONAL TRENDS
        # ==================================================

        dbc.Card(

            dbc.CardBody(

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

            ),

            className="shadow-sm"

        ),

        html.Br(),

        # ==================================================
        # LEAD TIME
        # ==================================================

        dbc.Card(

            dbc.CardBody(

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

            ),

            className="shadow-sm"

        ),

        html.Br(),

        # ==================================================
        # RISK SUMMARY
        # ==================================================

        dbc.Card(

            dbc.CardBody(

                [

                    html.H4(
                        "Operational Risk Summary"
                    ),

                    html.Hr(),

                    html.P(
                        f"Current inventory risk classification: "
                        f"{inventory_risk}."
                    ),

                    html.P(
                        f"Current stock-out rate: "
                        f"{stockout * 100:.1f}%."
                    ),

                    html.P(
                        f"Current return rate: "
                        f"{returns * 100:.1f}%."
                    ),

                    html.P(
                        f"Current average lead time: "
                        f"{lead_time:.1f}."
                    )

                ]

            ),

            className="shadow-sm"

        ),

        html.Br(),
        dbc.Card(dbc.CardBody([html.H4("Seasonal Risk"), html.Hr(), dbc.Table.from_dataframe(seasonal_risk[["Month_Name", "Seasonal_Effect", "Strategic_Risk"]], striped=True, hover=True, size="sm")]), className="shadow-sm")

    ],

    fluid=True

)
