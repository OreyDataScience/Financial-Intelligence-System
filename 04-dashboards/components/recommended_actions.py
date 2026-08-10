from dash import html
import dash_bootstrap_components as dbc

def recommended_actions_panel(actions):
    cards = []
    for _, action in actions.head(3).iterrows():
        cards.append(dbc.Col(dbc.Card(dbc.CardBody([
            html.Div([html.Span(f"Priority {int(action['Priority'])}", className="action-priority"), html.Span(str(action["Audience"]), className="action-audience")], className="d-flex justify-content-between mb-2"),
            html.H6(str(action["Action"]), className="mb-1"),
            html.P(str(action["Outcome"]), className="action-outcome mb-2"),
            dbc.Button("Review", href=str(action["Route"]), color="primary", size="sm"),
        ]), className="action-card h-100",
style={"minHeight": "155px"}), md=6, xl=4))
    return dbc.Card(dbc.CardBody([
        html.Div([html.H4("Recommended Actions", className="mb-0"), html.Small("Ranked by estimated impact")], className="d-flex justify-content-between align-items-center mb-3"),
        dbc.Row(cards, className="g-3"),
    ]), className="shadow-sm")