import tweepy
import os
import openai
import boto3
import uuid
from dotenv import load_dotenv
load_dotenv()
dynamodb = boto3.client('dynamodb')
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
API_KEY = os.environ.get("API_KEY")
API_KEY_SECRET = os.environ.get("API_KEY_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")
twitter_auth_keys = {
    "consumer_key": API_KEY,
    "consumer_secret": API_KEY_SECRET,
    "access_token": ACCESS_TOKEN,
    "access_token_secret": ACCESS_TOKEN_SECRET
}
auth = tweepy.OAuthHandler(
    twitter_auth_keys['consumer_key'],
    twitter_auth_keys['consumer_secret']
)
auth.set_access_token(
    twitter_auth_keys['access_token'],
    twitter_auth_keys['access_token_secret']
)

api = tweepy.API(auth)


def make_ddb_item(poem, dalle_image, s3_image_key):
    new_id = uuid.uuid4()
    item = {
        'id': {'S': str(new_id)},
        'poem': {'S': poem},
        'dalle_image_url': {'S': dalle_image},
        's3_image_key': {'S': s3_image_key},
    }
    return item


def Tweet(content):
    post_result = api.update_status(status=content)
    print(post_result)


def lambda_handler(event, context):
    print(twitter_auth_keys)
    response_text = openai.Completion.create(
        model="text-davinci-003",
        prompt="make a random theme poem within 120 characters and with hashtags at the end, the whole text should not exceeds 135 characters",
        temperature=0.6,
        max_tokens=150,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=1
    )
    poem_hashtags = response_text.choices[0].text
    Tweet(poem_hashtags)
