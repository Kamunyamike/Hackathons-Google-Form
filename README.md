# AfriCDSA Community Opportunities Registration

A mobile-first, three-page registration form built with Streamlit. Supabase stores registrations, edit tokens, and tracker follow-up data.

## Run locally

Install Python 3.11, then open a terminal in this project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app needs Supabase credentials before it can read or save responses.

## Supabase setup

1. Create a free project at [supabase.com](https://supabase.com). Choose a region near Kenya, such as `eu-central` or `eu-west`.
2. Open **SQL Editor**, paste the contents of [`supabase/schema.sql`](./supabase/schema.sql), and run it. This creates `public.responses` and enables row-level security without adding public policies.
3. Open **Project Settings → API** (or **API Keys**) and copy the **Project URL** and the **service_role (secret) key**.
4. For local development, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set:

   ```toml
   [supabase]
   url = "https://YOUR-PROJECT-REF.supabase.co"
   service_role_key = "your-service-role-key"
   ```

   Keep the `[admin]` and `[app]` sections from the example and replace their placeholder values too. For Streamlit Community Cloud, paste the same TOML into **App settings → Secrets**.
5. Save the secrets and reboot the app if it does not restart automatically.

**Keep the service-role key secret.** It bypasses row-level security and must only be stored in Streamlit secrets—never in source code or GitHub. The public anon key is not used by this server-side app.

Submissions are available in Supabase under **Table Editor → responses**. The `edit_token` is stored separately from response records, and `follow_up` preserves the admin Tracker fields. The Tracker is computed live; use **Refresh tracker** to clear cached data and reload it.

Existing Google Sheets responses are not imported automatically. Export or migrate them separately if they need to remain available in Supabase.

## Admin

Open the deployed app's `/admin` page and log in with the password configured in `[admin]`. The page provides searchable responses, counts, Excel/CSV/PDF downloads, individual PDF receipts, and the Tracker. Admin tables and downloads do not display edit tokens.

## Deploy for free

1. Push this project to a public GitHub repository without `.streamlit/secrets.toml`.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect GitHub, and deploy `streamlit_app.py`. Select Python 3.11 in the deployment settings.
3. Choose a custom subdomain such as `africdsa-registration.streamlit.app`.
4. In the deployed app's **App settings → Secrets**, set `[app] public_url` to the final public URL.
5. Add the `[supabase]` settings described above, then reboot the app if necessary.

The app sleeps after 12 hours without visitors. Open it yourself before posting the link in WhatsApp groups.

## Local verification

Run the unit tests with:

```powershell
python -m pytest -q
```

For an end-to-end check, configure Supabase secrets, submit one response for each choice in **Which opportunity are you interested in?** (AWS, Hackathon, and Both), and confirm the selected branch answers and tracker columns are correct. Use each confirmation's **Edit your response** link and verify resubmitting updates the same response. Also verify invalid email/phone values and missing required answers block progression/submission, then log in at `/admin` and download the Excel workbook, CSV, PDF summary, and an individual PDF receipt.
