const GITHUB_BASE_URL =
  'https://github.com/evinracher/spe-ai-labor-law-assistant/blob/main/rag/app/data';

/**
 * Given a citation source (filename such as "LEY 100 DE 1993.pdf"),
 * returns the full GitHub URL to the document.
 *
 * The filename is percent-encoded so that spaces and special characters
 * are handled correctly:
 *   "CAMBIO DE TURNOS ENTRE COMPAÑEREOS.pdf"
 *   → https://…/CAMBIO%20DE%20TURNOS%20ENTRE%20COMPA%C3%91EREOS.pdf
 */
export function sourceToGithubUrl(source: string): string {
  // Strip any leading path components the backend might include.
  // Handles both Unix forward-slashes and Windows back-slashes.
  const filename = source.split(/[\\/]/).pop()!;
  return `${GITHUB_BASE_URL}/${encodeURIComponent(filename)}`;
}

/**
 * Returns just the filename without its extension, for display purposes.
 *   "d:\...\DECRETO 780 DE 2016.pdf" → "DECRETO 780 DE 2016"
 */
export function sourceToDisplayName(source: string): string {
  const filename = source.split(/[\\/]/).pop()!;
  const dotIndex = filename.lastIndexOf('.');
  return dotIndex > 0 ? filename.slice(0, dotIndex) : filename;
}
