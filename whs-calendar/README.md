# WHS Calendar Tracker

Upload a WHS calendar PDF, review the imported events, and sync selected events to Google Calendar.

## Run

From the repo root:

```sh
python3 -m http.server 8081
```

Open:

```text
http://localhost:8081/whs-calendar/
```

After GitHub Pages deploys, open:

```text
https://stevembaron.github.io/projects/whs-calendar/index.html
```

## Google Calendar Setup

1. Create a Google Cloud project.
2. Enable the Google Calendar API.
3. Create an OAuth client ID for a web application.
4. Add the local origin you use, such as `http://localhost:8081`, to Authorized JavaScript origins.
5. Paste the OAuth client ID into the app, connect Google, then choose the existing family calendar from the calendar picker.

If the family calendar does not appear, make sure your Google account has permission to make changes to that calendar. You can also paste the family calendar ID manually.

The app stores events and Google settings in browser local storage. Uploading a newer PDF in the same format merges matching events and adds new ones.

## Easier Family Calendar Option

If you do not want to set up a Google OAuth client, use **Download ICS** in the app. In Google Calendar, import that `.ics` file into the existing family calendar.

## Auto Publish Setup

For the closest thing to magic, use the included `google-apps-script.js` file:

1. Go to <https://script.google.com/> and create a new project.
2. Paste the contents of `google-apps-script.js` into `Code.gs`.
3. Replace `replace-this-with-a-long-random-secret` with a private phrase.
4. In Apps Script settings, set the project timezone to `America/Denver`.
5. Deploy as a web app.
6. Set **Execute as** to yourself.
7. Set **Who has access** to anyone with the link.
8. Authorize the script when Google asks.
9. Copy the web app URL into the WHS app.
10. Paste the same private phrase into **Publish Secret**.
11. Put the family calendar ID in **Calendar ID**.

After that, **Publish Changes** will delete only WHS events created by the script and recreate the current PDF events. If **Auto publish after PDF import** is checked, uploading a new PDF triggers that replace flow automatically.
