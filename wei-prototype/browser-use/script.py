import os
import asyncio
import tempfile
from browser_use import Agent, BrowserSession, BrowserProfile, Controller, ActionResult
from browser_use.llm import ChatOpenAI
from dotenv import load_dotenv
from utils import get_copy_code

load_dotenv()

DATE = "2025-08-31"
TIME = "7PM"
PPL = 2
LOCATION = "San Francisco"
INBOX_ID = "opentable_2@agentmail.to"
PHONE = "+18777804236"
FIRST_NAME = "WAGENT"
LAST_NAME = "SRY"

# Create controller instance for custom functions
controller = Controller()


# Custom function to retrieve verification code from email
@controller.action("Get verification code from email")
def get_verification_code(inbox_id: str = INBOX_ID) -> ActionResult:
    """Retrieves verification code from the latest email in the specified inbox."""
    try:
        code = get_copy_code(inbox_id)
        if code:
            return ActionResult(extracted_content=f"Found verification code: {code}")
        else:
            return ActionResult(
                extracted_content="No verification code found in email yet. You may need to wait a moment for the email to arrive, then try again."
            )
    except Exception as e:
        return ActionResult(
            extracted_content=f"Error retrieving verification code: {str(e)}. You may need to check the email manually."
        )


async def main():
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables.")
        print("Please add OPENAI_API_KEY=your_openai_key to your .env file")
        print("You can get an API key from: https://platform.openai.com/api-keys")
        return

    # Initialize LLM
    llm = ChatOpenAI(api_key=openai_api_key, model="o3")

    # Create the main task for restaurant reservation
    task_details = f"""
    Complete a restaurant reservation on OpenTable:
    
    1. Go to opentable.com
    2. Fill out the search bar with date:{DATE}, time:{TIME}, number or people:{PPL},location in {LOCATION}, and click search for available restaurants
    3. Select the first available restaurant from the search results
    4. Use email {INBOX_ID} to make the reservation (If it requires credit card info, go back to previous step and choose another restaurant)
    5. If prompted for a verification code:
       - Use the "Get verification code from email" action to retrieve the code from email
       - Enter the verification code to complete the reservation
       - If no code is found, wait a moment and try the action again (emails may take time to arrive)
    6. If prompted for personal info:
       - Phone number: {PHONE} (+1 is USA Country Code)
       - FIRST_NAME: {FIRST_NAME}
       - LAST_NAME {LAST_NAME}
    7. Complete the reservation and return the final confirmation details including:
       - Restaurant name and location
       - Reservation date and time
       - Number of people
       - Confirmation number (if available)
    
    Important: Do not pause or stop when verification is needed - use the custom function to get the code and continue.
    """

    print("Starting restaurant reservation task...")

    # Create a browser profile with a temporary user data directory
    temp_dir = tempfile.mkdtemp(prefix="browser_use_")
    browser_profile = BrowserProfile(user_data_dir=temp_dir)

    # Create a browser session that will persist across tasks
    browser_session = BrowserSession(browser_profile=browser_profile)

    # Create and run the agent with persistent session
    agent = Agent(
        task=task_details,
        llm=llm,
        browser_session=browser_session,
        controller=controller,  # Pass the controller with custom functions
        max_steps=50,  # Limit steps for safety
        # use_vision=True,
        save_conversation_path="complete_reservation_conversation.json",
    )

    try:
        # Run the complete reservation task (including verification handling)
        print("Running reservation agent with automatic verification handling...")
        result = await agent.run()

        print("✅ Restaurant reservation task completed!")
        final_output = str(
            result.final_result() if hasattr(result, "final_result") else result
        )
        print(f"\nFinal reservation details:\n{final_output}")

    except Exception as e:
        print(f"❌ Error during task execution: {e}")
        print("Check the conversation files for more details.")
    finally:
        # Clean up browser session and temporary directory
        if "browser_session" in locals():
            try:
                # Browser session cleanup is handled automatically
                print("🔄 Browser session cleanup completed.")
            except Exception as cleanup_error:
                print(
                    f"Note: Browser cleanup error (this is usually normal): {cleanup_error}"
                )

        # Clean up temp directory
        if "temp_dir" in locals():
            import shutil

            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
                print(f"🗑️  Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
