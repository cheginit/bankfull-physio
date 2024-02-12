"""

Deps: pandas, geopandas, pyogrio, openpyxl
"""
import geopandas as gpd
import pandas as pd


def extract_ab(equation: str) -> list[str | None]:
    """Extract the 'a' and 'b' components from a regression equation string."""
    if pd.isna(equation):
        return [None, None]
    parts = equation.split("DA")
    a = parts[0].strip()
    b = parts[1].strip() if len(parts) > 1 else None
    return [a, b]


def process_excel_data(file_path: str) -> pd.DataFrame:
    """Process the Excel file to extract and format data."""
    excel_data = pd.read_excel(file_path, sheet_name=None)
    # Extracting data from the first sheet
    first_col = next(iter(excel_data.keys()))
    sheet_data = excel_data[first_col].dropna(how="all").reset_index(drop=True)

    sheet_data["a_width"], sheet_data["b_width"] = zip(
        *sheet_data["Bankfull width"].map(extract_ab), strict=True
    )
    sheet_data["a_depth"], sheet_data["b_depth"] = zip(
        *sheet_data["Bankfull depth"].map(extract_ab), strict=True
    )
    sheet_data["a_area"], sheet_data["b_area"] = zip(
        *sheet_data["Bankfull cross-sectional area"].map(extract_ab), strict=True
    )

    sheet_data = sheet_data.drop(
        columns=["Bankfull width", "Bankfull depth", "Bankfull cross-sectional area", "Unnamed: 3"]
    )

    sheet_data["Physiographic Province"] = sheet_data["Physiographic Province"].str.upper()
    sheet_data = sheet_data.set_index("Physiographic Province")
    for c in sheet_data:
        sheet_data[c] = pd.to_numeric(sheet_data[c], errors="coerce")
    return sheet_data


bf_equations = process_excel_data("bankfull.xlsx")
ab_div = bf_equations[bf_equations.index.str.len() == 3]
ab_prov = bf_equations[bf_equations.index.str.len() > 3]
url = "https://www.sciencebase.gov/catalog/file/get/631405bbd34e36012efa304e?f=__disk__fb%2Fbf%2F25%2Ffbbf251babefbc699117ab49ff2f9acf04349ca4"
phyis = gpd.read_file(url, engine="pyogrio")
name_map = {
    "INTERIOR PLAINS": "IPL",
    "PACIFIC MOUNTAIN SYSTEM": "PMS",
    "ROCKY MOUNTAIN SYSTEM": "RMS",
    "LAURENTIAN UPLAND": "LUP",
    "INTERMONTANE PLATEAUS": "IMP",
    "APPALACHIAN HIGHLANDS": "AHI",
    "ATLANTIC PLAIN": "APL",
    "INTERIOR HIGHLANDS": "IHI",
    None: "USA",
}
phyis["DIV"] = phyis["DIVISION"].map(name_map)
for c in ab_prov:
    phyis[c] = phyis["PROVINCE"].map(ab_prov[c]).fillna(phyis["DIV"].map(ab_div[c]))
phyis.to_parquet("bankfull_phyiso.parquet")
