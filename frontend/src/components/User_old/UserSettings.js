import React, { useState, useEffect } from "react";
import axios from "axios";

const UserSettings = ({ token }) => {
  // State to store user settings with default empty values
  const [settings, setSettings] = useState({
    setting_name: "",
    setting_value: "",
  });

  // Fetch user settings on component mount
  useEffect(() => {
    const fetchSettings = async () => {
      const res = await axios.get("/api/users/settings/", {
        headers: { Authorization: `Token ${token}` },
      });
      setSettings(res.data);
    };
    fetchSettings();
  }, [token]);

  // Save updated settings to the backend
  const handleSave = async () => {
    await axios.put("/api/users/settings/", settings, {
      headers: { Authorization: `Token ${token}` },
    });
  };

  return (
    <div>
      <h2>User Settings</h2>
      {/* Setting name input field */}
      <input
        type="text"
        placeholder="Setting Name"
        value={settings.setting_name}
        onChange={(e) =>
          setSettings({ ...settings, setting_name: e.target.value })
        }
      />
      {/* Setting value input field */}
      <input
        type="text"
        placeholder="Setting Value"
        value={settings.setting_value}
        onChange={(e) =>
          setSettings({ ...settings, setting_value: e.target.value })
        }
      />
      {/* Save button to update settings */}
      <button onClick={handleSave}>Save</button>
    </div>
  );
};

export default UserSettings;
