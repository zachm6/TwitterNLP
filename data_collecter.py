import tweepy
from tweepy import client
import config
import datetime
import pandas as pd
import psycopg2
import preprocessor as p
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.sentiment.util import *

# Authenticate using OAuth2.0 Twitter
# OUTPUT: TYPE(dataframe)
def collectData():
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
    hour = "00"
    minute = '00'
    minute_1 = '01'
    startTime = datetime.datetime.strptime(f'{year}{month}{day}{hour}{minute}', '%Y%m%d%H%M')
    endTime = datetime.datetime.strptime(f'{year}{month}{day}{hour}{minute_1}', '%Y%m%d%H%M')
    df = pd.DataFrame()

    symbol_list = ["TSLA", "AAPL", "AMZN"]

    # search tweets
    for symbol in symbol_list:
        q = f'{symbol} -is:retweet lang:en'

        tweets = auth.search_recent_tweets(
            query=q, 
            start_time=startTime, 
            end_time=endTime, 
            max_results=10)

        # extract 22k tweets per company (3 companies)
        for tweet in tweets.data:
            row = pd.DataFrame({
                "id": [tweet.id],
                "symbol": [symbol],
                "text": [tweet.text],
                "start": [startTime],
                "end": [endTime]
            })
            df = pd.concat([df, row])
            print(row)
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
            POLARITY_SCORE NUMERIC(4,3),
            POSITIVE_SCORE NUMERIC(4,3),
            NEUTRAL_SCORE NUMERIC(4,3),
            NEGATIVE_SCORE NUMERIC(4,3),
            SENTIMENT VARCHAR
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
                INSERT INTO tweet (ID, SYMBOL, TEXT, STARTTIME, ENDTIME, POLARITY_SCORE, NEUTRAL_SCORE, NEGATIVE_SCORE, POSITIVE_SCORE, SENTIMENT)
                VALUES
                ({int(row['id'])}, '{str(row['symbol'])}', '{str(row["clean_tweet"])}', '{str(row["start"])}', '{str(row["end"])}', {float(row["Polarity Score"])}, {float(row["Neutral Score"])}, {float(row["Negative Score"])}, {float(row["Positive Score"])}, '{str(row["Sentiment"])}')
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