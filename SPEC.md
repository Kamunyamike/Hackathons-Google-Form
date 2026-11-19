Build a complete, production-ready web application in **Next.js (App Router) + TypeScript + Tailwind CSS** that replicates the exact behavior, wording, branching logic, validation, and confirmation flow of the **AfriCDSA Community Opportunities Registration** form. 

I am going to deploy this to get a public URL and share it in WhatsApp community groups, so mobile responsiveness and WhatsApp link-preview metadata (Open Graph tags) are critical.

### 1. Visual Design & UI Enhancement
* **Reference style:** Combine the visual aesthetic, color palette, typography, card styling, and layout polish from my attached images while maintaining a clean, mobile-first, multi-step Google Forms–style experience.
* **Mobile UX:** Use large, single-tap radio cards for all Multiple Choice questions, a clear 3-step progress bar at the top (`Page 1 of 3` -> `Page 2 of 3` -> `Page 3 of 3`), and smooth step transitions without full page reloads.
* **Header:** Include a sleek top banner area (1600x400 aspect ratio equivalent) styled to match the attached UI images.

### 2. WhatsApp Link Preview & Sharing (Open Graph Metadata)
Configure Next.js `Metadata` (`og:title`, `og:description`, `og:image`, `twitter:card`) in `app/layout.tsx` so that pasting the link into a WhatsApp group automatically generates a rich preview card with:
* **Title:** `AfriCDSA Community Opportunities Registration`
* **Description:** `Register in 2 minutes for the AWS Student Builder Group Event (26 Nov 2026) and/or Hack for Inclusion Hackathon (7–9 Jan 2027).`
* **Preview Image:** Generate a clean, high-contrast Open Graph banner image (`public/og-banner.png` or dynamic `opengraph-image.tsx`) matching the UI theme.
* Also include a **"Share on WhatsApp"** button on the confirmation screen that opens `https://wa.me/?text=...` with a pre-filled caption and the live form URL.

### 3. Exact Form Specification (Do NOT alter wording, options, or logic)

#### Form Header (Shown on Page 1)
* **Title:** `AfriCDSA Community Opportunities Registration`
* **Description:**
  > AfriCDSA is inviting students and alumni to participate in upcoming learning, innovation, and professional development opportunities.
  >
  > Current opportunities include:
  > • AWS Student Builder Group Event - Think Like an Architect, Build Like One
  > • Hack for Inclusion Hackathon
  >
  > Complete this short form if you would like to participate in either or both opportunities.
  > Participants interested in the AWS event will receive the official Meetup registration link after submitting this form.
  >
  > Takes about 2 minutes. Your details are used only by the AfriCDSA Community Team to coordinate these opportunities and, if you agree, to share future ones.

---

#### PAGE 1: Basic Information & Opportunity Selection
All questions on Page 1 are **Required**. Do not allow advancing to Page 2 until all validations pass.

1. **Full Name**
   * Type: Short text input
   * Required: Yes
2. **Email Address**
   * Type: Email input
   * Validation: Must be a valid email format
   * Required: Yes
3. **Phone Number**
   * Type: Text input
   * Help text: `WhatsApp number preferred, e.g. 0712345678 or +254712345678`
   * Validation: Regex `^\+?[0-9 ]{10,15}$`
   * Required: Yes
4. **Are you a Student or Alumni?**
   * Type: Single-select (Radio)
   * Options: `Student`, `Alumni`
   * Required: Yes
5. **Current Program or Profession**
   * Type: Short text input
   * Help text: `e.g. Data Science student, or Data Analyst at XYZ Ltd`
   * Required: Yes
* **Sub-heading Divider:** `Opportunity selection`
6. **Which opportunity are you interested in?** *(Branching Question)*
   * Type: Single-select (Radio)
   * Options:
     * `AWS Student Builder Group Event` -> Routes to **Page 2A**
     * `Hack for Inclusion Hackathon` -> Routes to **Page 2B**
     * `Both` -> Routes to **Page 2C**
   * Required: Yes

---

#### PAGE 2: Conditional Event Interest (Render ONLY the branch selected in Q6)

##### Branch 2A: `AWS Event Interest` (Shown ONLY when Q6 = `AWS Student Builder Group Event`)
* **Section Description:** `AWS Student Builder Group Event: Think Like an Architect, Build Like One. Thursday 26 November 2026, 10:00 am to 5:00 pm, MKCC. Note: Participants will receive the official Meetup registration link from the AfriCDSA Community Team.`
* **Q7.** `Are you available to attend the event?` — Radio: `Yes`, `No`, `Not Sure` (Required)
* **Q8.** `Would you like to join the AfriCDSA AWS participant group?` — Radio: `Yes`, `No` (Required)
* **Q9.** `What interests you most?` — Radio: `Cloud Computing`, `Artificial Intelligence`, `AWS Technologies`, `DevOps`, `Networking`, `Career Growth` (Required)
* **Q10.** `After submitting this form, are you willing to complete the official Meetup registration?` — Radio: `Yes`, `No` (Required)
* *Next button routes to Page 3.*

