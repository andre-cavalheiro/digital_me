# Halo Webapp Initial Setup - LLM Script Template

This document serves as an **executable script for an LLM** to properly configure a Halo Webapp project for a specific use case. Simply define the variables below and paste this entire document into an LLM.

---

## 🎯 CONFIGURATION VARIABLES (Edit these)

```python
# Define your project configuration here
PROJECT_NAME = "Digital Me"                    # Display name for the app (e.g., "Digital Me", "Task Manager")
PROJECT_SUBTITLE = "AI Writing Assistant"      # Subtitle/tagline (e.g., "AI Writing Assistant", "Productivity Dashboard")
PROJECT_DESCRIPTION = "AI-assisted writing with content from your curated sources"

# Docker and Kubernetes configuration
DOCKER_IMAGE = "andrecavalheiro/digital-me-webapp"      # Docker image name for container registry
KUBERNETES_NAMESPACE = "digital-me"                      # Kubernetes namespace for deployment
KUBERNETES_CLUSTER = "kratos"                            # Kubernetes cluster name (default: "kratos")
HELM_SERVICE = "digital-me-webapp"                       # Helm service name

# Helm configuration
HELM_CHART_NAME = "digital-me-webapp"
HELM_CHART_DESCRIPTION = "Digital Me Web App - AI-assisted writing interface"
SERVICE_PORT = 3001                                      # Port the service will run on

# UI Metadata
PAGE_TITLE = "Digital Me"                                # Browser tab title
PAGE_DESCRIPTION = "AI-assisted writing with content from your curated sources"

# Navigation configuration
NAV_ITEMS = [                                            # Navigation menu items
    {"label": "Home", "href": "/"},
    {"label": "Plugins", "href": "/plugins"},
    {"label": "Writing", "href": "/writing"},
]

# Package metadata
PACKAGE_NAME = "digital-me-webapp"                       # NPM package name (kebab-case)
PACKAGE_DESCRIPTION = "Digital Me - AI-assisted writing platform"
PACKAGE_VERSION = "0.1.0"
```

---

## 📝 INSTRUCTIONS FOR LLM

You are tasked with configuring a Halo Webapp (Next.js) project for a specific use case. Use the configuration variables defined above to update all required files. Follow these steps **exactly**:

---

### Step 1: Update Makefile

**File:** `Makefile`

**Action:** Update the following variables at the top of the Makefile:

```makefile
DOCKER_IMAGE := {DOCKER_IMAGE}
KUBERNETES_NAMESPACE := {KUBERNETES_NAMESPACE}
KUBERNETES_CLUSTER := {KUBERNETES_CLUSTER}
HELM_SERVICE := {HELM_SERVICE}
```

**Instructions:**
- Locate the existing variable definitions in the Makefile
- Replace empty or placeholder values with the configured values
- Keep all other Makefile content unchanged
- Ensure proper Makefile syntax (`:=` for assignment, no quotes around values)

**Example:**
```makefile
DOCKER_IMAGE := andrecavalheiro/digital-me-webapp
KUBERNETES_NAMESPACE := digital-me
KUBERNETES_CLUSTER := kratos
HELM_SERVICE := digital-me-webapp
```

---

### Step 2: Update Helm Chart Metadata

**File:** `deploy/helm/Chart.yaml`

**Action:** Update the chart metadata:

```yaml
apiVersion: v2
name: {HELM_CHART_NAME}
description: {HELM_CHART_DESCRIPTION}
version: 0.1.0
appVersion: "1.0"
type: application
```

**Instructions:**
- Update the `name` field with the HELM_CHART_NAME value
- Update the `description` field with the HELM_CHART_DESCRIPTION value
- Keep the version, appVersion, and type fields as shown
- Maintain proper YAML formatting

---

### Step 3: Update Helm Values

**File:** `deploy/helm/values.yaml`

**Action:** Update the image repository and service port:

