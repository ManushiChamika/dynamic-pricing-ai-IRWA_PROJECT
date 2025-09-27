import React, { useState, useEffect, useRef } from "react";
import { FaRobot, FaCogs } from "react-icons/fa";
import { FiDownload, FiTrash2, FiCopy, FiLoader, FiSun, FiMoon, FiSearch, FiHardDrive } from "react-icons/fi";
import { motion, AnimatePresence } from "framer-motion";
import html2pdf from "html2pdf.js";
import { useTheme } from "../ThemeContext";
import { HiCpuChip, HiComputerDesktop, HiBolt, HiDevicePhoneMobile } from "react-icons/hi2";
import { BsGpuCard, BsMemory } from "react-icons/bs";
import { LuHardDrive } from "react-icons/lu";
import './BuildSuggestorAI.css';
import { useAuth } from "../../../context/authContext";
import { useNavigate } from "react-router-dom";

const components = [
  { name: 'PROCESSOR', icon: <HiCpuChip /> },
  { name: 'GPU', icon: <BsGpuCard /> },
  { name: 'Motherboard', icon: <HiComputerDesktop /> },
  { name: 'RAM', icon: <BsMemory /> },
  { name: 'Storage', icon: <LuHardDrive /> },
  { name: 'Power Supply', icon: <HiBolt /> },
  { name: 'Case', icon: <HiDevicePhoneMobile /> },
];