##### Branch 2B: `Hackathon Interest` (Shown ONLY when Q6 = `Hack for Inclusion Hackathon`)
* **Section Description:** `Hack for Inclusion Hackathon: 7 to 9 January 2027, building disability-inclusive solutions. The top five teams receive up to KES 1,000,000 in venture support, a six-month incubation programme and mentorship. Note: You must also apply through the official application form by 4 December 2026. We will send you the link and help you form a team.`
* **Q11.** `Have you participated in a hackathon before?` — Radio: `Yes`, `No` (Required)
* **Q12.** `Would you like to join a team?` — Radio: `Yes`, `No` (Required)
* **Q13.** `Which area interests you?` — Radio: `AI`, `Data Science`, `Accessibility Solutions`, `Software Development`, `Innovation & Entrepreneurship` (Required)
* **Q14.** `Do you already have a project idea?` — Radio: `Yes`, `No` (Required)
* *Next button routes to Page 3.*

##### Branch 2C: `AWS Event and Hackathon Interest` (Shown ONLY when Q6 = `Both`)
* **Section Description:** Combine both descriptions above (separated by a clean line break).
* Display **Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14** in exact order on this single page (all Required).
* *Next button routes to Page 3.*

---

#### PAGE 3: Future Opportunities and Consent (Shown to everyone)
* **Section Title:** `Future opportunities and consent`
* **Q15.** `Would you like to receive information about future opportunities? Tick all that apply.`
  * Type: Multi-select Checkboxes
  * Options: `Training Sessions`, `Hackathons`, `Competitions`, `Mentorship Programs`, `Scholarships`, `Internships`, `Research Projects`, `Community Leadership Opportunities`
  * Required: **No (Optional)**
* **Sub-heading Divider:** `Consent`
* **Q16.** `I agree to be contacted by AfriCDSA regarding:`
  * Type: Multi-select Checkboxes
  * Help text: `Tick Event Updates to receive the Meetup link and event information.`
  * Options: `Event Updates`, `Community Opportunities`, `Future Learning Programs`
  * Validation: **Must select at least 1 option**
  * Required: Yes

---

#### Confirmation / Thank-You Screen (Upon Submit)
* Allow respondents to click **"Edit your response"** (loads their submitted answers back into the form to update their record, matching Google Forms' `Allow response editing` setting). Do NOT show a "Submit another response" link.
* Display the exact confirmation message with clickable links:
  > Thank you for registering with AfriCDSA. Here is what to do next.
  >
  > **AWS Student Builder Group Event (Thursday 26 November, 10am to 5pm, MKCC):** Your place is confirmed only after you register on the official Meetup page. Please do it now: https://www.meetup.com/aws-sbg-at-mount-kenya-university-thika-town-campus/events/3174261 Then reply "REGISTERED" to the AfriCDSA Community Team on WhatsApp. We will add you to the AfriCDSA AWS participant group.
  >
  > **Hack for Inclusion Hackathon (7 to 9 January 2027):** Submit the official application by 4 December 2026: https://forms.cloud.microsoft/r/YTeSBsC9rF We will contact you about teams and support.
  >
  > Know someone who should join us? Share this form: *[Display dynamic shareable URL + Copy Link button + WhatsApp Share button]*

---

### 4. Multi-Format Storage & Admin Dashboard (`/admin`)
Build a password-protected admin route (`/admin`, using an `ADMIN_PASSWORD` environment variable) plus backend API routes (`/api/submit`, `/api/export`) that store and export responses in multiple formats:
1. **Primary Database Storage:** Store submissions in a structured database (e.g., SQLite via Prisma or Supabase/Postgres—default to local SQLite/JSON file storage so it works immediately out of the box in VS Code without extra setup, with clean adapter support for Postgres/Supabase when deployed).
2. **Automatic Google Sheets Sync (Optional Webhook):** Support an optional `GOOGLE_SHEETS_WEBHOOK_URL` environment variable so every submission can also automatically append a row to a Google Sheet (`AfriCDSA Opportunities 2026`). Include the 5-line Google Apps Script snippet in a `README.md` if the user wants live Google Sheets sync without OAuth verification issues.
3. **One-Click Multi-Format Exports from `/admin`:**
   * **Download Excel (`.xlsx`)** (using `xlsx` / SheetJS) — Automatically generate two sheets inside the workbook:
     * `Form Responses 1` (raw columns matching Google Forms)
     * `Tracker` (pre-populated with merged Q7–Q14 columns so `Both` respondents align cleanly with single-event respondents, plus tracking columns: `AWS status`, `In AWS participant group`, `Hackathon status`, `Hackathon team`, `Shared learnings after event`)
   * **Download CSV (`.csv`)**
   * **Download PDF Summary Report (`.pdf`)** (using `jspdf` + `jspdf-autotable`) containing registration funnel counts (AWS vs. Hackathon vs. Both) and a clean table of all registrants.
   * **Individual Submission PDF Receipt:** Allow exporting any single registration as a formatted PDF.

### 5. Deliverables
Generate the complete project file structure, install commands, `.env.example`, and a clear `README.md` explaining how to run locally in VS Code and deploy to Vercel so the WhatsApp link is live immediately.