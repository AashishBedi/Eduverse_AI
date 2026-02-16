import { useState, useRef, useEffect } from "react";
import "./App.css";
import AdminPanel from "./components/AdminPanel";

function App() {
  const [mode, setMode] = useState("general");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode,
          query: input,
        }),
      });

      const data = await res.json();

      const assistantMessage = {
        role: "assistant",
        content: data.answer || "No response.",
        metadata: data.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Backend connection error." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Quick Action Handlers
  const handleAdmissionInfo = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/admissions");
      const data = await response.json();

      if (data.length === 0) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "ℹ️ No admission information available. Please upload admission data via Admin Panel." }
        ]);
      } else {
        // Format admission data
        let content = "🎓 **Admission Information**\n\n";
        data.forEach((admission, index) => {
          content += `**${index + 1}. ${admission.program_name}**\n`;
          content += `   • Eligibility: ${admission.eligibility}\n`;
          content += `   • Duration: ${admission.duration}\n`;
          content += `   • Intake: ${admission.intake}\n`;
          content += `   • Process: ${admission.admission_process}\n`;
          if (admission.contact_email) {
            content += `   • Contact: ${admission.contact_email}\n`;
          }
          content += `\n`;
        });

        setMessages((prev) => [
          ...prev,
          { role: "assistant", content }
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Failed to fetch admission information: ${error.message}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTodaySchedule = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/timetable/today");
      const data = await response.json();

      if (data.length === 0) {
        const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        const today = days[new Date().getDay()];
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: `📅 No classes scheduled for today (${today}). Enjoy your day off! 🎉` }
        ]);
      } else {
        // Format today's schedule
        const days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
        const today = days[new Date().getDay()];
        let content = `📅 **Today's Schedule (${today})**\n\n`;

        data.forEach((entry, index) => {
          content += `**${index + 1}. ${entry.subject}**\n`;
          content += `   • Teacher: ${entry.teacher_name} (${entry.teacher_uid})\n`;
          content += `   • Time: ${entry.start_time} - ${entry.end_time}\n`;
          content += `   • Classroom: ${entry.classroom}\n`;
          content += `   • Department: ${entry.department}\n\n`;
        });

        setMessages((prev) => [
          ...prev,
          { role: "assistant", content }
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Failed to fetch today's schedule: ${error.message}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeeDetails = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/fees");
      const data = await response.json();

      if (data.length === 0) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "ℹ️ No fee information available. Please upload fee data via Admin Panel." }
        ]);
      } else {
        // Format fee data
        let content = "💰 **Fee Structure**\n\n";
        data.forEach((fee, index) => {
          content += `**${index + 1}. ${fee.program_name}**\n`;
          content += `   • Tuition Fee: ₹${fee.tuition_fee.toLocaleString()}\n`;
          if (fee.hostel_fee) content += `   • Hostel Fee: ₹${fee.hostel_fee.toLocaleString()}\n`;
          if (fee.exam_fee) content += `   • Exam Fee: ₹${fee.exam_fee.toLocaleString()}\n`;
          if (fee.other_fee) content += `   • Other Fee: ₹${fee.other_fee.toLocaleString()}\n`;
          content += `   • **Total Fee: ₹${fee.total_fee.toLocaleString()}**\n`;
          content += `   • Academic Year: ${fee.academic_year}\n\n`;
        });

        setMessages((prev) => [
          ...prev,
          { role: "assistant", content }
        ]);
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Failed to fetch fee details: ${error.message}` }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const getModeIcon = (modeValue) => {
    const icons = {
      general: "💡",
      admissions: "🎓",
      regulations: "📋",
      timetable: "📅",
      fees: "💰",
    };
    return icons[modeValue] || "💬";
  };

  const getModeColor = (modeValue) => {
    const colors = {
      general: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      admissions: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
      regulations: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
      timetable: "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
      fees: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    };
    return colors[modeValue] || colors.general;
  };

  return (
    <div className="app">
      {showAdmin ? (
        <AdminPanel />
      ) : (
        <>
          {/* Animated Background */}
          <div className="background-animation">
            <div className="gradient-orb orb-1"></div>
            <div className="gradient-orb orb-2"></div>
            <div className="gradient-orb orb-3"></div>
          </div>

          <div className="container">
            {/* Header */}
            <header className="header">
              <div className="logo-section">
                <div className="logo-icon">🎓</div>
                <div>
                  <h1 className="title">EduVerse AI</h1>
                  <p className="subtitle">Your Intelligent Academic Assistant</p>
                </div>
              </div>

              {/* Mode Selector */}
              <div className="mode-selector">
                <label className="mode-label">Mode</label>
                <div className="mode-select-wrapper">
                  <span className="mode-icon">{getModeIcon(mode)}</span>
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                    className="mode-select"
                    style={{ background: getModeColor(mode) }}
                  >
                    <option value="general">💡 General</option>
                    <option value="admissions">🎓 Admissions</option>
                    <option value="regulations">📋 Regulations</option>
                    <option value="timetable">📅 Timetable</option>
                    <option value="fees">💰 Fees</option>
                  </select>
                </div>
              </div>
            </header>

            {/* Chat Container */}
            <div className="chat-container">
              {messages.length === 0 ? (
                <div className="welcome-screen">
                  <div className="welcome-icon">✨</div>
                  <h2 className="welcome-title">Welcome to EduVerse AI!</h2>
                  <p className="welcome-text">
                    Ask me anything about admissions, timetables, fees, regulations, or general academic queries.
                  </p>
                  <div className="quick-actions">
                    <button className="quick-action" onClick={handleAdmissionInfo}>
                      🎓 Admission Info
                    </button>
                    <button className="quick-action" onClick={handleTodaySchedule}>
                      📅 Today's Schedule
                    </button>
                    <button className="quick-action" onClick={handleFeeDetails}>
                      💰 Fee Details
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`message ${msg.role === "user" ? "user-message" : "assistant-message"}`}
                    >
                      <div className="message-avatar">
                        {msg.role === "user" ? "👤" : "🤖"}
                      </div>
                      <div className="message-content">
                        <div className="message-text">{msg.content}</div>
                        {msg.metadata && (
                          <div className="message-metadata">
                            {msg.metadata.confidence && (
                              <span className={`confidence-badge ${msg.metadata.confidence}`}>
                                {msg.metadata.confidence === "high" ? "✓ High Confidence" :
                                  msg.metadata.confidence === "medium" ? "~ Medium Confidence" :
                                    "! Low Confidence"}
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="message assistant-message loading-message">
                      <div className="message-avatar">🤖</div>
                      <div className="message-content">
                        <div className="typing-indicator">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={chatEndRef} />
                </>
              )}
            </div>

            {/* Input Container */}
            <div className="input-container">
              <div className="input-wrapper">
                <input
                  className="input"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask me anything..."
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()}
                  disabled={isLoading}
                />
                <button
                  className={`send-button ${isLoading ? "loading" : ""}`}
                  onClick={sendMessage}
                  disabled={isLoading || !input.trim()}
                >
                  {isLoading ? (
                    <span className="spinner"></span>
                  ) : (
                    <span className="send-icon">➤</span>
                  )}
                </button>
              </div>
            </div>

            {/* Admin Toggle Button */}
            <button className="admin-toggle" onClick={() => setShowAdmin(true)}>
              📚 Admin Panel
            </button>
          </div>
        </>
      )}

      {/* Back to Chat Button (when in admin) */}
      {showAdmin && (
        <button className="back-to-chat" onClick={() => setShowAdmin(false)}>
          ← Back to Chat
        </button>
      )}
    </div>
  );
}

export default App;
