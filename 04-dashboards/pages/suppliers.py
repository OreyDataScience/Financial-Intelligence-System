from dash import html, register_page

register_page(
    __name__,
    path="/suppliers",
    name="Suppliers"
)

layout = html.Div(

    [

        html.H1("Supplier & Operational Risk"),

        html.Hr(),

        html.P(
            "Supplier performance, lead time analysis, operational risk, and procurement insights will appear here."
        )

    ],

    style={
        "padding": "30px"
    }

)