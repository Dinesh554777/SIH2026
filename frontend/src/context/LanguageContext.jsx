import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getTranslation } from '../i18n';

const LanguageContext = createContext();

export function LanguageProvider({ children }) {
  // Initialize from localStorage or default to 'en'
  const [lang, setLangState] = useState('en');
    return 'en';
  });

  const setLang = useCallback((newLang) => {
    setLangState(newLang);
    document.documentElement.lang = newLang;
  }, []);

  // Sync to document element on mount
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  // Provide the translation helper bound to the current language
  const t = useCallback((key, params = {}) => {
    let text = getTranslation(key, lang);
    
    // Simple interpolation for params, e.g. {village} -> "Demo Village"
    Object.keys(params).forEach(param => {
      text = text.replace(`{${param}}`, params[param] || '');
    });
    
    return text;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
