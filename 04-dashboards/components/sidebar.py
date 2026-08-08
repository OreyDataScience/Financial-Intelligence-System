from dash import html
import dash_bootstrap_components as dbc

sidebar = html.Div(

    [

        html.Br(),

        html.Img(
            src="/assets/logo.png",
            style={
                "width": "90%",
                "display": "block",
                "margin": "auto"
            }
        ),

        html.H3(
            "OREY ANALYTICS",
            className="text-center mt-3"
        ),

        html.P(
            "Retail Intelligence",
            className="text-center text-muted"
        ),

        html.Hr(),

        dbc.Nav(

            [

                dbc.NavLink(
                    "🏠 Executive Dashboard",
                    href="/",
                    active="exact"
                ),

                dbc.NavLink(
                    "📈 Revenue Intelligence",
                    href="/revenue",
                    active="exact"
                ),

                dbc.NavLink(
                    "🛒 Product Performance",
                    href="/products",
                    active="exact"
                ),

                dbc.NavLink(
                    "🏬 Store Performance",
                    href="/stores",
                    active="exact"
                ),

                dbc.NavLink(
                    "📦 Inventory Intelligence",
                    href="/inventory",
                    active="exact"
                ),

                dbc.NavLink(
                    "🚚 Supplier Risk",
                    href="/suppliers",
                    active="exact"
                )

            ],

            vertical=True,
            pills=True

        ),

        html.Div(

            [

                html.Hr(),

                html.Small(
                    "© Orey Analytics",
                    className="text-muted"
                )

            ],

            style={
                "position": "absolute",
                "bottom": "20px",
                "left": "20px"
            }

        )

    ],

    style={
        "height": "100vh",
        "padding": "20px",
        "backgroundColor": "#F8F9FA"
    }

)