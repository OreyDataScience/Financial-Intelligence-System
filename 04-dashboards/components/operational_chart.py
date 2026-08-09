import plotly.graph_objects as go


def operational_risk_chart(operational):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=operational["Month"],
            y=operational["StockOutRate"] * 100,

            mode="lines+markers",

            name="Stock-Out Rate",

            line=dict(color="#1479D2", width=3),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Stock-Out Rate: %{y:.1f}%"
                "<extra></extra>"
            )

        )

    )

    fig.add_trace(

        go.Scatter(

            x=operational["Month"],
            y=operational["ReturnRate"] * 100,

            mode="lines+markers",

            name="Return Rate",

            line=dict(color="#48A7F8", width=3),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Return Rate: %{y:.1f}%"
                "<extra></extra>"
            )

        )

    )

    fig.update_layout(

        title="Operational Risk Trends",

        height=360,

        xaxis_title="",

        yaxis_title="Rate (%)",

        hovermode="x unified",

        template="plotly_white",

        legend=dict(
            orientation="h",
            y=1.08,
            x=0
        ),

        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20
        )

    )

    fig.update_yaxes(
        ticksuffix="%"
    )

    return fig


def lead_time_chart(operational):

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=operational["Month"],

            y=operational["Avg_LeadTime"],

            mode="lines+markers",

            name="Average Lead Time",

            line=dict(color="#1479D2", width=3),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Average Lead Time: %{y:.1f}"
                "<extra></extra>"
            )

        )

    )

    fig.update_layout(

        title="Average Supplier Lead Time",

        height=340,

        xaxis_title="",

        yaxis_title="Lead Time",

        template="plotly_white",

        margin=dict(
            l=20,
            r=20,
            t=70,
            b=20
        )

    )

    return fig
