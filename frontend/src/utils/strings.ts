export function truncateString(str: string, num: number) {
  if (str.length <= num) {
    return str;
  }
  return str.slice(0, num) + '...';
}

/** The URL if it is an http(s) one: `javascript:` links run in our page. */
export function httpUrl(url: string | undefined | null) {
  return url && /^https?:\/\//i.test(url) ? url : undefined;
}
