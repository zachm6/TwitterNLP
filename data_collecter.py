import tweepy
from tweepy import client
import config
import datetime
import pandas as pd
import psycopg2
import preprocessor as p
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.sentiment.util import *
import numpy as np
import time

# Authenticate using OAuth2.0 Twitter
# OUTPUT: TYPE(dataframe)
def collectData():
    # initialize root dataframe
    df = pd.DataFrame()
    for hour in range(24):
        for minute in range(0, 60, 30):
            auth = tweepy.Client(
                bearer_token=config.BEARER_TOKEN,  
                consumer_key=config.API_KEY, 
                consumer_secret=config.API_KEY_SECRET, 
                access_token=config.ACCESS_TOKEN, 
                access_token_secret=config.ACCESS_TOKEN_SECRET
            )

            # use the datetime module here (automate)
            yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
            year = yesterday.strftime("%Y")
            month = yesterday.strftime("%m")
            day = yesterday.strftime("%d")
            hour = str(hour)
            minute = str(minute)
            minute_1 = str(int(minute)+1)
            startTime = datetime.datetime.strptime(f'{year}{month}{day}{hour}{minute}', '%Y%m%d%H%M')
            endTime = datetime.datetime.strptime(f'{year}{month}{day}{hour}{minute_1}', '%Y%m%d%H%M')

            symbol_list = ["TSLA", "AAPL", "AMZN"]

            # search tweets
            for symbol in symbol_list:
                q = f'{symbol} -is:retweet lang:en'

                # extract tweet data
                try:
                    row = {}

                    tweets = auth.search_recent_tweets(
                        query=q, 
                        start_time=startTime, 
                        end_time=endTime, 
                        max_results=100,
                        expansions=['author_id', 'entities.mentions.username', 'in_reply_to_user_id', 'referenced_tweets.id.author_id'],
                        user_fields=['public_metrics'],
                        tweet_fields=['public_metrics', 'created_at']    
                    )

                    # tweet data
                    for tweet in tweets.data:
                        row["id"] = tweet.id
                        row["symbol"] = symbol
                        row["text"] = tweet.text
                        row["start"] = startTime
                        row["end"] = endTime
                        row["retweet_count"] = tweet.public_metrics["retweet_count"]
                        row["reply_count"] = tweet.public_metrics["reply_count"]
                        row["like_count"] = tweet.public_metrics["like_count"]
                        row["quote_count"] = tweet.public_metrics["quote_count"]
                        row["impression_count"] = tweet.public_metrics["impression_count"]
                        row["created_at"] = tweet.created_at
                        print(row)
                    
                    # user data
                    for user in tweets.includes["users"]:

                        row["username"] = user.data["username"]
                        row["followers_count"] =  user.data["public_metrics"]["followers_count"]
                        row["following_count"] =  user.data["public_metrics"]["following_count"]
                        row["tweet_count"] = user.data["public_metrics"]["tweet_count"]
                        row["listed_count"] =  user.data["public_metrics"]["listed_count"]
                    
                    # convert dictionary to a dataframe and concatenate it to df
                    row_df = pd.DataFrame(row, index=[0])
                    df = pd.concat([df, row_df])
                
                except tweepy.errors.TooManyRequests as r:
                    MINUTES_TO_SLEEP = 15

                    # current time
                    ct = datetime.datetime.now()
                    ct = ct.strftime("%H:%M%:%S")
                    call_time = ct + datetime.timedelta(minutes=15)
                    call_time = call_time.strftime("%H:%M%:%S") 
                    print(f"Too many requests. Script is pausing for {MINUTES_TO_SLEEP} minutes @ {ct}")
                    print(f"The next call will occur at {call_time}")

                    # sleep 
                    time.sleep(MINUTES_TO_SLEEP*60)
                    print("Done Sleeping")

                except Exception as e:
                    print(f"A {e} has occured")
                    print()

    return df

# source: https://archive.is/9ApqZ#selection-1633.90-1645.43
# Using a library to deal with preprocessing
def preprocessing(row):
    text = str(row['text'])

    # Remove special characters
    text = text.replace("$", "").replace("&", "").replace("amp", "").replace(";", "").replace("\'", "")

    print(f"Text: {text}")
    text = p.clean(text)
    return text

# source: https://archive.is/9ApqZ#selection-2157.94-2157.818
def analysis(df):
    #Sentiment Analysis
    SIA = SentimentIntensityAnalyzer()

    # Applying Model, Variable Creation
    df['Polarity Score']=df["clean_tweet"].apply(lambda x:SIA.polarity_scores(x)['compound'])
    df['Neutral Score']=df["clean_tweet"].apply(lambda x:SIA.polarity_scores(x)['neu'])
    df['Negative Score']=df["clean_tweet"].apply(lambda x:SIA.polarity_scores(x)['neg'])
    df['Positive Score']=df["clean_tweet"].apply(lambda x:SIA.polarity_scores(x)['pos'])

    # Converting 0 to 1 Decimal Score to a Categorical Variable
    df['Sentiment']=''
    df.loc[df['Polarity Score']>0,'Sentiment']='Positive'
    df.loc[df['Polarity Score']==0,'Sentiment']='Neutral'
    df.loc[df['Polarity Score']<0,'Sentiment']='Negative'
    return df

