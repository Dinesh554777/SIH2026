import React, { useState } from 'react';
import { Play, Square, Volume2 } from 'lucide-react';

export default function VoicePlayer({ text, lang }) {
  const [playing, setPlaying] = useState(false);

  const togglePlay = () => {
    // In a real implementation, this would use the browser's speech synthesis API or play an audio file
    if (!playing) {
      setPlaying(true);
      const msg = new SpeechSynthesisUtterance(text);
      msg.lang = lang === 'ta' ? 'ta-IN' : 'en-IN';
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
      <div className="vp-text">Listen to Advisory</div>
      <button className="vp-btn" onClick={togglePlay}>
        {playing ? <Square size={14} /> : <Play size={14} />}
        {playing ? 'Stop' : 'Play'}
      </button>
    </div>
  );
}
