from botocore.exceptions import ClientError
import logging
import tweepy
import os
import openai
import boto3
import uuid
import requests
from dotenv import load_dotenv
load_dotenv()
dynamodb = boto3.client('dynamodb')
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
API_KEY = os.environ.get("API_KEY")
API_KEY_SECRET = os.environ.get("API_KEY_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET")
DYNAMODB_TABLE = os.environ.get("DYNAMODB_TABLE")
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


def upload_file_s3(file_name, bucket, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
        print(f's3 upload response {response}')
    except ClientError as e:
        logging.error(e)
        return False
    return True


def make_ddb_item(poem, dalle_image_url, s3_image_key):
    new_id = uuid.uuid4()
    item = {
        'id': {'S': str(new_id)},
        'poem': {'S': poem},
        'dalle_image_url': {'S': dalle_image_url},
        's3_image_key': {'S': s3_image_key},
    }
    return item


def Tweet(content, fileName):

    media = api.media_upload(fileName)

    # Post tweet with image
    post_result = api.update_status(status=content, media_ids=[media.media_id])
    print(post_result)


def generateImage(poem_hashtags):
    response_image_prompt = openai.Completion.create(
        model="text-davinci-003",
        prompt="turn this poem into one final text prompt for DALL.E to create an image "+poem_hashtags,
        temperature=0.6,
        max_tokens=150,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=1
    )

    image_prompt = response_image_prompt.choices[0].text
    print("result poem")
    print(poem_hashtags)
    print("image prompt")
    print(image_prompt)
    response_image = openai.Image.create(
        prompt=image_prompt,
        n=1,
        size="1024x1024"
    )
    for _, img in enumerate(response_image['data']):
        url = img['url']
        response = requests.get(url)

        # Directories
        img_dir = f'/tmp/img'
        os.makedirs(img_dir)
        # try:

        #     # Check if the response is valid
        #     if response.status_code == 200:
        #         # Set the file name and open the file in writing mode
        #         file_name = f'{img_dir}/{str(index)}.jpg'

        #         with open(file_name, "wb") as f:
        #             # Write the contents of the response (the image) to the file
        #             f.write(response.content)
        #     else:
        #         print("Could not download image")
        # except Exception as e:
        #     print(e)
        #     print(
        #         'Something went terribly wrong! Contact the developer (^_^) if the issue persists.')

        # Check if the response is valid
        if response.status_code == 200:
            # Set the file name and open the file in writing mode
            file_name = f'{str(uuid.uuid4())}.jpg'
            file_path = f'{img_dir}/{file_name}'
            with open(file_path, "wb") as f:
                # Write the contents of the response (the image) to the file
                f.write(response.content)
            # Tweet(poem_hashtags, file_name)
            return file_name, file_path, url
        else:
            print("Could not download image")


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
    file_name, file_path, url = generateImage(poem_hashtags)
    Tweet(poem_hashtags, file_path)
    upload_file_s3(file_path, S3_BUCKET_NAME)

    item = make_ddb_item(poem_hashtags, url, file_name)
    response = dynamodb.put_item(TableName=DYNAMODB_TABLE, Item=item)


def testPpt():
    response_text = openai.Completion.create(
        model="text-davinci-003",
        prompt="Make a ppt outline and bullet points on teaching History for high school 101 class with 10 slides, with great details and timeline and important historic figure names, seprate every slide with ##",
        temperature=0.6,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=1,
        presence_penalty=1
    )
    ppt = response_text.choices[0].text
    # print(ppt)
    pptArr = str(ppt).split("##")
    print(pptArr[3])
    response = openai.Image.create(
        prompt=f"make an image for the following slide with artistic style and high resolution {pptArr[3]}",
        n=3,
        size="1024x1024"
    )

    image_url = response['data'][0]['url']
    print(image_url)


testPpt()
