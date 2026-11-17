const localTimeFormatter = new Intl.DateTimeFormat("en-CA", {
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

export function formatName(name: string): string {
  // The generic title-caser would turn the "IP" acronym into "Geoip".
  if (name === "geoip") {
    return "GeoIP";
  }

  // Title-case every ASCII word, leaving non-ASCII text untouched:
  // "sing-box" -> "Sing-Box".
  return name.replace(/[A-Za-z]+/g, (word) => {
    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
  });
}

export function formatFileSize(size: number): string {
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatLocalTime(timestamp: number): string {
  if (timestamp <= 0) {
    return "—";
  }

  const parts = localTimeFormatter.formatToParts(new Date(timestamp * 1000));
  const values = new Map(parts.map((part) => [part.type, part.value]));

  const year = values.get("year");
  const month = values.get("month");
  const day = values.get("day");
  const hour = values.get("hour");
  const minute = values.get("minute");
  const second = values.get("second");

  return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
}

export function utcTimeTitle(timestamp: number): string {
  const utc = new Date(timestamp * 1000).toISOString();
  return `UTC时间: ${utc}\n本地时区: ${timeZone}`;
}
