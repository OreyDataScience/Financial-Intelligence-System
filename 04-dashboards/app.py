from dash import Dash, page_container
import dash_bootstrap_components as dbc

from components.sidebar import sidebar

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

app.title = "Orey Analytics"

app.layout = dbc.Container(

    [

        dbc.Row(

            [

                dbc.Col(
                    sidebar,
                    width=2,
                    className="sidebar"
                ),

                dbc.Col(
                    page_container,
                    width=10,
                    className="content"
                )

            ],

            className="g-0"

        )

    ],

    fluid=True

)

if __name__ == "__main__":
    app.run(debug=True)