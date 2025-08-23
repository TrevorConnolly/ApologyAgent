import os
from dotenv import load_dotenv
from agentmail import AgentMail
from bs4 import BeautifulSoup


def extract_confirm_email_url(html_content):
    """
    Extract confirmation URL from HTML content by looking for element with id="confirm-email-link".

    Args:
        html_content (str): HTML content to parse

    Returns:
        str or None: The confirmation URL if found, None otherwise
    """
    if not html_content:
        return None

    try:
        soup = BeautifulSoup(html_content, "html.parser")
        confirm_link = soup.find("a", id="confirm-email-link")

        if confirm_link and confirm_link.get("href"):
            return confirm_link["href"]
    except Exception as e:
        print(f"Error parsing HTML: {e}")

    return None


def get_confirmation_url(inbox_id="opentable@agentmail.to", api_key=None):
    """
    Get the confirmation URL from the latest email in the specified inbox.

    Args:
        inbox_id (str): The inbox ID to check for messages
        api_key (str, optional): AgentMail API key. If None, loads from .env

    Returns:
        str or None: The confirmation URL if found, None otherwise
    """
    # Load API key if not provided
    if api_key is None:
        load_dotenv()
        api_key = os.getenv("AGENTMAIL_API_KEY")

    if not api_key:
        raise ValueError(
            "AGENTMAIL_API_KEY not found in environment or provided as parameter"
        )

    # Initialize the client
    client = AgentMail(api_key=api_key)

    try:
        # Get all messages
        all_messages = client.inboxes.messages.list(inbox_id=inbox_id)

        if all_messages.count == 0:
            return None

        # Get the latest message
        latest_message_id = all_messages.messages[0].message_id
        message = client.inboxes.messages.get(
            inbox_id=inbox_id,
            message_id=latest_message_id,
        )

        # Extract confirmation URL
        return extract_confirm_email_url(message.html)

    except Exception as e:
        print(f"Error retrieving messages: {e}")
        return None


# Example usage when run as script
if __name__ == "__main__":
    confirm_url = get_confirmation_url()

    if confirm_url:
        print(f"Confirmation URL: {confirm_url}")
    else:
        print("No confirmation URL found")