def insert():
    # create database
    DB_NAME = "tweets"
    DB_USER = "zachmoss"
    DB_PASS = ""
    DB_HOST = "127.0.0.1"
    DB_PORT = "5432"
    conn = ""
    cur = ""
    
    # connect to database
    try:
        conn = psycopg2.connect(database=DB_NAME,
                                user=DB_USER,
                                password=DB_PASS,
                                host=DB_HOST,
                                port=DB_PORT)
        print("Database connected successfully")
    except:
        print("Database not connected successfully")
    
    # create table
    try:
        cur = conn.cursor()  # creating a cursor
 
        # executing queries to create table
        cur.execute("""
        CREATE TABLE Tweet
        (
            ID BIGINT PRIMARY KEY NOT NULL,
            SYMBOL VARCHAR(10),
            TEXT VARCHAR,
            STARTTIME VARCHAR,
            ENDTIME VARCHAR,
            CREATED_AT VARCHAR,
            POLARITY_SCORE NUMERIC(4,3),
            POSITIVE_SCORE NUMERIC(4,3),
            NEUTRAL_SCORE NUMERIC(4,3),
            NEGATIVE_SCORE NUMERIC(4,3),
            SENTIMENT VARCHAR,
            RETWEET_COUNT INT,
            REPLY_COUNT INT, 
            LIKE_COUNT INT,
            QUOTE_COUNT INT,
            IMPRESSION_COUNT INT,
            USERNAME VARCHAR,
            FOLLOWERS_COUNT INT, 
            FOLLOWING_COUNT INT, 
            TWEET_COUNT INT,
            LISTED_COUNT INT
        )
        """)
        
        # commit the changes
        conn.commit()
        print("Table Created successfully")
    except Exception as e:
        print("An exception occurred:", str(e))
        print("Table not created")
    
    # inserting rows into database
    for index, row in df.iterrows():
        try:
            # check if entry exists in database
            q = f"""
            SELECT 
                *
            FROM 
                tweet
            WHERE 
                ID = {row["id"]} 
            
            """
            cur.execute(q)
            rows = cur.fetchall()
            print(rows)
            print('Data fetched successfully')

            if not rows:
                # If the entry doesn't exist, insert it into the database
                cur.execute(f"""
                INSERT INTO tweet (ID, SYMBOL, TEXT, STARTTIME, ENDTIME, CREATED_AT ,POLARITY_SCORE, NEUTRAL_SCORE, NEGATIVE_SCORE, POSITIVE_SCORE, SENTIMENT, RETWEET_COUNT,
                REPLY_COUNT, LIKE_COUNT, QUOTE_COUNT, IMPRESSION_COUNT, USERNAME, FOLLOWERS_COUNT, FOLLOWING_COUNT, TWEET_COUNT, LISTED_COUNT)
                VALUES
                ({int(row['id'])}, '{str(row['symbol'])}', '{str(row["clean_tweet"])}', '{str(row["start"])}', '{str(row["end"])}', '{str(row["created_at"])}', {float(row["Polarity Score"])}, 
                {float(row["Neutral Score"])}, {float(row["Negative Score"])}, {float(row["Positive Score"])}, '{str(row["Sentiment"])}', {int(row["retweet_count"])}, 
                {int(row["reply_count"])}, {int(row["like_count"])}, {int(row["quote_count"])}, {int(row["impression_count"])}, '{str(row['username'])}', {int(row["followers_count"])},
                {int(row["following_count"])}, {int(row["tweet_count"])}, {int(row["listed_count"])})
                """)
                conn.commit()
                print('Data inserted successfully')
            else:
                print('Entry already exists in the database')
        except Exception as e:
            print(f'Exception occurred: {str(e)}')
            conn.rollback()
    conn.close()

def outputFile(df):
    # reconnect to database
    DB_NAME = "tweets"
    DB_USER = "zachmoss"
    DB_PASS = ""
    DB_HOST = "127.0.0.1"
    DB_PORT = "5432"
    conn = ""
    cur = ""

    try:
        conn = psycopg2.connect(database=DB_NAME,
                                user=DB_USER,
                                password=DB_PASS,
                                host=DB_HOST,
                                port=DB_PORT)
        print("Database connected successfully")
    except:
        print("Database not connected successfully")

    # export to csv
    try:
        cur = conn.cursor()  # creating a cursor
 
        # executing queries to create table
        cur.execute("""
        COPY tweet TO '/Users/zachmoss/Twitter Project/output.csv' WITH DELIMITER ',' CSV HEADER;
        """)
        
        # commit the changes
        conn.commit()
        print("CSV Created successfully")
    except Exception as e:
        print("An exception occurred:", str(e))
        print("CSV not created")
    conn.close()

# store tweets in a database
if __name__ == "__main__":
    df = collectData()
    preprocessing(df)
    df['clean_tweet'] = df.apply(preprocessing, axis=1)
    df = analysis(df)
    insert()
    outputFile(df)