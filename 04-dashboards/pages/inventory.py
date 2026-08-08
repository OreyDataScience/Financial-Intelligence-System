from dash import html, register_page

register_page(
    __name__,
    path="/inventory",
    name="Inventory"
)

layout = html.Div(

    [

        html.H1("Inventory Intelligence"),

        html.Hr(),

        html.P(
            "Inventory health, stock-outs, inventory turnover, and replenishment insights will appear here."
        )

    ],

    style={
        "padding": "30px"
    }

)