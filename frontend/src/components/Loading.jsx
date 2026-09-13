import { useLanguage } from '../context/LanguageContext.jsx';

export default function Loading({ label }) {
  const { t } = useLanguage();
  return (
    <div className="loading" role="status">
      <div className="spinner" aria-hidden="true" />
      <span>{label || t('common.loading')}</span>
    </div>
  );
}
