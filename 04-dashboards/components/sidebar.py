from dash import html
import dash_bootstrap_components as dbc

NAV_ITEMS = [("Executive Dashboard", "/"), ("Revenue Intelligence", "/revenue"), ("Product Performance", "/products"), ("Store Performance", "/stores"), ("Inventory Intelligence", "/inventory"), ("Supplier Risk", "/suppliers"), ("Customer Segments", "/segments"), ("Channel Analysis", "/channels"), ("Operational Risk", "/operational")]

sidebar = html.Div([
    html.Img(src="/assets/logo.png", className="orey-logo"),
    html.H3("OREY ANALYTICS", className="orey-brand text-center"),
    html.P("Retail Intelligence", className="orey-tagline text-center"),
    html.Hr(style={"borderColor": "rgba(157,200,244,.22)", "margin": "10px 0"}),
    dbc.Nav([dbc.NavLink(label, href=href, active="exact") for label, href in NAV_ITEMS], vertical=True, pills=True, className="orey-nav"),
    html.Small("© Orey Analytics", className="orey-sidebar-footer"),
], className="orey-sidebar-inner")
