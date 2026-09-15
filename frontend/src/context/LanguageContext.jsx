import React, { createContext, useContext, useState, useCallback } from 'react';
import { getTranslation } from '../i18n';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState('en');

  const setLang = useCallback((newLang) => {
    setLangState(newLang);
    document.documentElement.lang = newLang;
  }, []);

  const t = useCallback(
    (key, params = {}) => {
      let text = getTranslation(key, lang);
      if (typeof text !== 'string') {
        return key;
      }
      Object.entries(params).forEach(([k, v]) => {
        text = text.replace(new RegExp(`{${k}}`, 'g'), v);
      });
      return text;
    },
    [lang]
  );

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}
