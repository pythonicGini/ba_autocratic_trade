import pandas as pd
import json
import numpy as np
from scpi_pkg.scdata import scdata
from scpi_pkg.scest import scest
from scpi_pkg.scpi import scpi
from scpi_pkg.scplot import scplot
from plotnine import coord_cartesian, labs, theme, element_rect
import os
import warnings
warnings.filterwarnings("ignore")

def main() -> None:
    with open("00_treatment_countries.json", "r") as f:
        countries = json.load(f)


    folder = "09_plots"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)


    df_data = pd.read_csv("00_final_data.csv")
    df_data["index"] = pd.factorize(df_data['reporterISO'])[0]
    df_data = df_data.set_index("index")

    count = 0
    count_max = len(countries.keys())

    for country, value_dict in countries.items():
        count += 1
        if count % 3 == 0:
            print("Completed ", count, "of ", count_max)


        if not all(value_dict.values()):
            continue

        treated_unit = country
        donor_units = [c for c in countries.keys() if (countries[c]["dem"] == "steady") and (c != treated_unit)]
        pre_period = np.arange(2000, value_dict["treat_start"])
        post_period = np.arange(value_dict["treat_start"], 2023)

        # Lade deinen Datensatz
        df_data_local = df_data.copy()[["reporterISO", "refYear", "auto_share"]]
        df_data_local = df_data_local.loc[df_data_local["reporterISO"].isin(donor_units + [treated_unit])]


        # 1. Datenstruktur vorbereiten
        prep = scdata(
            df=df_data_local,
            id_var="reporterISO",
            time_var="refYear",
            outcome_var="auto_share",
            unit_tr=treated_unit,
            unit_co=donor_units,
            period_pre=pre_period,
            period_post=post_period,
            #constant=True,
            cointegrated_data=True
        )

        ## 2. Gewichtsschätzung (Punkt-Schätzung)
        #est = scest(
        #    df=prep,
        #    w_constr={"name": "ridge"},  # alternativ: lasso, ridge
        #    V="separate",
        #    #solver="ECOS"
        #)

        # 3. Inferenz + Unsicherheitsbereiche (optional aber empfohlen)
        w_constr = {'name': 'simplex', 'Q': 1}
        u_missp = True
        u_sigma = "HC1"
        u_order = 1
        u_lags = 0
        e_method = "all"
        e_order = 1
        e_lags = 0
        e_alpha = 0.05
        u_alpha = 0.05
        sims = 50
        cores = 8

        result = scpi(
            data=prep,
            sims=sims,
            w_constr=w_constr,
            u_order=u_order,
            u_lags=u_lags,
            e_order=e_order,
            e_lags=e_lags,
            e_method=e_method,
            u_missp=u_missp,
            u_sigma=u_sigma,
            cores=cores,
            e_alpha=e_alpha,
            u_alpha=u_alpha,
            verbose=False
        )

        # 4. Plot generieren

        ((scplot(result) +
         coord_cartesian(ylim=(0, 1))+
         labs(
             title='Share of trade with autocratic regimes for ' + country,
             x='Time',
             y='Share of trade with autocratic regimes' ) +
         theme(
             legend_position=(0, 1),
             legend_justification=(0, 1),
             legend_background=element_rect(fill='white', alpha=0.5))
        )
         .save(f"09_plots/{value_dict["dem"]}_{country}.png", width=6, height=4, dpi=400))

if __name__ == "__main__":
    main()