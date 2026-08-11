import pandas as pd
import plotly.graph_objects as go


# ==========================================================
# OREY ANALYTICS COLOUR PALETTE
# ==========================================================

OREY_NAVY = "#061A35"
OREY_BLUE = "#1479D2"
OREY_LIGHT_BLUE = "#48A7F8"
OREY_GREEN = "#2ECC71"
OREY_ORANGE = "#F39C12"
OREY_RED = "#C0392B"
OREY_PURPLE = "#8E44AD"
OREY_GREY = "#7F8C8D"
OREY_LIGHT_GREY = "#E9EEF5"


# ==========================================================
# COMMON CHART LAYOUT
# ==========================================================

def apply_chart_layout(
    fig,
    height=340,
    title=None,
    yaxis_title=None
):

    fig.update_layout(

        template="plotly_white",

        height=height,

        title=dict(
            text=title if title else "",
            font=dict(
                size=20,
                color=OREY_NAVY
            ),
            x=0
        ),

        font=dict(
            family="Arial",
            color=OREY_NAVY
        ),

        paper_bgcolor="white",

        plot_bgcolor="white",

        margin=dict(
            l=55,
            r=25,
            t=65,
            b=55
        ),

        hovermode="x unified",

        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        )

    )

    fig.update_xaxes(

        showgrid=False,

        linecolor="#D9E1EA",

        tickfont=dict(
            size=11
        )

    )

    fig.update_yaxes(

        title=yaxis_title,

        gridcolor="#E9EEF5",

        zeroline=False,

        title_font=dict(
            size=12
        ),

        tickfont=dict(
            size=11
        )

    )

    return fig


# ==========================================================
# OPERATIONAL RISK TRENDS
# ==========================================================

def operational_risk_chart(operational):

    data = operational.copy()

    # ------------------------------------------------------
    # ENSURE CORRECT ORDER
    # ------------------------------------------------------

    try:

        data["_Month_Date"] = pd.to_datetime(
            data["Month"]
        )

        data = data.sort_values(
            "_Month_Date"
        )

    except Exception:

        pass

    # ------------------------------------------------------
    # VALUES
    # ------------------------------------------------------

    stockout = (
        data["StockOutRate"]
        .astype(float)
        .mul(100)
    )

    returns = (
        data["ReturnRate"]
        .astype(float)
        .mul(100)
    )

    # ------------------------------------------------------
    # CHART
    # ------------------------------------------------------

    fig = go.Figure()

    # Stock-out rate
    fig.add_trace(

        go.Scatter(

            x=data["Month"],

            y=stockout,

            mode="lines+markers",

            name="Stock-Out Rate",

            line=dict(
                color=OREY_RED,
                width=3
            ),

            marker=dict(
                size=7,
                color=OREY_RED
            ),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Stock-Out Rate: %{y:.2f}%"
                "<extra></extra>"
            )

        )

    )

    # Return rate
    fig.add_trace(

        go.Scatter(

            x=data["Month"],

            y=returns,

            mode="lines+markers",

            name="Return Rate",

            line=dict(
                color=OREY_ORANGE,
                width=3
            ),

            marker=dict(
                size=7,
                color=OREY_ORANGE
            ),

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Return Rate: %{y:.2f}%"
                "<extra></extra>"
            )

        )

    )

    # ------------------------------------------------------
    # REFERENCE LINES
    # ------------------------------------------------------

    stockout_median = stockout.median()

    fig.add_hline(

        y=stockout_median,

        line_dash="dash",

        line_width=1,

        line_color=OREY_GREY,

        annotation_text=(
            f"Stock-Out Median: "
            f"{stockout_median:.2f}%"
        ),

        annotation_position="top left"

    )

    # ------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------

    apply_chart_layout(

        fig,

        height=360,

        title="Operational Risk Trends",

        yaxis_title="Rate (%)"

    )

    fig.update_yaxes(
        ticksuffix="%"
    )

    return fig


# ==========================================================
# LEAD TIME TREND
# ==========================================================

