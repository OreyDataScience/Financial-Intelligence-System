import plotly.express as px


# ==========================================================
# SUPPLIER RISK COLOURS
# ==========================================================

RISK_COLOURS = {
    "Reliable": "#2ECC71",
    "Moderate Risk": "#F39C12",
    "High Risk": "#C0392B"
}

RISK_ORDER = [
    "Reliable",
    "Moderate Risk",
    "High Risk"
]


# ==========================================================
# NORMALISE RISK VALUES
# ==========================================================

def normalise_risk(value):

    value = str(value).strip().lower()

    if value in ["low", "reliable"]:
        return "Reliable"

    elif value in [
        "medium",
        "moderate",
        "moderate risk"
    ]:
        return "Moderate Risk"

    elif value in [
        "high",
        "critical",
        "high risk"
    ]:
        return "High Risk"

    else:
        return "High Risk"


# ==========================================================
# SUPPLIER ATTENTION SCORE
# ==========================================================

def calculate_supplier_attention_score(suppliers):

    data = suppliers.copy()

    # ------------------------------------------------------
    # NORMALISE RISK
    # ------------------------------------------------------

    data["Risk_Display"] = data["Supplier_Risk"].apply(
        normalise_risk
    )

    # ------------------------------------------------------
    # OPERATIONAL CONCERN
    # ------------------------------------------------------

    median_stockout = data["StockOutRate"].median()

    median_lead_time = data["Avg_LeadTime"].median()

    def operational_concern(row):

        stockout = row["StockOutRate"]
        lead_time = row["Avg_LeadTime"]
        risk = row["Risk_Display"]

        if risk == "High Risk":

            if stockout >= median_stockout and \
               lead_time >= median_lead_time:

                return "Critical supplier exposure"

            elif stockout >= median_stockout:

                return "High stock-out exposure"

            elif lead_time >= median_lead_time:

                return "Extended lead time"

            else:

                return "Monitor supplier reliability"

        elif risk == "Moderate Risk":

            if stockout >= median_stockout:

                return "Monitor stock availability"

            elif lead_time >= median_lead_time:

                return "Monitor delivery time"

            else:

                return "Monitor supplier performance"

        else:

            return "Reliable supplier"

    data["Operational_Concern"] = data.apply(
        operational_concern,
        axis=1
    )

    # ------------------------------------------------------
    # RISK SCORE — 30%
    # ------------------------------------------------------

    risk_scores = {
        "Reliable": 0,
        "Moderate Risk": 50,
        "High Risk": 100
    }

    data["Risk_Score"] = data["Risk_Display"].map(
        risk_scores
    )

    # ------------------------------------------------------
    # STOCK-OUT EXPOSURE SCORE — 30%
    # ------------------------------------------------------

    max_stockout = data["StockOutRate"].max()

    if max_stockout > 0:

        data["StockOut_Score"] = (
            data["StockOutRate"] /
            max_stockout
        ) * 100

    else:

        data["StockOut_Score"] = 0

    # ------------------------------------------------------
    # LEAD-TIME EXPOSURE SCORE — 25%
    # ------------------------------------------------------

    max_lead_time = data["Avg_LeadTime"].max()

    if max_lead_time > 0:

        data["LeadTime_Score"] = (
            data["Avg_LeadTime"] /
            max_lead_time
        ) * 100

    else:

        data["LeadTime_Score"] = 0

    # ------------------------------------------------------
    # OPERATIONAL CONCERN SCORE — 15%
    # ------------------------------------------------------

    concern_scores = {

        "Critical supplier exposure": 100,

        "High stock-out exposure": 85,

        "Extended lead time": 75,

        "Monitor supplier reliability": 60,

        "Monitor stock availability": 55,

        "Monitor delivery time": 50,

        "Monitor supplier performance": 40,

        "Reliable supplier": 0

    }

    data["Concern_Score"] = (
        data["Operational_Concern"]
        .map(concern_scores)
        .fillna(0)
    )

    # ------------------------------------------------------
    # FINAL ATTENTION SCORE
    # ------------------------------------------------------

    data["Attention_Score"] = (

        data["Risk_Score"] * 0.30

        + data["StockOut_Score"] * 0.30

        + data["LeadTime_Score"] * 0.25

        + data["Concern_Score"] * 0.15

    )

    # Keep score strictly between 0 and 100
    data["Attention_Score"] = (

        data["Attention_Score"]

        .clip(
            lower=0,
            upper=100
        )

        .round(1)

    )

    return data


