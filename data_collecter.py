import tweepy
from tweepy import client
import config
import datetime
import pandas as pd

#Authenticate using OAuth2.0 Twitter
OAuth2_client = tweepy.Client(
    bearer_token=config.BEARER_TOKEN,  
    consumer_key=config.API_KEY, 
    consumer_secret=config.API_KEY_SECRET, 
    access_token=config.ACCESS_TOKEN, 
    access_token_secret=config.ACCESS_TOKEN_SECRET
    )

q = 'tesla -is:retweet'

# use the datetime module here (automate)
yesterday = datetime.datetime.today() - datetime.timedelta(days=1)
year = yesterday.strftime("%Y")
month = yesterday.strftime("%m")
day = yesterday.strftime("%d")
hour = '00'
minute_1 = '00'
minute_2 = '01'
second = '00'
format_data = '%Y%m%d%H%M'
test_str = '202201140015'
test_int = int(test_str)
startTime = datetime.datetime.strptime(f'{year}{month}{day}{minute_1}', '%Y%m%d%M')
endTime = datetime.datetime.strptime(f'{year}{month}{day}{minute_2}', '%Y%m%d%M')
data = {}

# a function that return endtime that leads to a query with a result_count less than or equal to 100
# INPUT TYPES: start and end: datetime object
# RETURN TYPES: end: datetime object
def find_end_time(start, end):
    # start and end need to be a datetime object
    tweets = OAuth2_client.search_recent_tweets(query=q, start_time=start, end_time=end, max_results=100)
    num_of_tweets = tweets.meta['result_count']
    tweet_limit = 100

    while num_of_tweets < tweet_limit:
        end += datetime.timedelta(minutes=1)
        tweets = OAuth2_client.search_recent_tweets(query=q, start_time=start, end_time=end, max_results=100)
        num_of_tweets = tweets.meta['result_count']

    # decrement end by 1 to ensure that it is a number less than 100
    end -= datetime.timedelta(minutes=1)
    return end

def store_data(counter, tweets, start, end):
    l1 = [tweets, start, end]
    counter += 1
    data[counter] = l1
    return data

def get_tweets_from_one_day(start, end):
    counter = 0
    data = {}
    # now_str = datetime.datetime.now().strftime(format)

    # convert end into an integer to make a comparison
    end = int(end.strftime(format_data))

    while end < test_int:
        print(f'start: {start}')
        print(f'end: {end}')

        # convert end integer into a string
        end = str(end)

        # convert end from string back into a datetime object
        end = datetime.datetime.strptime(end, format_data)

        # update end
        end = find_end_time(start, end)

        # get the data 
        tweets = OAuth2_client.search_recent_tweets(query=q, start_time = start, end_time = end, max_results=100)

        # store the data
        data = store_data(counter, tweets.data, start, end)
        counter += 1

        # update start
        start = end

        # increment end by one
        end += datetime.timedelta(minutes=1)

        # convert end into an integer to make a comparison
        end = int(end.strftime(format_data))
    return data

def main():
    # TYPES: startTime and endTime: datetime objects
    data = get_tweets_from_one_day(startTime, endTime)
    print('Completed gathering tweets...')
    df = pd.DataFrame(data)
    df = df.T
    print(df.head())
    return data

if __name__ == "__main__":
    main()

# goal is to create a function that collects all tweets from one day

#TODO:
# save data into a dataframe (tweets.data is cleanly stored into a DataFrame)
# clean the data to have appropriate fields
# understand the rate limits
# automate this process of data collection
# get information about the number of likes (way to clean the data)