Locate the `image` section and update:
```yaml
image:
  repository: {DOCKER_IMAGE}
  pullPolicy: IfNotPresent
  tag: "latest"
```

Locate the `service` section and update:
```yaml
service:
  type: ClusterIP
  port: {SERVICE_PORT}
```

**Instructions:**
- Only update the `repository` field in the `image` section
- Only update the `port` field in the `service` section
- Keep all other values.yaml content unchanged
- Maintain proper YAML formatting and indentation

---

### Step 4: Update Application Layout Metadata

**File:** `src/app/layout.tsx`

**Action:** Locate the `metadata` export and update:

```typescript
export const metadata: Metadata = {
  title: "{PAGE_TITLE}",
  description: "{PAGE_DESCRIPTION}",
};
```

**Instructions:**
- Find the `metadata` constant (usually near the top of the file)
- Update only the `title` and `description` fields
- Keep all other metadata fields unchanged
- Maintain proper TypeScript syntax
- Preserve all other imports and component code

**Example:**
```typescript
export const metadata: Metadata = {
  title: "Digital Me",
  description: "AI-assisted writing with content from your curated sources",
};
```

---

### Step 5: Update Sidebar Configuration

**File:** `src/components/sidebar.tsx`

**Action:** Update the sidebar branding and navigation:

Locate the project name section and update:
```typescript
<div className="flex items-center gap-2 px-2 py-1.5">
  <div className="flex flex-col">
    <span className="text-sm font-semibold">{PROJECT_NAME}</span>
    <span className="text-xs text-muted-foreground">{PROJECT_SUBTITLE}</span>
  </div>
</div>
```

Locate the navigation items section and update:
```typescript
const navItems = {GENERATE_NAV_ITEMS_ARRAY};
```

**Instructions:**
- Find the sidebar header/branding section (usually contains project name and subtitle)
- Update the project name with PROJECT_NAME value
- Update the subtitle with PROJECT_SUBTITLE value
- Find the navigation items array (may be called `navItems`, `menuItems`, or similar)
- Update with NAV_ITEMS configuration
- Keep all other sidebar functionality unchanged
- Maintain proper TypeScript/JSX syntax

**Example nav items array:**
```typescript
const navItems = [
  {
    title: "Home",
    url: "/",
    icon: Home,
  },
  {
    title: "Plugins",
    url: "/plugins",
    icon: Puzzle,
  },
  {
    title: "Writing",
    url: "/writing",
    icon: FileText,
  },
];
```

---

### Step 6: Update Package Metadata

**File:** `package.json`

**Action:** Locate the root object and update:

```json
{
  "name": "{PACKAGE_NAME}",
  "version": "{PACKAGE_VERSION}",
  "description": "{PACKAGE_DESCRIPTION}",
  "private": true,
  "scripts": {
    // ... keep unchanged
  },
  "dependencies": {
    // ... keep unchanged
  }
}
```

**Instructions:**
- Update the `name` field with the PACKAGE_NAME value
- Update the `version` field if different from current
- Update the `description` field with the PACKAGE_DESCRIPTION value
- Keep all `scripts`, `dependencies`, and `devDependencies` unchanged
- Maintain proper JSON formatting

**Example:**
```json
{
  "name": "digital-me-webapp",
  "version": "0.1.0",
  "description": "Digital Me - AI-assisted writing platform",
  "private": true,
  ...
}
```

---

## 🔌 PLUGIN CONFIGURATION (Human Decision Required)

**Note for LLM:** The following section describes plugin configuration that requires **human decision-making** and is **outside the scope of automated LLM scripting**. Include this section in any output to inform the human user about additional manual steps needed.

### Plugin Data Sources Setup

**File to review:** `src/lib/plugin-data-sources.ts`

The Halo Webapp includes a plugin system for integrating with external data sources. The configuration defines which plugin types the application supports and their metadata.

