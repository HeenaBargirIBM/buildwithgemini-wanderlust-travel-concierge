# Seed script for Firestore travel destinations catalog
import logging
from google.cloud import firestore

# IMPORTANT: Hardcode project ID string (do NOT use GOOGLE_CLOUD_PROJECT or google.auth.default())
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-02-60f927bb363e"
FIRESTORE_DATABASE_ID = "(default)"

COLLECTION_NAME = "destinations"

SAMPLE_DESTINATIONS = [
    {
        "id": "kyoto-japan",
        "name": "Kyoto",
        "country": "Japan",
        "description": "Historical capital of Japan famous for classical Buddhist temples, gardens, imperial palaces, and cherry blossoms.",
        "budget_tier": "moderate",
        "best_season": "Spring / Autumn",
        "popular_activities": ["Temple tour in Arashiyama", "Geisha district walk in Gion", "Fushimi Inari shrine hike"],
        "top_attractions": ["Kinkaku-ji (Golden Pavilion)", "Fushimi Inari Taisha", "Bamboo Grove"],
        "average_daily_cost_usd": 150
    },
    {
        "id": "paris-france",
        "name": "Paris",
        "country": "France",
        "description": "Global center for art, fashion, gastronomy, and culture with iconic landmarks along the Seine River.",
        "budget_tier": "luxury",
        "best_season": "Spring / Early Autumn",
        "popular_activities": ["Louvre museum guided tour", "Eiffel Tower sunset viewing", "Pastry tasting in Le Marais"],
        "top_attractions": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral"],
        "average_daily_cost_usd": 250
    },
    {
        "id": "banff-canada",
        "name": "Banff National Park",
        "country": "Canada",
        "description": "Canada's oldest national park nestled in the majestic Rocky Mountains with turquoise glacial lakes and alpine trails.",
        "budget_tier": "moderate",
        "best_season": "Summer / Winter",
        "popular_activities": ["Canoeing on Lake Louise", "Sulfur Mountain gondola ride", "Wildlife spotting in Bow Valley"],
        "top_attractions": ["Lake Louise", "Moraine Lake", "Icefields Parkway"],
        "average_daily_cost_usd": 180
    },
    {
        "id": "cape-town-south-africa",
        "name": "Cape Town",
        "country": "South Africa",
        "description": "Port city on South Africa's southwest coast beneath dramatic Table Mountain, with stunning beaches and winelands.",
        "budget_tier": "budget",
        "best_season": "Summer (Nov - Mar)",
        "popular_activities": ["Table Mountain cableway", "Boulders Beach penguin visit", "Cape Peninsula scenic drive"],
        "top_attractions": ["Table Mountain", "Cape of Good Hope", "Robben Island"],
        "average_daily_cost_usd": 90
    },
    {
        "id": "bali-indonesia",
        "name": "Bali",
        "country": "Indonesia",
        "description": "Tropical Indonesian island known for iconic rice terraces, volcanic mountains, coral reefs, and vibrant culture.",
        "budget_tier": "budget",
        "best_season": "Dry Season (Apr - Oct)",
        "popular_activities": ["Ubud rice terrace walk", "Surfing in Canggu", "Sunset dinner at Uluwatu Temple"],
        "top_attractions": ["Tegallalang Rice Terraces", "Uluwatu Temple", "Mount Batur"],
        "average_daily_cost_usd": 70
    }
]


def seed_database():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info(f"Initializing Firestore client for project: {FIRESTORE_PROJECT_ID}, db: {FIRESTORE_DATABASE_ID}")
    db = firestore.Client(project=FIRESTORE_PROJECT_ID, database=FIRESTORE_DATABASE_ID)

    collection_ref = db.collection(COLLECTION_NAME)

    for item in SAMPLE_DESTINATIONS:
        doc_id = item["id"]
        doc_ref = collection_ref.document(doc_id)
        doc_ref.set(item)
        logger.info(f"Seeded destination document: '{doc_id}' -> {item['name']}, {item['country']}")

    print(f"Successfully seeded {len(SAMPLE_DESTINATIONS)} destinations into Firestore collection '{COLLECTION_NAME}' (project: {FIRESTORE_PROJECT_ID})!")


if __name__ == "__main__":
    seed_database()
