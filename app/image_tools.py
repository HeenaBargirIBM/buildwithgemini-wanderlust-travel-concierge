# Image generation tools for Wanderlust Travel Concierge
import logging
import uuid
from google import genai
from google.genai import types
from google.cloud import storage
from google.adk.tools import ToolContext

logger = logging.getLogger(__name__)

# IMPORTANT: Hardcoded project ID and public Cloud Storage bucket name
PROJECT_ID = "qwiklabs-gcp-02-60f927bb363e"
BUCKET_NAME = "wanderlust-media-qwiklabs-gcp-02-60f927bb363e"


def generate_destination_postcard(
    prompt: str,
    tool_context: ToolContext,
) -> dict[str, str]:
    """Generates a scenic postcard visual for a travel destination or landmark using gemini-3.1-flash-lite-image in the global region.

    Saves the image as an ADK artifact for the Playground Artifacts panel and uploads the in-memory image bytes to Cloud Storage, returning the public HTTPS URL.

    Args:
        prompt: Visual description of the destination, landmark, or scenic spot (e.g., 'A vibrant postcard of Eiffel Tower at sunset in Paris').
        tool_context: Injected ADK ToolContext context object.

    Returns:
        A dictionary containing the public HTTPS Cloud Storage URL, artifact filename, and status message.
    """
    logger.info(f"Generating image with gemini-3.1-flash-lite-image in global region for prompt: '{prompt}'")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
        ),
    )

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return {"error": f"Failed to generate image bytes for prompt: '{prompt}'."}

    ext = "png" if "png" in mime_type else "jpg"
    unique_id = str(uuid.uuid4())[:8]
    filename = f"postcard_{unique_id}.{ext}"

    # (1) Save image as ADK artifact so it appears in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)
    logger.info(f"Saved artifact '{filename}' via tool_context.save_artifact.")

    # (2) Upload in-memory image bytes directly to public Cloud Storage bucket (no local file written)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob_path = f"postcards/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
    logger.info(f"Uploaded in-memory postcard bytes to Cloud Storage: {public_url}")

    return {
        "status": "success",
        "message": f"Successfully generated postcard for '{prompt}'.",
        "artifact_filename": filename,
        "public_url": public_url,
    }


def generate_destination_video(
    prompt: str,
    tool_context: ToolContext,
) -> dict[str, str]:
    """Generates a short promotional video for a travel destination or landmark using gemini-omni-flash-preview in the global region.

    Saves the video as an ADK artifact for the Playground Artifacts panel and uploads the in-memory video bytes to Cloud Storage, returning the public HTTPS URL.

    Args:
        prompt: Visual and atmospheric description of the destination video (e.g., 'A short cinematic video of waves crashing on a tropical beach at sunset').
        tool_context: Injected ADK ToolContext context object.

    Returns:
        A dictionary containing the public HTTPS Cloud Storage URL, artifact filename, and status message.
    """
    logger.info(f"Generating video with gemini-omni-flash-preview in global region for prompt: '{prompt}'")
    client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")

    response = client.models.generate_content(
        model="gemini-omni-flash-preview",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "VIDEO"],
        ),
    )

    video_bytes = None
    mime_type = "video/mp4"

    if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                video_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not video_bytes:
        return {"error": f"Failed to generate video bytes for prompt: '{prompt}'."}

    unique_id = str(uuid.uuid4())[:8]
    filename = f"destination_video_{unique_id}.mp4"

    # (1) Save video as ADK artifact so it appears in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    tool_context.save_artifact(filename=filename, artifact=artifact_part)
    logger.info(f"Saved artifact '{filename}' via tool_context.save_artifact.")

    # (2) Upload in-memory video bytes directly to public Cloud Storage bucket (no local file written)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob_path = f"videos/{filename}"
    blob = bucket.blob(blob_path)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{blob_path}"
    logger.info(f"Uploaded in-memory video bytes to Cloud Storage: {public_url}")

    return {
        "status": "success",
        "message": f"Successfully generated video for '{prompt}'.",
        "artifact_filename": filename,
        "public_url": public_url,
    }

