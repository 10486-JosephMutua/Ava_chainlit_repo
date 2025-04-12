from Ava_graph.graph.interfaces.interface import main as run_ava_graph
import chainlit as cl
import os # Make sure os is imported

# Define index function (looks good)
async def index(query):
  result= await run_ava_graph(query)
  # DEBUG: Print the raw result from the backend
  print(f"--- Raw Backend Result ---")
  print(result)
  print(f"--------------------------")
  return result

@cl.on_chat_start
def on_chat_start():
    print("Chat started. Ava is ready.")
    # Optional: Send a welcome message
    # await cl.Message(content="Hello! Ask me anything.").send()


@cl.on_message
async def main(message: cl.Message):
    print(f"Received message: {message.content}")
    result = await index(message.content)

    # --- More Robust Error Handling ---
    if not result:
        print("Error: Backend returned None or empty result.")
        await cl.Message(content="Sorry, I received an empty response from the backend.").send()
        return
    if 'messages' not in result or not result['messages']:
        print("Error: Backend result missing 'messages' list or it's empty.")
        await cl.Message(content="Sorry, I couldn't structure the backend response properly.").send()
        return
    # --- End Error Handling ---

    response = result['messages'][-1]
    workflow = result.get('workflow', None) # Use .get for safety
    print(f"DEBUG: Workflow detected: {workflow}")

    message_elements = [] # Initialize empty list for elements

    if workflow == "image":
        print("DEBUG: Entered 'image' workflow block.")
        image_file_path = result.get('image_path', None) # Use .get for safety

        if image_file_path:
            print(f"DEBUG: Potential image path: {image_file_path}")

            # *** CRITICAL CHECK: Does the file exist? ***
            if os.path.exists(image_file_path):
                print(f"DEBUG: File EXISTS at path: {image_file_path}")
                try:
                    # Create the image element
                    image_element = cl.Image(
                        path=image_file_path,
                        name="GeneratedImage", # Consistent name
                        display="inline",
                        size="medium"
                    )
                    # Add the element to our list
                    message_elements.append(image_element)
                    print(f"DEBUG: cl.Image element CREATED and ADDED to list.")

                except Exception as e:
                    # Catch errors during cl.Image creation itself
                    print(f"Error creating cl.Image object: {e}")
                    await cl.Message(content=f"Sorry, I found the image file but couldn't prepare it for display. Error: {e}").send()
                    # Still send the text part without the image
                    await cl.Message(content=f"{response.content}").send()
                    return # Exit early if image prep failed

            else:
                # *** The file was NOT found ***
                print(f"ERROR: File NOT FOUND at path: {image_file_path}")
                # Send the text response, but inform the user the image failed
                await cl.Message(
                    content=f"{response.content}\n\n(I tried to generate an image, but couldn't find the file at the expected location.)"
                ).send()
                return # Exit after sending the message with the error note

        else:
            print("ERROR: Workflow is 'image', but 'image_path' key is missing in the result.")
            # Send just the text response if path is missing
            await cl.Message(content=f"{response.content}").send()
            return # Exit early

    # If we got here, either workflow wasn't "image", OR it was "image" and the element was successfully added.

    print(f"DEBUG: Final message_elements list before sending: {message_elements}")
    print(f"DEBUG: Final text response to send: {response.content}")

    # Send the final message
    try:
        await cl.Message(
            content=f"{response.content}",
            elements=message_elements # Use the list (might be empty or contain the image)
        ).send()
        print("DEBUG: cl.Message sent successfully.")
    except Exception as e:
        print(f"ERROR sending cl.Message: {e}")