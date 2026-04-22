const WEATHERFLOW_URL =
  "https://swd.weatherflow.com/swd/rest/observations/station/63486?token=8d86c8c3-5df3-42c2-9e26-e0c4dfb755c1";

const elements = {
  stationName: document.getElementById("stationName"),
  temperature: document.getElementById("temperature"),
  condition: document.getElementById("condition"),
  refreshButton: document.getElementById("refreshButton"),
  updatedAt: document.getElementById("updatedAt"),
  feelsLike: document.getElementById("feelsLike"),
  humidity: document.getElementById("humidity"),
  pressure: document.getElementById("pressure"),
  todayRain: document.getElementById("todayRain"),
  lightMood: document.getElementById("lightMood"),
  lightDetail: document.getElementById("lightDetail"),
  sunFill: document.getElementById("sunFill"),
  rainMood: document.getElementById("rainMood"),
  rainDetail: document.getElementById("rainDetail"),
  readings: document.getElementById("readings"),
};

elements.refreshButton.addEventListener("click", loadWeather);
loadWeather();

async function loadWeather() {
  elements.refreshButton.disabled = true;
  elements.refreshButton.textContent = "Refreshing";

  try {
    const response = await fetch(WEATHERFLOW_URL, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`WeatherFlow returned ${response.status}`);
    }

    const payload = await response.json();
    renderWeather(payload);
  } catch (error) {
    elements.condition.innerHTML = '<span class="error">The station did not answer. Try again in a moment.</span>';
    elements.updatedAt.textContent = "Live data unavailable";
    console.error(error);
  } finally {
    elements.refreshButton.disabled = false;
    elements.refreshButton.textContent = "Refresh";
  }
}

function renderWeather(payload) {
  const obs = payload.obs?.[0] || {};
  const stationTime = new Date((obs.timestamp || Date.now() / 1000) * 1000);
  const tempF = cToF(obs.air_temperature);
  const feelsF = cToF(obs.heat_index);
  const dewF = cToF(obs.dew_point);
  const wetBulbF = cToF(obs.wet_bulb_temperature);
  const normalizedBarometerInHg = mbToInHg(obs.sea_level_pressure);
  const correctedBarometerInHg = mbToInHg(obs.barometric_pressure ?? obs.station_pressure);
  const stationPressureInHg = mbToInHg(obs.station_pressure);
  const elevationFeet = metersToFeet(payload.elevation);
  const rainNowIn = mmToIn(obs.precip);
  const rainHourIn = mmToIn(obs.precip_accum_last_1hr);
  const rainTodayIn = mmToIn(obs.precip_accum_local_day);
  const rainYesterdayIn = mmToIn(obs.precip_accum_local_yesterday);
  const brightnessPercent = clamp((obs.brightness || 0) / 1000, 0, 100);

  elements.stationName.textContent = payload.public_name || payload.station_name || "Home Weather";
  elements.temperature.textContent = `${round(tempF)}°F`;
  elements.condition.textContent = conditionSentence(obs, tempF, dewF);
  elements.updatedAt.textContent = `Updated ${formatDateTime(stationTime, payload.timezone)}`;
  elements.feelsLike.textContent = `${round(feelsF)}°F`;
  elements.humidity.textContent = `${round(obs.relative_humidity)}%`;
  elements.pressure.textContent = `${fixed(normalizedBarometerInHg, 2)} inHg`;
  elements.todayRain.textContent = `${fixed(rainTodayIn, 2)} in`;

  elements.lightMood.textContent = lightMood(obs.solar_radiation, obs.uv);
  elements.lightDetail.textContent = `${round(obs.solar_radiation)} W/m² solar radiation, ${fixed(obs.uv, 1)} UV, and ${round(obs.brightness)} lux at the station.`;
  elements.sunFill.style.height = `${Math.max(8, brightnessPercent)}%`;

  elements.rainMood.textContent = rainMood(obs);
  elements.rainDetail.textContent = `${fixed(rainHourIn, 2)} in during the last hour, ${fixed(
    rainTodayIn,
    2,
  )} in today, and ${round(obs.precip_minutes_local_day)} wet minutes since midnight.`;

  const readings = [
    ["Dew Point", `${round(dewF)}°F`, "Moisture in the air"],
    ["Wet Bulb", `${round(wetBulbF)}°F`, "Evaporative cooling point"],
    ["Pressure Trend", titleCase(obs.pressure_trend), "Trend of the normalized corrected barometer"],
    ["Normalized Barometer", `${fixed(normalizedBarometerInHg, 2)} inHg`, "Sea-level corrected pressure"],
    ["Corrected Station Barometer", `${fixed(correctedBarometerInHg, 2)} inHg`, "Corrected local barometer reading"],
    ["Station Pressure", `${fixed(stationPressureInHg, 2)} inHg`, "Raw pressure at elevation"],
    ["Rain Rate", `${fixed(rainNowIn, 2)} in`, "Current precipitation"],
    ["Yesterday", `${fixed(rainYesterdayIn, 2)} in`, "Local day total"],
    ["Lightning 1 hr", `${round(obs.lightning_strike_count_last_1hr)}`, "Strikes detected nearby"],
    ["Last Lightning", lightningText(obs), "Distance and time"],
    ["Air Density", `${fixed(obs.air_density, 3)} kg/m³`, "Current density"],
    ["Delta T", `${fixed(cToFDelta(obs.delta_t), 1)}°F`, "Dry bulb minus wet bulb"],
    ["Elevation", `${round(elevationFeet)} ft`, "Station elevation"],
    ["Location", `${fixed(payload.latitude, 4)}, ${fixed(payload.longitude, 4)}`, payload.timezone || "Local station"],
  ];

  elements.readings.innerHTML = readings
    .map(
      ([label, value, note]) => `
        <article class="reading-card">
          <span>${label}</span>
          <strong>${value}</strong>
          <small>${note}</small>
        </article>
      `,
    )
    .join("");
}

