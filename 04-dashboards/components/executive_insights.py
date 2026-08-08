from dash import html
import dash_bootstrap_components as dbc


def executive_insights(
    revenue,
    forecast,
    margin,
    inventory,
    returns
):

    return dbc.Card(

        dbc.CardBody(

            [

                html.H4("Executive Insights"),

                html.Hr(),

                html.P(
                    f"• Latest revenue recorded: R {revenue:,.0f}"
                ),

                html.P(
                    f"• Next month's forecast: R {forecast:,.0f}"
                ),

                html.P(
                    f"• Average margin: {margin:.1f}%"
                ),

                html.P(
                    f"• Inventory status: {inventory}"
                ),

                html.P(
                    f"• Return rate: {returns*100:.1f}%"
                )

            ]

        ),

        className="shadow-sm h-100"

    )