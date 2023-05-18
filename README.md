# Twitter Bot

This is a Twitter bot project that generates and posts random theme poems to the Twitter account [@momo123us](https://twitter.com/momo123us). The bot uses the Twitter API and OpenAI's text generation model to create poems and automatically post them on Twitter.

## Prerequisites

Before running the project, make sure you have the following:

- Python 3.x installed
- Twitter API credentials
- OpenAI API key
- AWS S3 bucket configured
- AWS DynamoDB client

## Installation

1. Clone the repository:

```shell
git clone https://github.com/your-username/your-repo.git
```

2. Install the required dependencies by running the following command:

```shell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root directory and populate it with your environment variables:

```
S3_BUCKET_NAME=your-bucket-name
BEARER_TOKEN=your-twitter-bearer-token
API_KEY=your-twitter-api-key
API_KEY_SECRET=your-twitter-api-key-secret
ACCESS_TOKEN=your-twitter-access-token
ACCESS_TOKEN_SECRET=your-twitter-access-token-secret
OPENAI_API_KEY=your-openai-api-key
```

## Usage

To use the Twitter bot, follow these steps:

1. Run the `lambda_handler` function in the `bot.py` file.

2. The bot will generate a random theme poem within 120 characters using OpenAI's text generation model.

3. The generated poem, along with relevant hashtags, will be posted to the Twitter account [@momo123us](https://twitter.com/momo123us).

## Contributing

Contributions to the project are welcome. If you encounter any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).
