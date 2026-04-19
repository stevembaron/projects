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
