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
DOCUMENT_SOURCE_CONFIG = f"{DOCUMENTS_ID}/source-config"
DOCUMENT_SOURCE_CONFIG_GROUP = f"{DOCUMENT_SOURCE_CONFIG}/groups/{{group_id}}"
DOCUMENT_SOURCE_CONFIG_SOURCE = f"{DOCUMENT_SOURCE_CONFIG}/sources/{{source_id}}"
DOCUMENT_CITATIONS = f"{DOCUMENTS_ID}/citations"

# Document content suggest
DOCUMENT_CONTENT_SUGGEST = f"{DOCUMENTS_ID}/content/suggest"

# Conversations
CONVERSATIONS = "/conversations"
CONVERSATIONS_ID = f"{CONVERSATIONS}/{{id_}}"
CONVERSATION_MESSAGES = f"{CONVERSATIONS_ID}/messages"

# Sources
SOURCES = "/sources"
SOURCES_ID = f"{SOURCES}/{{id_}}"
SOURCE_SYNC = f"{SOURCES_ID}/sync"
SOURCE_SYNC_STATUS = f"{SOURCES_ID}/sync-status"
PLUGINS_AVAILABLE_SOURCES = f"{PLUGINS_ID}/available-sources"

# Content
CONTENTS = "/content"
CONTENTS_ID = f"{CONTENTS}/{{id_}}"
CONTENT_SEARCH = f"{CONTENTS}/search"

# Source groups
SOURCE_GROUPS = "/source-groups"
SOURCE_GROUPS_ID = f"{SOURCE_GROUPS}/{{id_}}"
SOURCE_GROUP_MEMBERS = "/source-group-members"
SOURCE_GROUP_MEMBERS_ID = f"{SOURCE_GROUP_MEMBERS}/{{id_}}"
SOURCE_GROUP_CONTENT = f"{SOURCE_GROUPS_ID}/content"

# Citations
CITATIONS_ID = "/citations/{id_}"
