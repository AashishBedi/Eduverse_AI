import React from 'react';
import './ModeSelector.css';

const MODES = [
  { value: 'general', label: 'General', description: 'General educational queries' },
  { value: 'admissions', label: 'Admissions', description: 'Admission-related questions' },
  { value: 'timetable', label: 'Timetable', description: 'Teacher schedule queries' },
  { value: 'fees', label: 'Fees', description: 'Fee-related information' },
  { value: 'regulations', label: 'Regulations', description: 'Academic policies' },
];

const ModeSelector = ({ selectedMode, onModeChange }) => {
  return (
    <div className="mode-selector">
      <label htmlFor="mode-select" className="mode-label">
        Query Mode:
      </label>
      <select
        id="mode-select"
        value={selectedMode}
        onChange={(e) => onModeChange(e.target.value)}
        className="mode-select"
      >
        {MODES.map((mode) => (
          <option key={mode.value} value={mode.value}>
            {mode.label}
          </option>
        ))}
      </select>
      <span className="mode-description">
        {MODES.find((m) => m.value === selectedMode)?.description}
      </span>
    </div>
  );
};

export default ModeSelector;
