
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import {
  Bot,
  Send,
  Paperclip,
  FileText,
  User,
  LoaderCircle,
  Sparkles,
  CheckCircle2,
  Code2,
  BrainCircuit,
  ClipboardList,
  ArrowRight,
  Users,
  GitBranch,
  MessageSquare,
  Settings,
  Mic,
  X,
  UploadCloud,
  ShieldCheck,
  PanelLeft,
} from "lucide-react";

import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function getSessionId() {
  let id = sessionStorage.getItem("hr_session_id");

  if (!id) {
    id = crypto.randomUUID();
    sessionStorage.setItem("hr_session_id", id);
  }

  return id;
}

function cleanMarkdown(content) {
  return content
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/\r\n/g, "\n")
    .trim();
}

const suggestions = [
  {
    icon: Code2,
    title: "Analyze Candidate Skills",
    description: "Explore technical skills and development experience.",
    prompt: "Analyze the candidate's technical skills and development experience.",
    color: "purple",
  },
  {
    icon: BrainCircuit,
    title: "Extract Core ML Skills",
    description: "Identify documented AI and machine learning experience.",
    prompt: "What AI, machine learning and NLP skills are documented in the candidate's profile?",
    color: "green",
  },
  {
    icon: ClipboardList,
    title: "Draft Screening Questions",
    description: "Generate interview questions based on the candidate's profile.",
    prompt: "Generate relevant technical screening questions based on the candidate's documented skills and projects.",
    color: "orange",
  },
];

