import { useLanguage } from '../context/LanguageContext.jsx';

export default function DemoBanner({ visible = true }) {
  const { t } = useLanguage();
  if (!visible) return null;
  return (
    <div className="demo-banner">
      {t('dashboard.demoBanner')}
    </div>
  );
}