const BuildSuggestor = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { isDark, toggleTheme } = useTheme();
  const [requirement, setRequirement] = useState("");
  const [buildData, setBuildData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const historyRefs = useRef({});

  // Compute storage key after user is defined
  const STORAGE_KEY = user ? `buildHistory_${user._id}` : null;

  useEffect(() => {
    if (!user) {
      setHistory([]);
      return;
    }
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    setHistory(stored);
  }, [user, STORAGE_KEY]);

  const addToHistory = (req, build) => {
    const entry = {
      id: Date.now(),
      time: new Date().toLocaleString(),
      requirement: req,
      build,
    };
    const newHistory = [entry, ...history];
    setHistory(newHistory);
    if (STORAGE_KEY) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newHistory));
    }
  };

  const handleSubmit = async () => {
    if (!requirement.trim()) return;
    setLoading(true);
    setError("");
    setBuildData(null);

    try {
      const res = await fetch("http://localhost:5000/api/suggest-build", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requirement }),
      });
      const text = await res.text();
      let data;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error("Invalid JSON from server");
      }
      if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
      setBuildData(data);
      addToHistory(requirement, data);
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadHistory = () => {
    if (history.length === 0) {
      alert("No build history to download");
      return;
    }
    
    // Create a temporary div element with proper styling
    const tempDiv = document.createElement("div");
    tempDiv.style.padding = "20px";
    tempDiv.style.fontFamily = "Arial, sans-serif";
    tempDiv.style.color = "#333";
    tempDiv.style.backgroundColor = "#fff";
    
    // Header content
    let content = `
      <div style="text-align: center; margin-bottom: 20px;">
        <h1 style="color: #2c3e50;">AI Build Description History</h1>
        <p>User: ${user?._id || "Anonymous"}</p>
        <p>Generated: ${new Date().toLocaleString()}</p>
      </div>
      <hr style="border: 1px solid #eee; margin: 20px 0;">
    `;
    
    // Add each history item
    history.forEach((item, index) => {
      content += `
        <div style="margin-bottom: 30px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
          <h2 style="color: #3498db;">Build #${index + 1}</h2>
          <p><strong>Date:</strong> ${item.time}</p>
          <p><strong>Requirement:</strong> ${item.requirement}</p>
      `;
      
      // Handle build data if available
      if (item.build && item.build.components) {
        content += `<h3>Components:</h3><ul>`;
        
        // Safely process components
        try {
          Object.entries(item.build.components).forEach(([key, component]) => {
            const name = typeof component === 'object' ? (component.name || 'Unknown') : component;
            const price = typeof component === 'object' ? (component.price || 'N/A') : 'N/A';
            
            content += `<li><strong>${key}:</strong> ${name} ${price !== 'N/A' ? '- $' + price : ''}</li>`;
          });
        } catch (e) {
          content += `<li>Error processing components</li>`;
        }
        
        content += `</ul>
          <p><strong>Total Cost:</strong> $${item.build.totalCost || 'N/A'}</p>
          <p><strong>Performance Notes:</strong> ${item.build.performanceNotes || 'N/A'}</p>
        `;
      } else {
        content += `<p><em>No detailed build information available</em></p>`;
      }
      
      content += `</div>`;
    });
    
    // Set the HTML content
    tempDiv.innerHTML = content;
    
    // Add to document temporarily
    document.body.appendChild(tempDiv);
    
    // Use html2pdf with explicit width setting and wait for rendering
    html2pdf().set({
      margin: 10,
      filename: `AI_Build_History_${user?._id || "user"}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { 
        scale: 2,
        logging: true, 
        dpi: 192,
        letterRendering: true
      },
      jsPDF: { 
        unit: 'mm', 
        format: 'a4', 
        orientation: 'portrait'
      }
    }).from(tempDiv).save().then(() => {
      // Clean up
      document.body.removeChild(tempDiv);
      console.log("PDF generation completed");
    }).catch(err => {
      console.error("PDF generation failed:", err);
      document.body.removeChild(tempDiv);
    });
  };

  const clearHistory = () => {
    if (window.confirm("Are you sure you want to clear all build history?")) {
      setHistory([]);
      if (STORAGE_KEY) {
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  };

  if (!user) {
    return (
      <div style={{ padding: "2rem", color: isDark ? "#e0f2fe" : "#0A1F44", textAlign: "center" }}>
        <h2>Please log in to use the AI Build Suggester.</h2>
      </div>
    );
  }

  const downloadPDF = (id) => {
    const el = historyRefs.current[id];
    if (!el) return;
    html2pdf()
      .from(el)
      .set({ margin: 10, filename: `AI_Build_Description_${id}.pdf`, html2canvas: { scale: 2 }, jsPDF: { unit: "mm", format: "a4", orientation: "portrait" } })
      .save();
  };

  const copyJSON = (build) => {
    navigator.clipboard.writeText(JSON.stringify(build, null, 2));
    alert("Build JSON copied!");
  };

  const filteredHistory = history.filter((h) =>
    h.requirement.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getComponentIcon = (componentName) => {
    const found = components.find((comp) => comp.name.toLowerCase() === componentName.toLowerCase());
    return found ? found.icon : <FaRobot />;
  };

  return (
    <div className="cyberpunk-container">
      {/* 🌟 INLINE STYLES (PLACE CSS HERE IF NEEDED) */}

      {/* Animated background */}
      <div className="circuit-background">
        <div className="circuit-lines"></div>
      </div>

      {/* Main Panel */}
      <div className="main-panel">
        <header className="neo-header">
          <h1 className="title-glow">
            <FaCogs className="rotating-icon" /> PC Build AI
          </h1>
          <div className="theme-toggle-container">
            <button onClick={toggleTheme} className="theme-toggle" aria-label="Toggle theme">
              {isDark ? <FiMoon className="sun-pulse" /> : <FiSun className="moon-glow" />}
            </button>
          </div>
        </header>

        {/* Input Card */}
        <div className="input-card">
          <div className="card-inner">
            <input
              type="text"
              placeholder="Eg:- Suggest me 11th gen pc build for gaming..."
              maxLength={100}
              value={requirement}
              onChange={(e) => setRequirement(e.target.value)}
              className="neo-input"
            />
            <button
              className="cyber-button"
              onClick={handleSubmit}
              disabled={loading}
            >
              <span className="cyber-button-text">
                {loading ? <FiLoader className="spin" /> : "Suggest Build"}
              </span>
              <span className="button-glow"></span>
            </button>

            {error && <p className="error-message">{error}</p>}
          </div>
        </div>

        {/* Build Results */}
        <AnimatePresence>
          {buildData && (
            <motion.div
              key="build"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.5 }}
              className="build-grid"
            >
              {Object.entries(buildData).map(([component, model], index) => (
                <motion.div
                  key={component}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  className="component-card"
                >
                  <div className="hexagon">
                    <div className="hexagon-inner">
                      {getComponentIcon(component)}
                    </div>
                  </div>
                  <h2 className="component-title">{component}</h2>
                  <p className="component-model">{model}</p>
                  <div className="card-highlight"></div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* History Panel */}
      <div className="history-panel">
        <div className="history-header">
          <h3 className="history-title">Build History</h3>
          <div className="history-actions">
            <FiDownload onClick={downloadHistory} className="history-icon download" />
            <FiTrash2 onClick={clearHistory} className="history-icon delete" />
          </div>
        </div>

        <div className="search-container">
          <FiSearch className="search-icon" />
          <input
            type="text"
            placeholder="Search keyword..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>

        {filteredHistory.length === 0 && (
          <div className="empty-history">
            <FiHardDrive className="empty-icon" />
            <p>No builds saved</p>
          </div>
        )}

        <AnimatePresence>
          <div className="history-list">
            {filteredHistory.map((item) => (
              <motion.div
                key={item.id}
                ref={(el) => (historyRefs.current[item.id] = el)}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.3 }}
                className="history-item"
              >
                <div className="item-header">
                  <small className="timestamp">{item.time}</small>
                  <div className="action-buttons">
                    <FiCopy onClick={() => copyJSON(item.build)} className="action-icon" />
                    <FiDownload onClick={() => downloadPDF(item.id)} className="action-icon" />
                  </div>
                </div>
                <p className="requirement">"{item.requirement}"</p>
                <div className="build-specs">
                  {Object.entries(item.build).map(([comp, mod]) => (
                    <p key={comp} className="spec-item">
                      <span className="spec-name">{comp}:</span>
                      <span className="spec-value">{mod}</span>
                    </p>
                  ))}
                </div>
                <div className="item-glow"></div>
              </motion.div>
            ))}
          </div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default BuildSuggestor;
