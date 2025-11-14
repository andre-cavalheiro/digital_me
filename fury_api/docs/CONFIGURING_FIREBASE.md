# Firebase Configuration

This application uses **Firebase Authentication** for user management. Before running the application locally or deploying it, you need to set up a Firebase project and configure the required environment variables.

## Step 1: Create a Firebase Project

If you don't already have a Firebase project:

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Click **Add project** (or select an existing one)
3. Follow the setup wizard to create your project

## Step 2: Obtain Service Account Credentials (Required for API)

The backend API requires Firebase Admin SDK credentials to verify authentication tokens:

1. **Navigate to Project Settings:**
   - Click on the **⚙️ Gear Icon** in the left menu
   - Select **Project settings**

2. **Go to the "Service accounts" Tab:**
   - Click on the **Service accounts** tab
   - Scroll down and click **Generate new private key**
   - Click **Generate key** in the confirmation dialog

3. **Download the JSON file:**
   - A `.json` file will be downloaded containing your service account credentials
   - This file contains sensitive information - **never commit it to version control**

4. **Extract the following values for your API `.env` file:**
   ```bash
   FURY_FIREBASE_PROJECT_ID=<project_id>
   FURY_FIREBASE_PRIVATE_KEY_ID=<private_key_id>
   FURY_FIREBASE_PRIVATE_KEY=<private_key>
   FURY_FIREBASE_CLIENT_EMAIL=<client_email>
   FURY_FIREBASE_CLIENT_ID=<client_id>
   FURY_FIREBASE_CLIENT_X509_CERT_URL=<client_x509_cert_url>
   ```

## Step 3: Obtain Web API Key (Optional for API setup, only required for a Webapp)

The frontend webapp needs the Firebase Web API key for client-side authentication:

1. **Navigate to Project Settings:**
   - Click on the **⚙️ Gear Icon** in the left menu
   - Select **Project settings**

2. **Go to the "General" Tab:**
   - Scroll down to the **"Your apps"** section
   - If you already have a web app, click on it to find the configuration
   - If not, click **Add app** → Choose **Web** (</>) and register your app

3. **Copy the Firebase SDK configuration:**
   - Look for the **"Firebase SDK snippet"** section
   - Select **"Config"** format
   - You'll see something like:
     ```javascript
     const firebaseConfig = {
       apiKey: "AIza...",
       authDomain: "your-project.firebaseapp.com",
       projectId: "your-project",
       // ... other fields
     };
     ```

4. **Extract the following values for your webapp `.env.local` file:**
   ```bash
   NEXT_PUBLIC_FIREBASE_API_KEY=<apiKey>
   NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=<authDomain>
   NEXT_PUBLIC_FIREBASE_PROJECT_ID=<projectId>
   ```

5. **Also add the API Web Key to your API `.env` file:**
   ```bash
   FURY_FIREBASE_WEB_API_KEY=<apiKey>  # Same value as NEXT_PUBLIC_FIREBASE_API_KEY
   ```

## Step 4: Enable Authentication Methods

Enable the authentication methods you want to use:

1. In the Firebase Console, go to **Authentication** in the left menu
2. Click on the **Sign-in method** tab
3. Enable Google as the only authentication providers (this system as is, is only prepared for Google)
