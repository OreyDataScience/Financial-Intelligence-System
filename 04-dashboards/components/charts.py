import plotly.graph_objects as go


def revenue_chart(monthly, forecast):

    fig = go.Figure()

    # Historical Revenue
    fig.add_trace(

        go.Scatter(

            x=monthly["Month"],
            y=monthly["Revenue"],

            mode="lines+markers",

            name="Revenue",

            line=dict(
                color="#1479D2",
                width=3
            ),

            marker=dict(size=8),

            hovertemplate="<b>%{x}</b><br>Revenue: R %{y:,.0f}<extra></extra>"

        )

    )

    # Forecast
    fig.add_trace(

        go.Scatter(

            x=forecast["Month"],
            y=forecast["Revenue_Forecast"],

            mode="lines",

            name="Forecast",

            line=dict(
                color="#48A7F8",
                width=3,
                dash="dash"
            ),

            hovertemplate="<b>%{x}</b><br>Forecast: R %{y:,.0f}<extra></extra>"

        )

    )

    # Upper CI
    fig.add_trace(

        go.Scatter(

            x=forecast["Month"],
            y=forecast["Upper_95"],

            mode="lines",

            line=dict(width=0),

            showlegend=False,

            hoverinfo="skip"

        )

    )

    # Lower CI
    fig.add_trace(

        go.Scatter(

            x=forecast["Month"],
            y=forecast["Lower_95"],

            mode="lines",

            fill="tonexty",

            fillcolor="rgba(72,167,248,0.20)",

            line=dict(width=0),

            name="95% Confidence",

            hoverinfo="skip"

        )

    )

    fig.update_layout(

        template="plotly_white",

        height=330,

        title=dict(
            text="Revenue Trend & 6-Month Forecast",
            x=0.01,
            font=dict(size=17, color="#102A4C")
        ),

        hovermode="x unified",

        paper_bgcolor="#FFFFFF",

        plot_bgcolor="#FFFFFF",

        margin=dict(
            l=20,
            r=20,
            t=55,
            b=20
        ),

        legend=dict(
            orientation="h",
            y=1.08,
            x=0
        )

    )

    fig.update_xaxes(

        title="",

        showgrid=False,

        showline=False

    )

    fig.update_yaxes(

        title="Revenue (R)",

        separatethousands=True,

        gridcolor="#DDEAF6",

        zeroline=False

    )

    return fig
