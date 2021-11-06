import pandas as pd
import os
import typer

KEY_WORDS = ["Alexandre DO", "data science"]

PATH_SAVE = "./inputs/"
SAVED_FILE_NAME = "input_google_search.txt"
if __name__ == "__main__":
    date_from = ["2018/01/01", "2019/01/01", "2020/01/01"]
    date_to = ["2019/01/01", "2020/01/01", "2021/01/01"]
    save_file = ["data_2018.jsonl", "data_2019.jsonl", "data_2020.jsonl"]
    requests = []
    for word in KEY_WORDS:
        for date_from_, date_to_, save_file_ in zip(date_from, date_to, save_file):
            request = ";".join(
                [f'{word}', date_from_, date_to_, PATH_SAVE + save_file_]
            )
            requests.append(request)

    if not os.path.isdir(PATH_SAVE):
        os.makedirs(PATH_SAVE)
    with open(PATH_SAVE + SAVED_FILE_NAME, "w") as f:
        for request in requests:
            f.write(request)
            f.write("\n")
