import pandas as pd
from ai import review_application , ReviewedApplication

def read_file(filename):
    df = pd.read_csv(filename)
    df["revised_description"] = ""
    for index,row in df.iterrows():
       result: ReviewedApplication = review_application(row["Job Description"])
       revised_summary = result.overall_summary
       print("\n\n",revised_summary,"\n\n")
       df.loc[index,"revised_description"] = revised_summary
    
    df.to_csv("test/eval_output.csv")

read_file("test/job_rewriting_tests.csv")