#### Current Default Plugins:
The file may include examples like:
- **Cloudflare** - Managed subdirectory hosting
- **Namecheap** - Managed subdirectory hosting
- Other placeholder integrations

#### Human Actions Required:
1. **Review** the `plugin-data-sources.ts` file to see the current plugin type definitions
2. **Decide** which data sources are needed for your use case:
   - For Digital Me: Twitter, Substack, Medium, RSS, Notion, Readwise, Pocket, GitHub, etc.
   - For other use cases: Choose relevant integrations
3. **Add/Remove** plugin type definitions as needed:
   ```typescript
   export type PluginDataSourceId =
     | "twitter"
     | "substack"
     | "medium"
     | "rss"
     // ... etc

   export const pluginDataSources: Record<PluginDataSourceId, PluginDataSourceConfig> = {
     twitter: {
       id: "twitter",
       name: "Twitter/X",
       description: "Sync tweets and bookmarks",
       icon: TwitterIcon,
       // ... configuration
     },
     // ... other sources
   };
   ```
4. **Implement OAuth flows** and credential management for each plugin type
5. **Create UI components** for plugin configuration pages
6. **Update backend** (fury_api) to support the same plugin types

#### Example Decision Process for Digital Me:
- **Content aggregation app?** → Add Twitter, Substack, Medium, RSS, Notion
- **Writing assistant?** → Add grammar checkers, Google Docs integration
- **Research tool?** → Add Readwise, Pocket, scholarly databases
- **Blog platform?** → Keep hosting providers like Cloudflare, Vercel

**This configuration cannot be automated and requires human judgment based on the application's purpose and user needs.**

---

## ✅ VERIFICATION CHECKLIST

After generation, verify the following:

- [ ] `Makefile` updated with correct values:
  - [ ] DOCKER_IMAGE set to your Docker registry image
  - [ ] KUBERNETES_NAMESPACE set to your deployment namespace
  - [ ] KUBERNETES_CLUSTER set appropriately
  - [ ] HELM_SERVICE set to match your project
- [ ] `deploy/helm/Chart.yaml` updated:
  - [ ] `name` field matches HELM_CHART_NAME
  - [ ] `description` field describes your project
- [ ] `deploy/helm/values.yaml` updated:
  - [ ] `image.repository` matches DOCKER_IMAGE
  - [ ] `service.port` matches SERVICE_PORT
- [ ] `src/app/layout.tsx` updated:
  - [ ] `metadata.title` reflects your project name
  - [ ] `metadata.description` describes your project
- [ ] `src/components/sidebar.tsx` updated:
  - [ ] Project name reflects your branding
  - [ ] Subtitle/tagline updated
  - [ ] Navigation items match your app structure
- [ ] `package.json` updated:
  - [ ] `name` matches PACKAGE_NAME
  - [ ] `description` describes your project
  - [ ] `version` is appropriate
- [ ] Plugin decisions documented (human action item)

---

## 🎨 CONCRETE EXAMPLE: Digital Me Project

Here's a complete example for the "Digital Me" AI-assisted writing platform:

### Configuration:
```python
PROJECT_NAME = "Digital Me"
PROJECT_SUBTITLE = "AI Writing Assistant"
PROJECT_DESCRIPTION = "AI-assisted writing with content from your curated sources"

DOCKER_IMAGE = "andrecavalheiro/digital-me-webapp"
KUBERNETES_NAMESPACE = "digital-me"
KUBERNETES_CLUSTER = "kratos"
HELM_SERVICE = "digital-me-webapp"

HELM_CHART_NAME = "digital-me-webapp"
HELM_CHART_DESCRIPTION = "Digital Me Web App - AI-assisted writing interface"
SERVICE_PORT = 3001

PAGE_TITLE = "Digital Me"
PAGE_DESCRIPTION = "AI-assisted writing with content from your curated sources"

NAV_ITEMS = [
    {"label": "Home", "href": "/"},
    {"label": "Plugins", "href": "/plugins"},
    {"label": "Writing", "href": "/writing"},
]

PACKAGE_NAME = "digital-me-webapp"
PACKAGE_DESCRIPTION = "Digital Me - AI-assisted writing platform"
PACKAGE_VERSION = "0.1.0"
```

