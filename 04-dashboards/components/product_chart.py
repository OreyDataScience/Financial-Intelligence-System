import plotly.express as px

OREY_BLUES = ["#1479D2", "#48A7F8", "#0B4F92", "#8CC9FF", "#2467A5"]


def top_products_chart(products):

    top = (

        products

        .sort_values("Revenue", ascending=False)

        .head(10)

    )

    fig = px.bar(

        top,

        x="Revenue",

        y="ProductName",

        orientation="h",

        color="Category",

        text="Revenue",

        template="plotly_white",
        color_discrete_sequence=OREY_BLUES

    )

    fig.update_traces(

        texttemplate="R %{text:,.0f}",

        textposition="outside"

    )

    fig.update_layout(

        title="Top 10 Products by Revenue",

        height=360,

        xaxis_title="Revenue (R)",

        yaxis_title="",

        legend_title="Category",

        margin=dict(

            l=20,

            r=20,

            t=70,

            b=20

        )

    )

    fig.update_yaxes(

        categoryorder="total ascending"

    )

    return fig
