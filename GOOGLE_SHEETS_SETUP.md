# Google Sheets API Setup Guide

Follow these steps to set up Google Sheets API access:

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "NEW PROJECT"
3. Name it (e.g., "LinkedIn Job Scraper") → Click "CREATE"

## Step 2: Enable Google Sheets API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Google Sheets API"
3. Click on it → Click "ENABLE"

## Step 3: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "+ CREATE CREDENTIALS" → "Service account"
3. Fill in:
   - Service account name: `linkedin-scraper`
   - Description: `Service account for LinkedIn job scraper`
4. Click "CREATE AND CONTINUE"
5. Skip role selection (not needed for Sheets API) → Click "CONTINUE"
6. Click "DONE"

## Step 4: Generate JSON Key

1. Click on the newly created service account
2. Go to "KEYS" tab
3. Click "ADD KEY" → "Create new key"
4. Select JSON format → Click "CREATE"
5. Save the downloaded JSON file as `credentials.json` in this project folder

## Step 5: Create Google Sheet

1. Go to [Google Sheets](https://sheets.google.com/)
2. Create a new spreadsheet (e.g., "LinkedIn Jobs")
3. Note the **Spreadsheet ID** from the URL:
   - URL: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the `SPREADSHEET_ID` part

## Step 6: Share Sheet with Service Account

1. In your Google Sheet, click "Share" button
2. Copy the **client_email** from your `credentials.json` file
3. Paste the email and give it "Editor" access
4. Click "Done"

## Step 7: Update .env File

Add these to your `.env` file:

```
# Google Sheets Configuration
GOOGLE_SHEET_ID=your_spreadsheet_id_here
GOOGLE_CREDENTIALS_FILE=credentials.json
```

## Step 8: Install Dependencies

```bash
pip install gspread google-auth google-auth-oauthlib google-auth-httplib2
```

## Directory Structure

Your project should look like:
```
linkedin_scraper/
├── credentials.json          # Service account key (keep private!)
├── .env                      # Contains GOOGLE_SHEET_ID
├── linkedin_session.json     # LinkedIn session (keep private!)
└── ...
```

## Security Notes

- Never commit `credentials.json` or `linkedin_session.json` to git
- Keep these files secure - they contain authentication credentials
- The `.gitignore` already excludes these files