### Result:
- Makefile configured for `digital-me` namespace and Docker image
- Helm charts branded as "Digital Me Web App"
- Browser tab shows "Digital Me" title
- Sidebar shows "Digital Me" branding with "AI Writing Assistant" subtitle
- Navigation includes Writing page for the editor interface
- Package.json ready for `npm install` and deployment
- Ready for plugin decisions (Twitter, Substack, RSS, etc.)

---

## 🚀 USAGE

1. Copy this entire document
2. Edit the **CONFIGURATION VARIABLES** section with your project details
3. Paste into an LLM (Claude, GPT-4, etc.) with the prompt:

   > "Using the configuration variables defined at the top, update all files specified in the instructions following the Halo Webapp setup pattern. Provide the complete updated content for each file."

4. Copy the updated file contents into your project
5. Review the Plugin Configuration section and make human decisions about which data sources to support
6. Run `npm install` to install dependencies
7. Configure environment variables:
   - Copy `.env.local.example` to `.env.local` (if exists)
   - Set `NEXT_PUBLIC_API_URL` to your fury_api endpoint
   - Add Firebase configuration
8. Start the dev server: `npm run dev`
9. Build for production: `npm run build`

---

## 🔧 NEXT STEPS AFTER SETUP

After completing this initial setup, you may want to:

1. **Configure API integration**
   - Update `NEXT_PUBLIC_API_URL` in `.env.local`
   - Test connection to fury_api backend
   - Verify authentication flow works

2. **Set up Firebase**
   - Configure Firebase project in `.env.local`
   - Update Firebase config in the app
   - Test login/signup flow

3. **Build core features**
   - Create main application pages
   - Implement plugin configuration UI
   - Build data visualization components
   - Add real-time updates with WebSockets

4. **Customize styling**
   - Update `globals.css` with brand colors
   - Customize UI components from `src/components/ui/`
   - Add custom fonts if needed

5. **Add plugin integrations**
   - Review and update `src/lib/plugin-data-sources.ts`
   - Implement OAuth flows for each data source
   - Create plugin configuration pages
   - Build credential management UI

6. **Deploy to Kubernetes**
   - Build Docker image: `make build`
   - Push to registry: `make push`
   - Deploy with Helm: `make deploy`

---

## 📚 ARCHITECTURE OVERVIEW

The Halo Webapp is built with modern Next.js and follows best practices:

- **Framework**: Next.js 15 with App Router
  - Server and client components
  - API routes for backend communication
  - Server-side rendering (SSR) and static generation

- **UI Components**: Radix UI + shadcn/ui
  - Accessible, composable components
  - Customizable with Tailwind CSS
  - Dark mode support built-in

- **Authentication**: Firebase Authentication
  - Email/password, Google, GitHub, etc.
  - JWT token management
  - Protected routes with middleware

- **API Communication**: Axios
  - Centralized API client
  - Request/response interceptors
  - Error handling

- **State Management**: React hooks + Context API
  - Local state with useState/useReducer
  - Global state with Context
  - Can be extended with Zustand or Jotai if needed

- **Form Handling**: React Hook Form + Zod
  - Type-safe form validation
  - Schema-based validation
  - Clean form state management

- **Styling**: Tailwind CSS
  - Utility-first CSS
  - Responsive design
  - Custom theme configuration

The setup ensures:
- ✅ Fast development with hot reload
- ✅ Type safety with TypeScript
- ✅ Responsive design out of the box
- ✅ Accessible UI components
- ✅ Production-ready build optimization
- ✅ SEO-friendly with Next.js metadata API
- ✅ Easy deployment with Docker + Kubernetes