def lead_time_chart(operational):

    data = operational.copy()

    try:

        data["_Month_Date"] = pd.to_datetime(
            data["Month"]
        )

        data = data.sort_values(
            "_Month_Date"
        )

    except Exception:

        pass

    lead_time = data["Avg_LeadTime"].astype(float)

    fig = go.Figure()

    # ------------------------------------------------------
    # LEAD TIME
    # ------------------------------------------------------

    fig.add_trace(

        go.Scatter(

            x=data["Month"],

            y=lead_time,

            mode="lines+markers",

            name="Average Lead Time",

            line=dict(
                color=OREY_BLUE,
                width=3
            ),

            marker=dict(
                size=7,
                color=OREY_BLUE
            ),

            fill="tozeroy",

            fillcolor="rgba(20,121,210,0.08)",

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Average Lead Time: %{y:.2f} days"
                "<extra></extra>"
            )

        )

    )

    # ------------------------------------------------------
    # MEDIAN REFERENCE
    # ------------------------------------------------------

    median_lead_time = lead_time.median()

    fig.add_hline(

        y=median_lead_time,

        line_dash="dash",

        line_width=1,

        line_color=OREY_GREY,

        annotation_text=(
            f"Median: {median_lead_time:.2f} days"
        ),

        annotation_position="top left"

    )

    # ------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------

    apply_chart_layout(

        fig,

        height=320,

        title="Average Supplier Lead Time",

        yaxis_title="Days"

    )

    return fig


# ==========================================================
# OPERATIONAL RISK PRESSURE
# ==========================================================

def operational_pressure_chart(operational):

    data = operational.copy()

    try:

        data["_Month_Date"] = pd.to_datetime(
            data["Month"]
        )

        data = data.sort_values(
            "_Month_Date"
        )

    except Exception:

        pass

    # ------------------------------------------------------
    # NORMALISATION
    # ------------------------------------------------------

    def min_max(series):

        minimum = series.min()

        maximum = series.max()

        if maximum == minimum:

            return pd.Series(
                [50] * len(series),
                index=series.index
            )

        return (
            (series - minimum)
            /
            (maximum - minimum)
            * 100
        )

    stockout_score = min_max(
        data["StockOutRate"].astype(float)
    )

    return_score = min_max(
        data["ReturnRate"].astype(float)
    )

    lead_time_score = min_max(
        data["Avg_LeadTime"].astype(float)
    )

    # Equal-weight operational pressure index
    pressure = (

        stockout_score * 0.40

        +

        return_score * 0.25

        +

        lead_time_score * 0.35

    )

    fig = go.Figure()

    fig.add_trace(

        go.Scatter(

            x=data["Month"],

            y=pressure,

            mode="lines+markers",

            name="Operational Pressure",

            line=dict(
                color=OREY_PURPLE,
                width=3
            ),

            marker=dict(
                size=7,
                color=OREY_PURPLE
            ),

            fill="tozeroy",

            fillcolor="rgba(142,68,173,0.08)",

            hovertemplate=(
                "<b>%{x}</b><br>"
                "Operational Pressure: %{y:.1f}/100"
                "<extra></extra>"
            )

        )

    )

    # ------------------------------------------------------
    # RISK BANDS
    # ------------------------------------------------------

    fig.add_hrect(

        y0=0,
        y1=33.3,

        fillcolor="rgba(46,204,113,0.08)",

        line_width=0,

        annotation_text="Lower Pressure",

        annotation_position="top left"

    )

    fig.add_hrect(

        y0=33.3,
        y1=66.6,

        fillcolor="rgba(243,156,18,0.08)",

        line_width=0,

        annotation_text="Moderate Pressure",

        annotation_position="top left"

    )

    fig.add_hrect(

        y0=66.6,
        y1=100,

        fillcolor="rgba(192,57,43,0.08)",

        line_width=0,

        annotation_text="Higher Pressure",

        annotation_position="top left"

    )

    apply_chart_layout(

        fig,

        height=320,

        title="Operational Pressure Index",

        yaxis_title="Pressure Score"

    )

    fig.update_yaxes(
        range=[0, 100]
    )

    return fig