import pandas as pd
import json
import os
import warnings
warnings.filterwarnings("ignore")


# Definition of the essential columns expected in the trade datasets
REQUIRED_COLUMNS = ['reporterCode', 'reporterISO', 'reporterDesc', 'partnerCode', 'partnerISO', 'partnerDesc', 'refYear', 'primaryValue']

# A list of country codes that are to be excluded from the dataset
NOT_USED_COUNTRY_CODES = [0, 899, 490, 837, 568]

# Merge trade data
def load_csvs_from_folder(folder_path: str) -> pd.DataFrame:

    csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]
    dataframes = []

    for file in csv_files:
        file_path = os.path.join(folder_path, file)
        df = pd.read_csv(file_path, encoding="windows-1252", index_col=False)
        dataframes.append(df)

    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df

def add_democracies_to_dataframe(combined_df: pd.DataFrame) -> pd.DataFrame:
    df_ert = pd.read_csv("01_rawdata/ert.csv")

    # Select only the relevant columns from df_ert
    df_ert_subset = df_ert[['country_text_id', 'year', 'v2x_polyarchy']]

    # Perform the merge
    merged_df = combined_df.merge(
        df_ert_subset,
        left_on=['partnerISO', 'refYear'],
        right_on=['country_text_id', 'year'],
        how='left'
    )

    # Drop the now redundant 'country_text_id' and 'year' columns
    merged_df = merged_df.drop(columns=['country_text_id', 'year'])
    merged_df.to_csv("trade_test.csv", index=False)
    return merged_df

def interpolate_data(combined_df: pd.DataFrame) -> pd.DataFrame:
    min_year = combined_df["refYear"].min()
    max_year = combined_df["refYear"].max()


    df_full = (
        combined_df.set_index(['reporterISO', 'refYear'])
        .groupby('reporterISO')
        .apply(lambda g: g.reindex(
            pd.MultiIndex.from_product([[g.name], range(min_year,
                                                        max_year)],
                                       names=['reporterISO_duplicate', 'refYear'])))
    )
    df_full = df_full.reset_index().drop(columns=['reporterISO_duplicate'])
    df_full['auto_share'] = df_full['auto_share'].interpolate()
    df_full['dem_share'] = df_full['dem_share'].interpolate()

    unique_combinations = df_full[['reporterISO', 'reporterDesc']].drop_duplicates().dropna()
    unique_combinations = unique_combinations.set_index('reporterISO').to_dict()["reporterDesc"]
    df_full['reporterDesc'] = df_full['reporterDesc'].fillna(df_full['reporterISO'].map(unique_combinations))
    return df_full


def group_trade_data(combined_df: pd.DataFrame) -> pd.DataFrame:
    combined_df["total_auto_trade"] = combined_df.loc[combined_df["v2x_polyarchy"] < 0.5]["primaryValue"]
    combined_df["total_dem_trade"] = combined_df.loc[combined_df["v2x_polyarchy"] >= 0.5]["primaryValue"]
    df_group_trade_data = combined_df.groupby(["reporterISO", "reporterDesc", "refYear"])[["total_auto_trade", "total_dem_trade"]].sum()
    df_group_trade_data["auto_share"] = df_group_trade_data["total_auto_trade"] /(df_group_trade_data["total_auto_trade"] + df_group_trade_data["total_dem_trade"])
    df_group_trade_data["dem_share"] = df_group_trade_data["total_dem_trade"] /(df_group_trade_data["total_auto_trade"] + df_group_trade_data["total_dem_trade"])
    return df_group_trade_data.reset_index()


def main() -> None:
    df_trade_data = load_csvs_from_folder("01_rawdata/trade_data")[REQUIRED_COLUMNS]
    df_trade_data = add_democracies_to_dataframe(df_trade_data)
    df_trade_data = group_trade_data(df_trade_data)
    df_trade_data = interpolate_data(df_trade_data)

    df_trade_data.to_csv("00_final_data.csv", index=False)
    return


if __name__ == "__main__":
    main()