function App() {
  const [sessionId] = useState(getSessionId);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! I'm your HR Portfolio AI Assistant. Ask me about the candidate's skills, education, experience, and projects. You can also upload a Job Description to evaluate candidate suitability.",
    },
  ]);

  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);

  const [uploading, setUploading] = useState(false);
  const [sending, setSending] = useState(false);

  const [jdUploaded, setJdUploaded] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");

  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);
  const composerRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, sending]);

  const selectFile = (selectedFile) => {
    if (!selectedFile) return;

    const allowedTypes = [".pdf", ".docx", ".txt"];
    const extension = selectedFile.name
      .toLowerCase()
      .slice(selectedFile.name.lastIndexOf("."));

    if (!allowedTypes.includes(extension)) {
      setUploadMessage("Please select a PDF, DOCX or TXT file.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setUploadMessage("File size must not exceed 10 MB.");
      return;
    }

    setFile(selectedFile);
    setUploadMessage("");
  };

  const uploadJD = async () => {
    if (!file || uploading) return;

    setUploading(true);
    setUploadMessage("");

    const formData = new FormData();

    formData.append("session_id", sessionId);
    formData.append("file", file);

    try {
      const response = await fetch(`${API_URL}/upload-jd`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to upload job description."
        );
      }

      setJdUploaded(true);
      setUploadMessage("Job description successfully processed.");

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `### Job Description Processed

**${data.filename}**

- Characters extracted: ${data.characters_extracted}
- Chunks indexed: ${data.chunks_indexed}

You can now ask me to evaluate the candidate against this job description.`,
        },
      ]);

      setFile(null);

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (error) {
      setUploadMessage(error.message);
    } finally {
      setUploading(false);
    }
  };

  const sendMessage = async (text = input) => {
    const message = text.trim();

    if (!message || sending) return;

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: message,
      },
    ]);

    setInput("");
    setSending(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          message,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong.");
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `**Request failed:** ${error.message}. Please check whether the backend is running.`,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const focusComposer = () => {
    composerRef.current?.focus();
  };

  const handleDrop = (event) => {
    event.preventDefault();

    const droppedFile = event.dataTransfer.files?.[0];

    if (droppedFile) {
      selectFile(droppedFile);
    }
  };

  return (
    <div className="app-container">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">
            <Sparkles size={23} />
          </div>

          <div className="brand-text">
            <h2>Portfolio AI</h2>
            <span>HR Intelligence</span>
          </div>
        </div>

        <div className="sidebar-section">
          <p className="sidebar-label">RECRUITING NAVIGATION</p>

          <button className="sidebar-item active">
            <Bot size={18} />
            <span>Copilot Hub</span>
          </button>
{/* 
          <button className="sidebar-item" disabled>
            <Users size={18} />
            <span>Talent Pipeline</span>
            <small>SOON</small>
          </button>

          <button className="sidebar-item" disabled>
            <Sparkles size={18} /> 
            <span>AI Candidate Matches</span>
            <small>SOON</small>
          </button>

          <button className="sidebar-item" disabled>
            <MessageSquare size={18} />
            <span>Outreach Autopilot</span>
            <small>SOON</small>
          </button>

          <button className="sidebar-item" disabled>
            <ShieldCheck size={18} />
            <span>Scorecards & Bias Review</span>
            <small>SOON</small>
          </button> */}

          <button className="sidebar-item" disabled>
            <GitBranch size={18} />
            <span>ATS Integration</span>
            <span className="sync-badge">SYNCED</span>
          </button>
        </div>

        <div className="sidebar-bottom">

          <div className="usage-card">
            <div className="usage-heading">
              <span>AI ASSISTANT</span>
              <span className="usage-status">ONLINE</span>
            </div>

            {/* <div className="usage-track">
              <div className="usage-progress" />
            </div> */}

            <p>Candidate intelligence workspace</p>
          </div>

          <button className="sidebar-settings" disabled>
            <Settings size={17} />
            Settings & Workspaces
          </button>

          <div className="sidebar-profile">
            <div className="profile-avatar">HR</div>

            <div>
              <strong>HR Workspace</strong>
              <span>Candidate Evaluation</span>
            </div>
          </div>

        </div>
      </aside>

      {/* MAIN AREA */}
      <main className="main-content">

        {/* HEADER */}
        <header className="topbar">
          <div className="topbar-title">
            <div className="mobile-brand-icon">
              <PanelLeft size={19} />
            </div>

            <div>
              <h3>Candidate Assistant</h3>
              <p>
                Ask questions about the candidate or upload a Job
                Description for instant AI evaluation
              </p>
            </div>
          </div>

          <div className="status-pill">
            <span className="status-dot" />
            AI Assistant Active
          </div>
        </header>

        {/* SCROLLABLE CONTENT */}
        <section className="chat-area">

          {/* WELCOME */}
          <div className="welcome-heading">
            <div className="welcome-icon">
              <Sparkles size={29} />
            </div>

            <h1>How can I help you today?</h1>

            <p>
              Explore candidate information or upload a Job Description
              for an AI-powered evaluation.
            </p>
          </div>

          {/* JOB DESCRIPTION UPLOAD */}
          <div className="upload-card">

            <div className="upload-card-heading">

              <div className="upload-icon">
                <FileText size={21} />
              </div>

              <div className="upload-heading-text">
                <h3>Job Description Evaluation</h3>
                <p>
                  Upload a JD to evaluate candidate-job fit instantly
                </p>
              </div>

              <span className="version-badge">
                AUTO-MATCH V1.0
              </span>

            </div>

            <div
              className="drop-zone"
              onDragOver={(event) => event.preventDefault()}
              onDrop={handleDrop}
            >

              <div className="drop-icon">
                <UploadCloud size={21} />
              </div>

              <div className="drop-text">
                <strong>
                  {file ? file.name : "Choose File or drag & drop here"}
                </strong>

                <span>
                  PDF, DOCX or TXT (max 10 MB)
                </span>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt"
                hidden
                onChange={(event) => {
                  selectFile(event.target.files?.[0]);
                }}
              />

              <div className="upload-actions">

                {file && (
                  <button
                    className="remove-file"
                    onClick={() => {
                      setFile(null);
                      if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                      }
                    }}
                    aria-label="Remove file"
                  >
                    <X size={17} />
                  </button>
                )}

                <button
                  className="choose-file-button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploading}
                >
                  Choose File
                </button>

                <button
                  className="upload-button"
                  onClick={uploadJD}
                  disabled={!file || uploading}
                >
                  {uploading ? (
                    <>
                      <LoaderCircle className="spin" size={16} />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles size={15} />
                      Upload JD & Scan
                    </>
                  )}
                </button>

              </div>
            </div>

            {uploadMessage && (
              <p
                className={
                  jdUploaded ? "upload-success" : "upload-error"
                }
              >
                {jdUploaded && <CheckCircle2 size={15} />}
                {uploadMessage}
              </p>
            )}

            {jdUploaded && (
              <div className="jd-status">
                <CheckCircle2 size={15} />
                Job description indexed for this session
              </div>
            )}

          </div>

          {/* SUGGESTED ACTIONS */}
          <div className="suggestion-grid">
            {suggestions.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.title}
                  className="suggestion-card"
                  onClick={() => {
                    setInput(item.prompt);
                    focusComposer();
                  }}
                >
                  <div className={`suggestion-icon ${item.color}`}>
                    <Icon size={19} />
                  </div>

                  <ArrowRight
                    className="suggestion-arrow"
                    size={17}
                  />

                  <h4>{item.title}</h4>
                  <p>{item.description}</p>
                </button>
              );
            })}
          </div>

          {/* CHAT MESSAGES */}
          <div className="messages-container">

            {messages.map((message, index) => (
              <div
                key={index}
                className={`message-row ${message.role}`}
              >

                <div className="message-avatar">
                  {message.role === "assistant" ? (
                    <Bot size={19} />
                  ) : (
                    <User size={19} />
                  )}
                </div>

                <div className="message-bubble">

                  <div className="message-header">
                    <span className="message-author">
                      {message.role === "assistant"
                        ? "Portfolio AI Assistant"
                        : "You"}
                    </span>

                    {message.role === "assistant" && (
                      <span className="message-time">AI RESPONSE</span>
                    )}
                  </div>

                  {message.role === "assistant" ? (
                    <div className="markdown-content">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {cleanMarkdown(message.content)}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    <p className="user-message-content">
                      {message.content}
                    </p>
                  )}

                  {message.role === "assistant" &&
                    index === 0 && (
                      <div className="message-tags">
                        <span className="confidence-tag">
                          <CheckCircle2 size={12} />
                          Profile-grounded
                        </span>

                        <span className="neutral-tag">
                          <ShieldCheck size={12} />
                          Evidence-based
                        </span>
                      </div>
                    )}

                </div>
              </div>
            ))}

            {/* THINKING */}
            {sending && (
              <div className="message-row assistant">

                <div className="message-avatar">
                  <Bot size={19} />
                </div>

                <div className="message-bubble typing">
                  <LoaderCircle className="spin" size={18} />
                  Thinking...
                </div>

              </div>
            )}

            <div ref={messagesEndRef} />

          </div>

        </section>

        {/* BOTTOM COMPOSER */}
        <footer className="chat-footer">

          <div className="chat-input-wrapper">

            <button
              className="attachment-button"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Attach job description"
              title="Attach a job description"
            >
              <Paperclip size={18} />
            </button>

            <textarea
              ref={composerRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about skills, projects, experience or job fit..."
              rows={1}
              disabled={sending}
            />

            <button
              className="send-button"
              onClick={() => sendMessage()}
              disabled={!input.trim() || sending}
              aria-label="Send message"
            >
              <Send size={19} />
            </button>

          </div>

          <p className="footer-note">
            <ShieldCheck size={12} />
            AI-generated responses should be verified against candidate evidence.
          </p>

        </footer>

      </main>
    </div>
  );
}

export default App;
