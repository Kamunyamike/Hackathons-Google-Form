# AfriCDSA Community Opportunities Registration

A mobile-first, three-page registration form built with Streamlit. Google Sheets is the only persistent data store.

## 1. Run locally

Install Python 3.11, then open a terminal in this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app requires Google Sheets credentials before it can read or save responses. Configure those credentials in the next section.

## 2. Create and share the Google Sheet

1. In Google Cloud Console, create a project.
2. Enable **Google Sheets API** and **Google Drive API** for that project.
3. Create a service account and download its JSON key.
4. Create a Google spreadsheet named **AfriCDSA Opportunities 2026**.
5. Share the spreadsheet with the service account's `client_email` as an **Editor**.
6. Copy the spreadsheet ID from its URL (the text between `/d/` and `/edit`).

The app creates the `Form Responses 1` worksheet and its header row when needed. It also creates a `Tracker` worksheet for the admin rebuild action.

## 3. Configure secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`. Fill in the service-account JSON fields, spreadsheet ID, admin password, and public app URL. Keep `.streamlit/secrets.toml` private; it is ignored by Git.

For Streamlit Community Cloud, paste the same TOML content into **App settings → Secrets**. Do not commit credentials or the secrets file.

### Fixing "Google Sheets is not configured" on the deployed app

This message means the deployed app has no Google Sheets secrets. The app needs `[gcp_service_account]` and `sheets.spreadsheet_id` (see `lib/sheets.py`); the message lists exactly which keys are missing.

1. Go to [share.streamlit.io](https://share.streamlit.io), open the app's **⋮ menu → Settings → Secrets**.
2. Paste the whole contents of `.streamlit/secrets.toml.example`, then replace every placeholder with the values from your service-account JSON key file:
   - `project_id`, `private_key_id`, `client_email`, `client_id`, `client_x509_cert_url` → copy from the JSON.
   - `private_key` → copy the full key, including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines, inside the triple quotes `"""..."""`. (A key pasted on one line with `\n` sequences also works.)
   - `sheets.spreadsheet_id` → the long ID between `/d/` and `/edit` in the Google Sheet URL.
   - `admin.password` and `app.public_url` → your admin password and the app's live URL.
3. Click **Save**. The app restarts with the new secrets (use **Reboot app** if it doesn't).
4. In Google Sheets, click **Share**, paste the service account's `client_email` (ends in `.iam.gserviceaccount.com`), set it to **Editor**, untick "Notify people", and click **Share**.
5. Make sure the spreadsheet is named exactly **AfriCDSA Opportunities 2026**.

If something is still wrong, the app now names the problem: missing keys, sheet not shared with the service account, wrong spreadsheet ID, bad private key, or wrong sheet name.

## 4. Deploy for free

1. Push this project to a **public GitHub repository**, without `.streamlit/secrets.toml`.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect GitHub, and deploy `streamlit_app.py`. Select Python 3.11 in the deployment settings.
3. Choose a custom subdomain such as `africdsa-registration.streamlit.app`.
4. In the deployed app's **App settings → Secrets**, set `[app] public_url` to the final public URL, for example `https://africdsa-registration.streamlit.app`.
5. Confirm the Google Sheet is shared with the service-account email as Editor.

The app sleeps after 12 hours without visitors. Open it yourself before posting the link in WhatsApp groups.

## Admin

Open the deployed app's `/admin` page and log in with the password configured in `[admin]`. The page provides searchable responses, counts, Excel/CSV/PDF downloads, individual PDF receipts, and a **Rebuild Tracker sheet** button. Admin tables and downloads do not display edit tokens.

The `Tracker` worksheet keeps the team's five follow-up columns when rebuilt, matching existing values by Response ID.

## Local end-to-end verification

After setting up Google Cloud and secrets, start the app and submit one response for each choice in **Which opportunity are you interested in?**: AWS, Hackathon, and Both. Confirm the `Form Responses 1` rows populate only the selected branch columns and that `Tracker` merges Q7–Q14 into one set. Use each confirmation's **Edit your response** link and verify that resubmitting updates the same row.

Also verify that invalid email/phone values and missing required answers block progression/submission, then log in at `/admin` and download the Excel workbook, CSV, PDF summary, and one individual PDF receipt. The live Sheet, service-account key, admin password, and hosted URL are deployment-specific, so these Google Sheets integration checks must be run with your configured account.
