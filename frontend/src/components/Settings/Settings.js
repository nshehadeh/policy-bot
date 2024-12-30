import React, { useState } from 'react';
import './Settings.css';

function Settings({ onClose, theme }) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [isEditingSettings, setIsEditingSettings] = useState(false);

  const handleSaveSettings = () => {
    // TODO: Implement settings save
    setIsEditingSettings(false);
    onClose();
  };

  return (
    <div className={`settings-overlay ${theme}`}>
      <div className="settings-modal">
        <div className="settings-header">
          <h2>Settings</h2>
          <button onClick={onClose} className="close-button">×</button>
        </div>
        <div className="settings-content">
          <div className="settings-form">
            <div className="form-group">
              <label>First Name:</label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                disabled={!isEditingSettings}
              />
            </div>
            <div className="form-group">
              <label>Last Name:</label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                disabled={!isEditingSettings}
              />
            </div>
          </div>
          <div className="settings-actions">
            {!isEditingSettings ? (
              <button onClick={() => setIsEditingSettings(true)}>Edit</button>
            ) : (
              <>
                <button onClick={handleSaveSettings}>Save</button>
                <button onClick={() => setIsEditingSettings(false)}>Cancel</button>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Settings;
