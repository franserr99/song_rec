import os, sys, spotipy, requests, datetime, pytz, sqlalchemy
import pandas as pd
from  dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List

import pandas as pd

def main():
    #these lines we used to get the songs from public playlists
    #df,playlist_name=getPlaylistSongs('Vum0YuVdSUmLvCvp8mBfmQ&dd=1')
    #print(df)
    #df.to_csv(playlist_name+'.csv',index=False)
    getLikedSongs()
    
    
    pass


def getLikedSongs():
    oauth, spotify_client=init_auth_client()
    spotipy_id=spotify_client.me()['id']
    #spotify dev docs lists 50 as max
    saved_tracks=spotify_client.current_user_saved_tracks(limit=50)

    access_token=oauth.get_access_token()
    token=access_token['access_token']
    type=access_token['token_type']
    track_IDs, tracks_name,track_artists=get_tracks_info(saved_tracks)

    if(saved_tracks['next']):
        offset=50
        while(saved_tracks['next']):
            saved_tracks=spotify_client.current_user_saved_tracks(limit=50,offset=offset)
            offset+=50
            more_idx, more_track_names,more_artist_names= get_tracks_info(saved_tracks)
            track_IDs.extend(more_idx)
            tracks_name.extend(more_track_names)
            track_artists.extend(more_artist_names)

    #to avoid a low rate limit for auth code flow i am going to switch to client credentials flow 
    oauth,spotify_client=init_credentials_client()
    df= getAudFeatures(trackIDs=track_IDs, spotify_client=spotify_client)
    df.to_csv(spotipy_id+'liked_songs.csv', index=False)
    print(df)
    
def getPlaylistSongs(playlistURL:str ):
    #dont need authorization code flow,limited to anything that is public
    oauth, spotify_client=init_credentials_client()

    playlist_tracks=spotify_client.playlist(playlistURL)
    playlist_name=playlist_tracks['name']
    track_names=[]
    track_artists=[]
    track_URIs=[]

    for track_info in playlist_tracks['tracks']['items']:
        track_names.append(track_info['track']['name'])
        track_URIs.append(track_info['track']['uri'])
        track_artists.append(track_info['track']['artists'][0]['name'])
    
    #if more pages to process
    if playlist_tracks['tracks']['next']:
        access_token=oauth.get_access_token()
        token=access_token['access_token']
        type=access_token['token_type']
        paginate_results(playlist_tracks['tracks'], track_URIs,track_names,track_artists,token,type)

    #print(track_names)
    #print(track_URIs)
    #print(track_artists)

    return getAudFeatures(trackIDs=track_URIs,spotify_client=spotify_client),playlist_name

def getAudFeatures(trackIDs:List[str], spotify_client:spotipy.Spotify):
    partitioned_list=[] 
    if not trackIDs or len(trackIDs)==0:
        return 
    #break into 100 item chunks
    for i in range (0, len(trackIDs), 100): 
        partitioned_list.append(trackIDs[i:i+100])
    all_features=spotify_client.audio_features(trackIDs[0])[0]
    
    #get feature names
    feature_column_names=list(all_features.keys()) 
    print(feature_column_names)
    #this line gets taken out once we validate the data set
    feature_column_names.append('uri') #keep a copy to make sure data lines up later
    songs_audio_features=[]
    #account for songs that dont have audio features, easiest implementation i can think of
    all_bad_indices=[]

    for k, chunk in enumerate(partitioned_list):
        features=list(spotify_client.audio_features(chunk)) 
        assert(len(features)==len(chunk))
        #clean up data 
        if None in features: 
            #print(features)
            bad_indices=[]
            #get indicies of null values
            for i, v in enumerate(features): 
                if(v is None):
                    #account for the partioning 
                    all_bad_indices.append(int(i+((k)*100))) 
                    bad_indices.append(i) 
            #get rid of items in feature list that are null
            for j in range (len(bad_indices)): 
                features.pop(bad_indices[j])    
        #removed all nulls by now, dealing with only a list of dictionaries
        for song_features in features:
            feats=[]
            for column_name in feature_column_names:
                feats.append(song_features[column_name])
            #print(feats)
            songs_audio_features.append(feats)

    #create dataframe and return it 

    return pd.DataFrame(data=songs_audio_features,columns=feature_column_names)
def get_tracks_info(tracks:dict):
    tracks_URI=[]
    tracks_name=[]
    artists_name=[]
    for item in tracks['items']:
        tracks_URI.append(item['track']['uri'])
        tracks_name.append(item['track']['name'])
        artists=''
        n=len(item['track']['artists'])
        for i in range (n):
            artists+=item['track']['artists'][i]['name']
            if(i<=n-2):
                artists+=', '
        artists_name.append(artists) 
    

    assert(len(tracks_URI)==len(tracks_name)==len(artists_name))
    return tracks_URI, tracks_name, artists_name
def paginate_results(tracks:dict, idx:list, track_names:list, artist_names:list ,accessToken,type):
    while(tracks['next']):
        tracks= requests.get(tracks['next'], headers={ 'Authorization': type+" "+accessToken }).json()
        more_idx, more_track_names,more_artist_names= get_tracks_info(tracks)
        idx.extend(more_idx)
        track_names.extend(more_track_names)
        artist_names.extend(more_artist_names)

def loadENV():
    load_dotenv("/Users/franserr/Documents/spring_2023/data_science/song_reccomender/client.env")     #load env vars
    load_dotenv("/Users/franserr/Documents/spring_2023/data_science/song_reccomender/db.env")
    try: 
        #load_dotenv should load env var, now just check they exist in the enviorment
        os.environ["SPOTIPY_CLIENT_SECRET"] 
        os.environ['SPOTIPY_CLIENT_ID']
        os.environ["SPOTIPY_REDIRECT_URI"]
        os.environ['user']
        os.environ['password']
        os.environ['port']
    except:
        print("one of these were not set as an enviormental variable, needed for successful execution")
        sys.exit(1) 

#this assumes that the db is already up and running, prior to this a script has been run to seed the database and create the structure for it 
def init_credentials_client():
    loadENV()
    auth_manager = SpotifyClientCredentials()
    client = spotipy.Spotify(auth_manager=auth_manager)
    return auth_manager,client
def init_auth_client(): 
    loadENV()
    scope= "user-library-read user-read-playback-position user-top-read user-read-recently-played playlist-read-private"
    #now= datetime.datetime.now(tz=pytz.timezone('US/Pacific'))
    #now=now.strftime('%Y-%m-%d %H:%M:%S')
    oauth=SpotifyOAuth(scope=scope)
    sp=spotipy.Spotify(auth_manager=oauth)
    return oauth, sp



main()
