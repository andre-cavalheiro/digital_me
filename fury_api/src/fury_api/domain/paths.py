API_ROOT = "/api/v1"

HEALTH_CHECK = "/health"
HEALTH_CHECK_VELINI = "/health/velini"

ORGANIZATIONS = "/organizations"
ORGANIZATIONS_SELF = f"{ORGANIZATIONS}/self"

USERS = "/users"
USERS_SELF = f"{USERS}/self"
USERS_ID = f"{USERS}/{{id_}}"

ADMIN = "/admin"
ADMIN_ORGANIZATIONS = f"{ADMIN}/organizations"

PLUGINS = "/plugins"
PLUGINS_ID = f"{PLUGINS}/{{id_}}"

# Documents
DOCUMENTS = "/documents"
DOCUMENTS_ID = f"{DOCUMENTS}/{{id_}}"
DOCUMENT_CONTENT = f"{DOCUMENTS_ID}/content"
DOCUMENT_CONVERSATIONS = f"{DOCUMENTS_ID}/conversations"

# Conversations
CONVERSATIONS = "/conversations"
CONVERSATIONS_ID = f"{CONVERSATIONS}/{{id_}}"
CONVERSATION_MESSAGES = f"{CONVERSATIONS_ID}/messages"
CONVERSATION_MESSAGES_STREAM = f"{CONVERSATION_MESSAGES}/stream"

# Authors
AUTHORS = "/authors"
AUTHORS_ID = f"{AUTHORS}/{{id_}}"
AUTHORS_ID_PARAM = "id_"
AUTHORS_ID_CONTENT = f"{AUTHORS_ID}/content"

# Collections
COLLECTIONS = "/collections"
COLLECTIONS_ID = f"{COLLECTIONS}/{{id_}}"
COLLECTIONS_ID_PARAM = "id_"
COLLECTIONS_ID_CONTENT = f"{COLLECTIONS_ID}/content"
COLLECTIONS_ID_AUTHOR_STATISTICS = f"{COLLECTIONS_ID}/author-statistics"

# Content
CONTENTS = "/content"
CONTENTS_ID = f"{CONTENTS}/{{id_}}"
CONTENTS_BATCH = f"{CONTENTS}/batch"
CONTENT_SEARCH = f"{CONTENTS}/search"
