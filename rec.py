import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist


def main():
    # assuming they are in the csv files folder it should look like this: "csv_files/Back.csv"
    csv_file_name=input("provide the path to the csv file containing your songs")
    user_songs=pd.read_csv(csv_file_name, index_col=False)
    #ask the user what they want to do
    own_pool=int(input("enter 1 to provide your own rec pool of songs or 0 to use default pool"))
    if(own_pool==1):
        their_pool=input("provide the path like you did before for the pool of songs")
        rec_pool=pd.read_csv(their_pool, index_col=False)
    else: 
        rec_pool=pd.read_csv("csv_files/rec_pool.csv", index_col=False)
    rec_songs=get_rec_songs(rec_pool=rec_pool, user_songs=user_songs, num_of_recs=12)
    print(rec_songs.describe())

    rec_songs.to_csv("testFrancisco.csv", index=False)

def get_mean_vector(df:pd.DataFrame):
    #i am leaving key and mode out of this will return and explain why 
    numerical_features=["danceability","energy","loudness","speechiness","acousticness",
                        "instrumentalness","liveness","valence","tempo"]
    num_df=df[numerical_features]
    #print(num_df)
    #print("we have this many columns:",len(num_df.columns))
    return np.mean(num_df, axis=0), num_df
def get_rec_songs(rec_pool:pd.DataFrame, user_songs:pd.DataFrame, num_of_recs:int):
    #returns the mean vector and the df stipped down to numerical features only 
    mean_vector, num_df=get_mean_vector(user_songs)
    rec_pool.drop_duplicates(subset=["track_name", "artists"], inplace=True, keep="first")

    numerical_features=["danceability","energy","loudness","speechiness","acousticness",
                        "instrumentalness","liveness","valence","tempo"]
    rec_pool_num=rec_pool[numerical_features]

    #prep the scaler, fit it to the user songs
    scaler= StandardScaler() 
    scaler.fit(num_df)
    #scale the mean vector and the rec pool 
    scaled_rec_pool= scaler.transform(rec_pool_num)
    scaled_mean_vector=scaler.transform(num_df)
    #get a list of cosine distances from the mean song vector 
    distances_from_mean_song=cdist(scaled_mean_vector,scaled_rec_pool, 'cosine')

    indices=list(np.argsort(distances_from_mean_song)[:,:num_of_recs][0])

    #get the songs from the rec_pool
    rec_song_df=rec_pool.iloc[indices]
    #only the songs that are not already in the songs user has
    rec_songs=rec_song_df[~rec_pool['track_id'].isin(user_songs['id'])]
    #extract relevant infp
    relevant_col = ['track_name', 'artists']
    relevant_df=rec_songs[relevant_col]

    return relevant_df
#def get
if __name__=="__main__":
    main()