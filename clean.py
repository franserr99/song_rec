from langdetect import detect
import pandas as pd
import numpy as np
def main(): 

    #rec_pool=pd.read_csv("csv_files/rec_pool.csv", index_col=False)
    #rec_pool['lang']=rec_pool['track_name'].apply(detect_lang)
    #rec_pool = rec_pool[rec_pool['lang'] == 'en']
    #rec_pool.to_csv("rec_pool_cleaned.csv", index=False)
    rec_pool= pd.read_csv("csv_files/rec_pool_cleaned.csv",index_col=False)
    rec_pool.drop(rec_pool.filter(regex="Unname"),axis=1, inplace=True)
    rec_pool.to_csv("rec_pool_cleaned.csv", index=False)

    #rec_pool.drop(, axis=1)

    print(rec_pool)

    pass
def detect_lang(text):
        try:
            return detect(text)
        except:
            return 'unknown'
if __name__=="__main__":
    main()
    