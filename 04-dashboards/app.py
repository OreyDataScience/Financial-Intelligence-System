from dash import Dash, page_container
import dash_bootstrap_components as dbc

from components.sidebar import sidebar
from scripts.data_loader import recommended_actions

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

app.title = "Orey Analytics"

@app.server.get("/api/recommendations/sme")
def sme_recommendations():
    return recommended_actions[recommended_actions["Audience"] == "SME"].to_json(orient="records")

@app.server.get("/api/recommendations/lender")
def lender_recommendations():
    return recommended_actions[recommended_actions["Audience"] == "Lender"].to_json(orient="records")

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