# ==========================================================
# TOP 10 SUPPLIERS REQUIRING MOST ATTENTION
# ==========================================================

def top_attention_suppliers(suppliers, n=10):

    data = calculate_supplier_attention_score(
        suppliers
    )

    return (

        data

        .sort_values(
            "Attention_Score",
            ascending=False
        )

        .head(n)

        .copy()

    )


# ==========================================================
# SUPPLIER RISK MATRIX
# ==========================================================

def supplier_risk_matrix_chart(suppliers):

    data = calculate_supplier_attention_score(
        suppliers
    )

    data["StockOut_Percent"] = (
        data["StockOutRate"]
        .round(4)
        .mul(100)
    )

    fig = px.scatter(

        data,

        x="Avg_LeadTime",

        y="StockOut_Percent",

        color="Risk_Display",

        size="Revenue",

        hover_name="SupplierID",

        hover_data={

            "Avg_LeadTime": ":.2f",

            "StockOut_Percent": ":.2f",

            "Revenue": ":,.0f",

            "Risk_Display": True,

            "Operational_Concern": True,

            "Attention_Score": ":.1f"

        },

        template="plotly_white",

        color_discrete_map=RISK_COLOURS,

        category_orders={
            "Risk_Display": RISK_ORDER
        }

    )

    median_lead_time = data["Avg_LeadTime"].median()

    median_stockout = data["StockOut_Percent"].median()

    fig.add_vline(

        x=median_lead_time,

        line_dash="dash",

        line_width=1,

        line_color="#7F8C8D",

        annotation_text="Median Lead Time",

        annotation_position="top"

    )

    fig.add_hline(

        y=median_stockout,

        line_dash="dash",

        line_width=1,

        line_color="#7F8C8D",

        annotation_text="Median Stock-Out Rate",

        annotation_position="top left"

    )

    fig.update_layout(

        title="Supplier Risk Matrix",

        height=430,

        xaxis_title="Average Lead Time (Days)",

        yaxis_title="Stock-Out Rate (%)",

        legend_title_text="",

        margin=dict(

            l=60,

            r=40,

            t=75,

            b=100

        ),

        legend=dict(

            orientation="h",

            yanchor="top",

            y=-0.18,

            xanchor="center",

            x=0.5

        )

    )

    return fig


# ==========================================================
# LOWEST SUPPLIER LEAD TIMES
# ==========================================================

def supplier_lowest_lead_time_chart(suppliers):

    data = suppliers.copy()

    data["Risk_Display"] = data["Supplier_Risk"].apply(
        normalise_risk
    )

    lowest = (

        data

        .sort_values(
            "Avg_LeadTime",
            ascending=True
        )

        .head(5)

        .copy()

    )

    fig = px.bar(

        lowest,

        x="SupplierID",

        y="Avg_LeadTime",

        color="Risk_Display",

        text="Avg_LeadTime",

        template="plotly_white",

        color_discrete_map=RISK_COLOURS,

        category_orders={

            "Risk_Display": RISK_ORDER,

            "SupplierID": lowest[
                "SupplierID"
            ].tolist()

        }

    )

    fig.update_traces(

        texttemplate="%{text:.2f} days",

        textposition="outside",

        textfont=dict(
            size=10
        )

    )

    fig.update_layout(

        title="Lowest Lead Times",

        height=300,

        xaxis_title="Supplier",

        yaxis_title="Average Lead Time (Days)",

        legend_title="Supplier Risk",

        margin=dict(

            l=50,

            r=30,

            t=70,

            b=80

        ),

        xaxis=dict(

            tickangle=0,

            type="category",

            tickmode="array",

            tickvals=lowest[
                "SupplierID"
            ].tolist(),

            ticktext=lowest[
                "SupplierID"
            ].tolist(),

            categoryorder="array",

            categoryarray=lowest[
                "SupplierID"
            ].tolist()

        )

    )

    for risk in RISK_ORDER:

        if risk not in lowest["Risk_Display"].values:

            fig.add_bar(

                x=[None],

                y=[None],

                name=risk,

                marker_color=RISK_COLOURS[risk],

                showlegend=True,

                hoverinfo="skip"

            )

    return fig


# ==========================================================
# HIGHEST SUPPLIER LEAD TIMES
# ==========================================================

