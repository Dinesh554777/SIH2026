import { en } from './en';
import { ta } from './ta';

const dictionaries = { en, ta };

/**
 * Safely resolves a dot-notation key (e.g. "dashboard.title") from a dictionary.
 * Falls back to English if the key is missing in the target language.
 * Logs a warning in development mode if missing.
 */
export function getTranslation(key, lang = 'en') {
  const keys = key.split('.');
  
  // Try to resolve in the target language
  let val = dictionaries[lang];
  for (const k of keys) {
    if (val === undefined) break;
    val = val[k];
  }

  // If found and it's a string, return it
  if (typeof val === 'string') {
    return val;
  }

  // Fallback to English
  if (lang !== 'en') {
    let fallbackVal = dictionaries['en'];
    for (const k of keys) {
      if (fallbackVal === undefined) break;
      fallbackVal = fallbackVal[k];
    }
    if (typeof fallbackVal === 'string') {
      if (import.meta.env?.DEV) {
        console.warn(`[i18n] Missing translation for key: "${key}" in language: "${lang}". Falling back to English.`);
      }
      return fallbackVal;
    }
  }

  // Absolute fallback if not even in English
  if (import.meta.env?.DEV) {
    console.error(`[i18n] Missing translation key completely: "${key}"`);
  }
  return key; // Return the key itself as a last resort so UI doesn't say "undefined"
}
