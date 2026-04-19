const WHS_SECRET = "replace-this-with-a-long-random-secret";
const WHS_MARKER = "WHS_CALENDAR_TRACKER_MANAGED_EVENT";

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    if (payload.secret !== WHS_SECRET) return json({ ok: false, error: "Bad secret" });
    if (!payload.calendarId) return json({ ok: false, error: "Missing calendarId" });
    if (!Array.isArray(payload.events)) return json({ ok: false, error: "Missing events" });

    const calendar = CalendarApp.getCalendarById(payload.calendarId);
    if (!calendar) return json({ ok: false, error: "Calendar not found" });

    const dates = payload.events.map((event) => event.date).sort();
    if (!dates.length) return json({ ok: false, error: "No events to publish" });

    const start = addDays(parseLocalDate(dates[0]), -2);
    const end = addDays(parseLocalDate(dates[dates.length - 1]), 3);
    calendar.getEvents(start, end).forEach((event) => {
      if ((event.getDescription() || "").indexOf(WHS_MARKER) !== -1) {
        event.deleteEvent();
      }
    });

    payload.events.forEach((item) => createCalendarEvent(calendar, item));
    return json({ ok: true, created: payload.events.length });
  } catch (error) {
    return json({ ok: false, error: String(error && error.message ? error.message : error) });
  }
}

function createCalendarEvent(calendar, item) {
  const title = item.title || "WHS Event";
  const description = [item.notes || "", WHS_MARKER, "Source key: " + (item.key || "")].filter(Boolean).join("\n\n");
  const options = { description };

  if (!item.startTime) {
    calendar.createAllDayEvent(title, parseLocalDate(item.date), options);
    return;
  }

  const start = parseLocalDateTime(item.date, item.startTime);
  const endDate = item.endTime && item.endTime <= item.startTime ? addDays(parseLocalDate(item.date), 1) : parseLocalDate(item.date);
  const end = parseLocalDateTime(formatDate(endDate), item.endTime || item.startTime);
  calendar.createEvent(title, start, end, options);
}

function parseLocalDate(value) {
  const parts = value.split("-").map(Number);
  return new Date(parts[0], parts[1] - 1, parts[2]);
}

function parseLocalDateTime(dateValue, timeValue) {
  const dateParts = dateValue.split("-").map(Number);
  const timeParts = timeValue.split(":").map(Number);
  return new Date(dateParts[0], dateParts[1] - 1, dateParts[2], timeParts[0], timeParts[1] || 0);
}

function addDays(date, days) {
  const copy = new Date(date.getTime());
  copy.setDate(copy.getDate() + days);
  return copy;
}

function formatDate(date) {
  return [date.getFullYear(), pad(date.getMonth() + 1), pad(date.getDate())].join("-");
}

function pad(value) {
  return String(value).padStart(2, "0");
}

function json(value) {
  return ContentService.createTextOutput(JSON.stringify(value)).setMimeType(ContentService.MimeType.JSON);
}
