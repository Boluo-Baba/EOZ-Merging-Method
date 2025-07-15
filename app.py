import faicons as fa
import plotly.express as px
import pandas as pd
import numpy as np

# Load data and compute static values
from shiny import reactive, render
from shiny.express import input, ui
from shinywidgets import render_plotly

tips = pd.read_csv("data/tips.csv")
data = pd.read_csv("data/Li_Minfeng_OD_27032023_094446_CUR.CSV", sep=';', encoding='iso-8859-1').set_index('FRONT').iloc[:, :-1].iloc[:140, 2:]
ui.include_css("styles.css")

bill_rng = (min(tips.total_bill), max(tips.total_bill))

ui.page_opts(title="EOZ-Merging-Method", fillable=True)

# Add main content
ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "ellipsis": fa.icon_svg("ellipsis"),
}

with ui.layout_columns(col_widths=[6], fill=False):
    with ui.value_box(showcase=ICONS["user"]):
        "Total tippers"

        @render.express
        def total_tippers():
            2333

with ui.layout_columns(col_widths=[6], fill=False):

    with ui.card(full_screen=True):
        with ui.card_header(class_="d-flex justify-content-between align-items-center"):
            "Total bill vs tip"
            with ui.popover(title="Add a color variable", placement="top"):
                ICONS["ellipsis"]
                ui.input_radio_buttons(
                    "scatter_color",
                    None,
                    ["none", "sex", "smoker", "day", "time"],
                    inline=True,
                )

        @render_plotly
        def scatterplot():
            color = input.scatter_color()

            z = np.random.randn(10, 12)
            fig = px.imshow(z, color_continuous_scale="Viridis")
            return fig
            
            # return px.scatter(
            #     tips_data(),
            #     x="total_bill",
            #     y="tip",
            #     color=None if color == "none" else color,
            #     trendline="lowess",
            # )

# --------------------------------------------------------
# Reactive calculations and effects
# --------------------------------------------------------

@reactive.calc
def tips_data():
    bill = input.total_bill()
    idx1 = tips.total_bill.between(bill[0], bill[1])
    idx2 = tips.time.isin(input.time())
    return tips[idx1 & idx2]


@reactive.effect
@reactive.event(input.reset)
def _():
    ui.update_slider("total_bill", value=bill_rng)
    ui.update_checkbox_group("time", selected=["Lunch", "Dinner"])
