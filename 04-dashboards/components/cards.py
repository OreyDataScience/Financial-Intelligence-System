from dash import html
import dash_bootstrap_components as dbc


def kpi_card(title, value, subtitle, colour):

    return dbc.Card(

        dbc.CardBody(

            [

                html.P(
                    title,
                    className="text-muted"
                ),

                html.H2(
                    value,
                    style={
                        "color": colour,
                        "fontWeight": "700"
                    }
                ),

                html.Small(
                    subtitle,
                    className="text-muted"
                )

            ]

        ),

        style={

            "borderRadius": "16px",
            "border": "none",
            "boxShadow": "0px 5px 15px rgba(0,0,0,.08)"

        }

    )