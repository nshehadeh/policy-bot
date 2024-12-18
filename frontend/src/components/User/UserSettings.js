// UserSettings.js
import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UserSettings = ({ token }) => {
  const [settings, setSettings] = useState({ setting_name: '', setting_value: '' });

  useEffect(() => {
    const fetchSettings = async () => {
      const res = await axios.get('/api/users/settings/', {
        headers: { Authorization: `Token ${token}` }
      });
      setSettings(res.data);
    };
    fetchSettings();
  }, [token]);

  const handleSave = async () => {
    await axios.put('/api/users/settings/', settings, {
      headers: { Authorization: `Token ${token}` }
    });
  };

  return (
    <div>
      <h2>User Settings</h2>
      <input
        type="text"
        placeholder="Setting Name"
        value={settings.setting_name}
        onChange={(e) => setSettings({ ...settings, setting_name: e.target.value })}
      />
      <input
        type="text"
        placeholder="Setting Value"
        value={settings.setting_value}
        onChange={(e) => setSettings({ ...settings, setting_value: e.target.value })}
      />
      <button onClick={handleSave}>Save</button>
    </div>
  );
}

export default UserSettings;
