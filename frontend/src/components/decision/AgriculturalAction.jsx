import React from 'react';

const ACTION_VERB = {
  SOW: "Sow",
  WAIT: "Wait — hold sowing",
  MONITOR: "Monitor",
  PREPARE: "Prepare land & inputs",
  IRRIGATION_PREPARE: "Irrigation prepare",
};

export default function AgriculturalAction({ decision }) {
  if (!decision) return null;

  return (
    <div className="action-panel">
      <div className="ap-header">WHAT SHOULD I DO NOW?</div>
      
      <div className="ap-card">
        <div className="ap-main-action">
          {ACTION_VERB[decision.decision] ?? decision.decision}
        </div>
        
        <p className="ap-explainer">
          {decision.decision_label}
        </p>

        <div className="ap-next-step">
          <strong>NEXT STEP</strong><br />
          Monitor rainfall persistence for the next 3-5 days.
        </div>
      </div>
    </div>
  );
}
