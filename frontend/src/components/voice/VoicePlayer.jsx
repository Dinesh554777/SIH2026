import React, { useState } from 'react';
import { Play, Square, Volume2 } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext.jsx';

export default function VoicePlayer({ text }) {
  const { lang, t } = useLanguage();
  const [playing, setPlaying] = useState(false);

  const togglePlay = () => {
    if (!playing) {
      window.speechSynthesis.cancel(); // Cancel any existing speech
      setPlaying(true);
      const msg = new SpeechSynthesisUtterance(text);
      msg.lang = lang === 'ta' ? 'ta-IN' : 'en-IN';
      msg.rate = 0.9;
      msg.pitch = 1;
      msg.onend = () => setPlaying(false);
      window.speechSynthesis.speak(msg);
    } else {
      window.speechSynthesis.cancel();
      setPlaying(false);
    }
  };

  return (
    <div className="voice-player">
      <div className="vp-icon">
        <Volume2 size={16} />
      </div>
      <div className="vp-text">{t('common.listen')}</div>
      <button className="vp-btn" onClick={togglePlay}>
        {playing ? <Square size={14} /> : <Play size={14} />}
        {playing ? t('common.stop') : t('common.listen')}
      </button>
    </div>
  );
}
