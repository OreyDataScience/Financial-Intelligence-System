from dash import html
import dash_bootstrap_components as dbc


def executive_insights(strategic_findings):

    findings = strategic_findings.head(6)

    items = []

    for _, row in findings.iterrows():

        items.append(

            dbc.Alert(

                [

                    html.Strong(
                        f"{row['Strategic_Area']}: "
                    ),

                    html.Span(
                        str(row["Insight"])
                    )

                ],

                color="light",

                className="mb-2"

            )

        )

    return dbc.Card(

        dbc.CardBody(

            [

                html.H4(
                    "Strategic Findings"
                ),

                html.Hr(),

                *items

            ]

        ),

        className="shadow-sm"

    )