def supplier_highest_lead_time_chart(suppliers):

    data = suppliers.copy()

    data["Risk_Display"] = data["Supplier_Risk"].apply(
        normalise_risk
    )

    highest = (

        data

        .sort_values(
            "Avg_LeadTime",
            ascending=False
        )

        .head(5)

        .sort_values(
            "Avg_LeadTime",
            ascending=True
        )

        .copy()

    )

    fig = px.bar(

        highest,

        x="SupplierID",

        y="Avg_LeadTime",

        color="Risk_Display",

        text="Avg_LeadTime",

        template="plotly_white",

        color_discrete_map=RISK_COLOURS,

        category_orders={

            "Risk_Display": RISK_ORDER,

            "SupplierID": highest[
                "SupplierID"
            ].tolist()

        }

    )

    fig.update_traces(

        texttemplate="%{text:.2f} days",

        textposition="outside",

        textfont=dict(
            size=10
        )

    )

    fig.update_layout(

        title="Highest Lead Times",

        height=300,

        xaxis_title="Supplier",

        yaxis_title="Average Lead Time (Days)",

        legend_title="Supplier Risk",

        margin=dict(

            l=50,

            r=30,

            t=70,

            b=80

        ),

        xaxis=dict(

            tickangle=0,

            type="category",

            tickmode="array",

            tickvals=highest[
                "SupplierID"
            ].tolist(),

            ticktext=highest[
                "SupplierID"
            ].tolist(),

            categoryorder="array",

            categoryarray=highest[
                "SupplierID"
            ].tolist()

        )

    )

    for risk in RISK_ORDER:

        if risk not in highest["Risk_Display"].values:

            fig.add_bar(

                x=[None],

                y=[None],

                name=risk,

                marker_color=RISK_COLOURS[risk],

                showlegend=True,

                hoverinfo="skip"

            )

    return fig


# ==========================================================
# SUPPLIER RISK DISTRIBUTION
# ==========================================================

def supplier_risk_distribution_chart(suppliers):

    data = suppliers.copy()

    data["Risk_Display"] = data["Supplier_Risk"].apply(
        normalise_risk
    )

    risk_distribution = (

        data["Risk_Display"]

        .value_counts()

        .reindex(
            RISK_ORDER,
            fill_value=0
        )

        .reset_index()

    )

    risk_distribution.columns = [
        "Risk",
        "Supplier_Count"
    ]

    fig = px.pie(

        risk_distribution,

        names="Risk",

        values="Supplier_Count",

        hole=0.55,

        template="plotly_white",

        color="Risk",

        color_discrete_map=RISK_COLOURS,

        category_orders={
            "Risk": RISK_ORDER
        }

    )

    fig.update_traces(

        textposition="outside",

        texttemplate="%{percent:.1%}",

        textfont=dict(
            size=11
        ),

        hovertemplate=(

            "<b>%{label}</b><br>"

            "Suppliers: %{value}<br>"

            "Share: %{percent}"

            "<extra></extra>"

        )

    )

    fig.update_layout(

        title="Supplier Risk Distribution",

        height=300,

        legend_title="Supplier Risk",

        margin=dict(

            l=10,

            r=10,

            t=60,

            b=20

        )

    )

    return fig


# ==========================================================
# AVERAGE LEAD TIME BY RISK
# ==========================================================

def supplier_lead_time_by_risk_chart(suppliers):

    data = suppliers.copy()

    data["Risk_Display"] = data["Supplier_Risk"].apply(
        normalise_risk
    )

    lead_time = (

        data

        .groupby(
            "Risk_Display",
            as_index=False
        )["Avg_LeadTime"]

        .mean()

        .set_index("Risk_Display")

        .reindex(RISK_ORDER)

        .reset_index()

    )

    fig = px.bar(

        lead_time,

        x="Risk_Display",

        y="Avg_LeadTime",

        color="Risk_Display",

        text="Avg_LeadTime",

        template="plotly_white",

        color_discrete_map=RISK_COLOURS,

        category_orders={
            "Risk_Display": RISK_ORDER
        }

    )

    fig.update_traces(

        texttemplate="%{text:.2f} days",

        textposition="outside",

        textfont=dict(
            size=10
        )

    )

    fig.update_layout(

        title="Average Lead Time by Risk",

        height=300,

        xaxis_title="Supplier Risk",

        yaxis_title="Average Lead Time (Days)",

        showlegend=False,

        margin=dict(

            l=50,

            r=20,

            t=60,

            b=60

        ),

        xaxis=dict(

            type="category",

            categoryorder="array",

            categoryarray=RISK_ORDER

        )

    )

    return fig