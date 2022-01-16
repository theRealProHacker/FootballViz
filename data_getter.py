import pandas as pd

def get_data(table_name:str):
    """Gets the dataframe from the given string"""
    path=f"./database/{table_name}.csv"
    df=pd.read_csv(path)
    assert (not df.empty)
    return df