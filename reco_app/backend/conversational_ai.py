import logging
import os

import dotenv
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationalAI:
    def __init__(self):
        # Load environment variables
        parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        dotenv.load_dotenv(f"{parent_dir}/.env", override=True)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key for OpenAI is not set in .env file")

        self.client = openai.OpenAI(api_key=self.api_key)

    def generate_response(
        self,
        message: str,
        history: list[str] = [],
        prompt: str = "You are a helpful assistant.",
        max_tokens=100,
    ):
        """
        Generates a response from the GPT-3.5 model given a prompt.

        Args:
            prompt (str): The input text to the model.
            max_tokens (int): Maximum number of tokens to generate in the response.

        Returns:
            str: The generated text response from the model.
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # or another appropriate engine
                messages=[
                    {"role": "system", "content": prompt},
                    *history,
                    {"role": "user", "content": message},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            logger.info(f"Generated response: {response}")
            return response.choices[0].message.content

        except Exception as e:
            print(f"An error occurred: {e}")
            return ""


# Example usage:
if __name__ == "__main__":
    cai = ConversationalAI()
    user_prompt = "Give me a random color."
    print(cai.generate_response(user_prompt))
