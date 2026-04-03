from data_processing.spreadsheet_reader import read_spreadsheet


def main() -> None:
    df = read_spreadsheet("data/input/sample_assets.xlsx")
    print(df.head())


if __name__ == "__main__":
    main()
