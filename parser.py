import pandas as pd

def parse_description(description: str) -> dict:
    """
    Parses a single interview description into a dictionary with journey and round-wise breakdown.
    """
    parts = description.split('## Interview Rounds')
    journey = parts[0].strip()
    parsed = {"journey": journey}
    
    if len(parts) > 1:
        rounds = parts[1].split('### Round')[1:]
        for i, content in enumerate(rounds, 1):
            parsed[f"round_{i}"] = f"### Round {content.strip()}"
    
    return parsed

def structure_df(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses all descriptions in the raw dataframe and returns a structured DataFrame
    with journey, round_1 ... round_n columns.
    """
    # Apply parsing to each row
    parsed_rows = raw_df['description'].apply(parse_description).tolist()
    parsed_df = pd.DataFrame(parsed_rows)

    # Ensure all round_i columns are present up to max round
    parsed_df = _pad_round_columns(parsed_df)

    # Drop original 'description' column and merge
    final_df = pd.concat([raw_df.drop(columns=['description']), parsed_df], axis=1)
    return final_df

def _pad_round_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pads the DataFrame to include all round_i columns up to the max found.
    Missing rounds will be filled with None.
    """
    round_cols = [col for col in df.columns if col.startswith("round_")]
    max_round = 0

    for col in round_cols:
        try:
            round_num = int(col.split("_")[1])
            max_round = max(max_round, round_num)
        except:
            pass

    for i in range(1, max_round + 1):
        col_name = f"round_{i}"
        if col_name not in df.columns:
            df[col_name] = None

    return df
