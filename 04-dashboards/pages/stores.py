from dash import html, register_page

register_page(
    __name__,
    path="/stores",
    name="Stores"
)

layout = html.Div(

    [

        html.H1("Store Performance"),

        html.Hr(),

        html.P(
            "Store-level performance, profitability, operational risk, and regional comparisons will appear here."
        )

    ],

    style={
        "padding": "30px"
    }

)