function conditionSentence(obs, tempF, dewF) {
  const humidity = round(obs.relative_humidity);
  const trend = obs.pressure_trend ? `Pressure is ${obs.pressure_trend}` : "Pressure is steady";
  const rainTodayIn = mmToIn(obs.precip_accum_local_day);
  const rain = rainTodayIn > 0 ? `${fixed(rainTodayIn, 2)} inches of rain today` : "no rain today";
  return `${round(tempF)} degrees with ${humidity}% humidity and a ${round(dewF)} degree dew point. ${trend}, with ${rain}.`;
}

function lightMood(solar, uv) {
  if (uv >= 6) return "Bright High-UV Sun";
  if (solar >= 500) return "Strong Mountain Light";
  if (solar >= 120) return "Soft Daylight";
  if (solar > 0) return "Low Angled Light";
  return "Night Reading";
}

function rainMood(obs) {
  if (obs.precip > 0) return "Rain Is Falling";
  if (obs.precip_accum_local_day > 0) return "Fresh Rain Today";
  if (obs.precip_accum_local_yesterday > 0) return "Recently Wet";
  return "Dry Ground";
}

function lightningText(obs) {
  if (!obs.lightning_strike_last_epoch) return "No recent strike";
  const when = new Date(obs.lightning_strike_last_epoch * 1000);
  return `${round(kmToMi(obs.lightning_strike_last_distance))} mi, ${formatDateTime(when)}`;
}

function cToF(value) {
  return Number.isFinite(value) ? (value * 9) / 5 + 32 : undefined;
}

function cToFDelta(value) {
  return Number.isFinite(value) ? (value * 9) / 5 : undefined;
}

function mbToInHg(value) {
  return Number.isFinite(value) ? value * 0.0295299831 : undefined;
}

function metersToFeet(value) {
  return Number.isFinite(value) ? value * 3.28084 : undefined;
}

function mmToIn(value) {
  return Number.isFinite(value) ? value / 25.4 : undefined;
}

function kmToMi(value) {
  return Number.isFinite(value) ? value * 0.621371 : undefined;
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function round(value) {
  return Number.isFinite(value) ? Math.round(value) : "--";
}

function fixed(value, digits) {
  return Number.isFinite(value) ? Number(value).toFixed(digits) : "--";
}

function formatDateTime(date, timezone) {
  return new Intl.DateTimeFormat([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
    timeZone: timezone || undefined,
  }).format(date);
}

function titleCase(value) {
  if (!value) return "--";
  return String(value)
    .split(/[\s_-]+/)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}
