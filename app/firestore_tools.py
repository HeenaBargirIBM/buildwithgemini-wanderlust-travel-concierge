# Firestore tools for Wanderlust Travel Concierge
import logging
from typing import Any, Optional
from google.cloud import firestore

# IMPORTANT: Hardcode project ID string (do NOT use GOOGLE_CLOUD_PROJECT or google.auth.default())
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-60f927bb363e"
FIRESTORE_DATABASE_ID = "(default)"
COLLECTION_NAME = "destinations"

logger = logging.getLogger(__name__)


def _get_firestore_client() -> firestore.Client:
    """Returns a Firestore client configured with hardcoded project ID."""
    return firestore.Client(
        project=FIRESTORE_PROJECT_ID,
        database=FIRESTORE_DATABASE_ID,
    )


def search_destinations(query: str = "", budget_tier: str = "") -> list[dict[str, Any]]:
    """Search travel destinations in the Firestore catalog by keywords or budget tier.

    Args:
        query: Optional keyword or country/city name to search for (e.g., 'Japan', 'beach', 'mountain', 'Kyoto').
        budget_tier: Optional budget filter ('budget', 'moderate', 'luxury').

    Returns:
        A list of matching destination dictionaries from Firestore.
    """
    db = _get_firestore_client()
    docs = db.collection(COLLECTION_NAME).stream()

    results = []
    q_lower = query.lower().strip()
    tier_lower = budget_tier.lower().strip()

    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id

        # Check budget tier match if specified
        if tier_lower and data.get("budget_tier", "").lower() != tier_lower:
            continue

        # Check query keywords if specified
        if q_lower:
            searchable_text = f"{data.get('name', '')} {data.get('country', '')} {data.get('description', '')} {' '.join(data.get('popular_activities', []))} {' '.join(data.get('top_attractions', []))}".lower()
            if q_lower not in searchable_text:
                continue

        results.append(data)

    return results


def get_destination_details(destination_id: str) -> dict[str, Any]:
    """Get full details for a specific destination by its ID.

    Args:
        destination_id: The unique ID of the destination (e.g., 'kyoto-japan', 'paris-france').

    Returns:
        A dictionary with the destination details, or an error message if not found.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(destination_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Destination with ID '{destination_id}' not found."}

    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_destination(
    destination_id: str,
    name: str,
    country: str,
    description: str,
    budget_tier: str = "moderate",
    best_season: str = "Year-round",
    popular_activities: Optional[list[str]] = None,
    top_attractions: Optional[list[str]] = None,
    average_daily_cost_usd: int = 150,
) -> dict[str, Any]:
    """Add a new travel destination or update an existing one in the Firestore catalog.

    Args:
        destination_id: Unique slug ID for the destination (e.g. 'tokyo-japan', 'rome-italy').
        name: Name of the destination city or region.
        country: Country where the destination is located.
        description: Brief overview of the destination.
        budget_tier: Budget category ('budget', 'moderate', 'luxury').
        best_season: Ideal time of year to visit.
        popular_activities: List of popular activities or experiences.
        top_attractions: List of top landmarks/attractions.
        average_daily_cost_usd: Estimated average daily cost per person in USD.

    Returns:
        A confirmation dictionary indicating success.
    """
    db = _get_firestore_client()
    doc_ref = db.collection(COLLECTION_NAME).document(destination_id)

    destination_data = {
        "id": destination_id,
        "name": name,
        "country": country,
        "description": description,
        "budget_tier": budget_tier,
        "best_season": best_season,
        "popular_activities": popular_activities or [],
        "top_attractions": top_attractions or [],
        "average_daily_cost_usd": average_daily_cost_usd,
    }

    doc_ref.set(destination_data)
    logger.info(f"Added/updated destination '{destination_id}' in Firestore.")
    return {
        "status": "success",
        "message": f"Successfully saved destination '{name}, {country}' to Firestore.",
        "destination": destination_data,
    }
