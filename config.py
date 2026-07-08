"""Project configuration.

Edit these constants for your local environment. For production use
store secrets in environment variables or a proper secrets manager.
"""

# Bot tokens used by the main controller and the second (payload) bot.
# These values in the repository are placeholders — replace with real
# tokens when running the system.
TOKEN = '8837786862:AAG5ojj6XNXr1rIv6FHupAFQdsKsrJHL50Q'
PAYLOAD_BOT_TOKEN = '8656129474:AAFjMhWj8W3OgzzfOzQ5Zi30ZC9HOSWo0yo'

# Master secret and salt for key derivation. Change before use.
MASTER_SECRET = 'CHANGE_THIS_TO_RANDOM_STRING_123456789'
SALT = b'fixed_salt_for_key_derivation_32bytes_12345'

# Runtime behavior tuning
POLLING_INTERVAL = 2  # seconds between polls (where applicable)
MAX_RETRIES = 5