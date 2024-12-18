import React, { useState } from "react";

const ChatSessionItem = ({
  session,
  isActive,
  onSelect,
  onDelete,
  onRename,
}) => {
  const [showActions, setShowActions] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState(
    session.name || new Date(session.created_at).toLocaleString()
  );

  const handleRename = (e) => {
    e.preventDefault();
    onRename(session.session_id, newName);
    setIsRenaming(false);
  };

  if (isRenaming) {
    return (
      <form onSubmit={handleRename} className="rename-form">
        <input
          type="text"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          className="rename-input"
          autoFocus
        />
        <div className="rename-actions">
          <button type="submit" className="action-button save">
            Save
          </button>
          <button
            type="button"
            onClick={() => setIsRenaming(false)}
            className="action-button cancel"
          >
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <div
      className={`session-item ${isActive ? "active" : ""}`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <button
        onClick={() => onSelect(session.session_id)}
        className="session-button"
      >
        {session.name || new Date(session.created_at).toLocaleString()}
      </button>

      {showActions && (
        <div className="session-actions">
          <button onClick={() => setIsRenaming(true)} className="action-button">
            ✎
          </button>
          <button
            onClick={() => {
              if (
                window.confirm("Are you sure you want to delete this chat?")
              ) {
                onDelete(session.session_id);
              }
            }}
            className="action-button delete"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
};

export default ChatSessionItem;
