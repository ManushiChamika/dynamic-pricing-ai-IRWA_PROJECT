import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { FiUploadCloud } from "react-icons/fi";
import { FaRobot, FaCheckCircle, FaCopy, FaTrash, FaDownload } from "react-icons/fa";
import html2pdf from "html2pdf.js";
import { useAuth } from "../../../context/authContext";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../../CustomBuilds/ThemeContext"; 
import { jsPDF } from "jspdf";


const ImageUploader = () => {
  const { user } = useAuth();
  const { isDark } = useTheme(); 
  const [image, setImage] = useState(null);
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const pdfRefs = useRef({});
  const navigate = useNavigate();
  const [uploadCounter, setUploadCounter] = useState(1); 

  const storageKey = user ? `aiHistory_${user._id}` : null;

  const extractKeywords = (text) => {
    const stopwords = ["the", "is", "in", "at", "of", "on", "and", "a", "an", "to", "with"];
    const cleanedText = text
      .replace(/Product Name:/gi, '')
      .replace(/Key Technical Specifications:/gi, '')
      .replace(/Typical Use Cases:/gi, '');
    const words = cleanedText
      .toLowerCase()
      .split(/\s+/)
      .map(word => word.replace(/[^a-z0-9]/gi, ''))
      .filter(word => word.length > 2 && !stopwords.includes(word));
    return [...new Set(words)].slice(0, 5);
  };

  const searchInventory = () => {
    const keywords = extractKeywords(description);
    const searchQuery = keywords.join(' ');
    navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
  };

  const searchInventoryForItem = (itemDescription) => {
    const productNameMatch = itemDescription.match(/Product Name:\s*(.*)/i);
    const productName = productNameMatch ? productNameMatch[1].trim() : '';
    if (productName) {
      navigate(`/search?q=${encodeURIComponent(productName)}`);
    } else {
      alert("Product Name not found in description.");
    }
  };

  useEffect(() => {
    if (!user) {
      setHistory([]); 
      return;
    }
    const storageKey = `aiHistory_${user._id}`;
    const stored = JSON.parse(localStorage.getItem(storageKey)) || [];
    setHistory(stored);
  }, [user]);
  

  const updateHistory = (fileName, desc, imageDataUrl, tags = [], metadata = {}) => {
    const newEntry = {
      id: Date.now() + Math.random(),  
      fileName,
      image: imageDataUrl,
      description: desc,
      tags,
      metadata,
    };
    const newHistory = [newEntry, ...history];
    setHistory(newHistory);
  
    if (storageKey) {
      localStorage.setItem(storageKey, JSON.stringify(newHistory));
    }
  };
  
  

  const handleImageChange = (e) => {
    setImage(e.target.files[0]);
    setDescription("");
  };

  const handleUpload = async () => {
    if (!image) return;
    setLoading(true);
    const formData = new FormData();
    formData.append("file", image);

    try {
      const res = await fetch("http://localhost:5000/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      const reader = new FileReader();
      reader.onloadend = () => {
        const imageBase64 = reader.result;
        updateHistory(image.name, data.description, imageBase64, data.tags || [], data.metadata || {});
        setDescription(data.description);
      };
      reader.readAsDataURL(image);
    } catch (error) {
      console.error("Upload failed", error);
      setDescription("Something went wrong. Try again.");
    }
    setLoading(false);
  };

  const beautifyDescription = (desc) => {
    if (!desc) return "";
    return desc
      .replace(/(Product Name:)/g, '**$1**')
      .replace(/(Key Technical Specifications:)/g, '**$1**')
      .replace(/(Typical Use Cases:)/g, '**$1**')
      .replace(/(?<=Key Technical Specifications:\n)(.+)/g, (match) => {
        return match.split('\n').map(line => `• ${line.trim()}`).join('\n');
      })
      .replace(/(?<=Typical Use Cases:\n)(.+)/g, (match) => {
        return match.split('\n').map(line => `• ${line.trim()}`).join('\n');
      });
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert("Description copied to clipboard!");
  };

  const downloadPDF = (id) => {
    const element = pdfRefs.current[id];
    if (!element) return;
    html2pdf()
      .from(element)
      .set({ margin: 10, filename: `AI_Description_${id}.pdf`, html2canvas: { scale: 2 }, jsPDF: { unit: "mm", format: "a4", orientation: "portrait" } })
      .save();
  };

  const downloadHistory = () => {
    if (!user || history.length === 0) {
      alert("No history available to download.");
      return;
    }
  
    const doc = new jsPDF("p", "mm", "a4");
    const pageWidth = doc.internal.pageSize.getWidth();
    const now = new Date();
    const dateStr = now.toLocaleDateString();
    const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  
    const logoUrl = `${window.location.origin}/Logo.jpg`;
  
    new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        doc.addImage(img, "JPEG", 15, 10, 35, 35 * (img.height / img.width));
        resolve();
      };
      img.src = logoUrl;
    }).then(() => {
      // Theme colors
      const primaryColor = "#2c3e50";
      const secondaryColor = "#7f8c8d";
      const accentColor = "#10b981";
  
      doc.setFont("helvetica");
  
      // User Info Top Right
      doc.setFontSize(10);
      doc.setTextColor(secondaryColor);
      doc.text(`${user.name}`, 180, 15, { align: "right" });
      doc.text(`${user.email}`, 180, 20, { align: "right" });
      doc.text(`Date: ${dateStr}`, 180, 25, { align: "right" });
      doc.text(`Time: ${timeStr}`, 180, 30, { align: "right" });
  
      // Title Center
      doc.setFontSize(18);
      doc.setTextColor(primaryColor);
      doc.setFont(undefined, "bold");
      doc.text("AI Analyzer History Report", pageWidth / 2, 50, { align: "center" });
  
      // Divider
      doc.setDrawColor(primaryColor);
      doc.setLineWidth(0.3);
      doc.line(15, 55, 195, 55);
  
      // Start Y
      let y = 60;
      let itemCount = 0;
  
      history.forEach((item, idx) => {
        if (y > 250) {
          doc.addPage();
          y = 20;
        }
      
        itemCount++;
      
        let imgHeight = 0; 
      
        if (item.image) {
          const imgProps = doc.getImageProperties(item.image);
          const imgRatio = imgProps.width / imgProps.height;
          const imgWidth = 50;
          imgHeight = imgWidth / imgRatio;
      
          doc.addImage(item.image, "JPEG", 15, y, imgWidth, imgHeight);
        }
      
        doc.setFontSize(12);
        doc.setTextColor(primaryColor);
        doc.text(`${item.fileName}`, 70, y + 5);
      
        doc.setFontSize(10);
        doc.setTextColor("#374151");
        const splitDesc = doc.splitTextToSize(item.description, 120);
        doc.text(splitDesc, 70, y + 12);
      
        // 🔥 More spacing after each item:
        y += Math.max(80, imgHeight + 40);
      });
    
  
      if (itemCount === 0) {
        doc.setFontSize(12);
        doc.setTextColor("#64748b"); // gray
        doc.text("No uploads available.", pageWidth / 2, 80, { align: "center" });
      }
  
      // Footer
      const pageHeight = doc.internal.pageSize.height;
      const totalPages = doc.internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor("#999999");
        doc.text(
          `Generated by Alpha IT Solutions - Page ${i}`,
          pageWidth / 2,
          pageHeight - 10,
          { align: "center" }
        );
      }
  
      // Border
      doc.setDrawColor("#F9FAFB");
      doc.setLineWidth(0.5);
      doc.rect(5, 5, 200, 287);
  
      // Save
      doc.save(`AI_Analyzer_History_${now.toISOString().slice(0, 10)}.pdf`);
    }).catch((error) => {
      console.error("PDF Generation Error:", error);
      alert("Failed to generate report PDF.");
    });
  };
  

  const clearHistory = () => {
    if (window.confirm("Are you sure you want to clear all history?")) {
      setHistory([]);
      setUploadCounter(1); // 🧹 Reset to 1
      if (storageKey) {
        localStorage.removeItem(storageKey);
      }
    }
  };
  

  if (!user) {
    return <div style={{ padding: "2rem", color: isDark ? "#e0f2fe" : "#0A1F44", textAlign: "center" }}>
      <h2>Please log in to use the AI Engine Analyzer.</h2>
    </div>;
  }

  return (
    <div style={{
      display: "flex",
      flexWrap: "wrap",
      minHeight: "100vh",
      background: isDark ? "#0f172a" : "#f8fafc",
      color: isDark ? "#e0f2fe" : "#0A1F44",
      padding: "2rem",
      fontFamily: "'Poppins', sans-serif",
    }}>
      {/* Upload Panel */}
      <div style={{ flex: 1, minWidth: "350px", maxWidth: "700px", marginRight: "2rem" }}>
        <div style={{
          background: isDark ? "#1e293b" : "#ffffff",
          padding: "2rem",
          borderRadius: "15px",
          boxShadow: "0 4px 30px rgba(0, 0, 0, 0.1)",
          border: `1px solid ${isDark ? "#38bdf8" : "#0A1F44"}`
        }}>
          {/* Content */}
          <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
            <h1 style={{
              fontSize: "2rem", fontWeight: "700",
              color: isDark ? "#38bdf8" : "#0A1F44",
              display: "flex", alignItems: "center", justifyContent: "center", gap: "1rem"
            }}>
              <FaRobot /> AI Engine Analyzer
            </h1>
            <p style={{ color: isDark ? "#94a3b8" : "#475569" }}>
              Upload an image of a computer component and let the AI identify it and search for similar products in inventory
            </p>
          </div>

          {/* Upload */}
          <label htmlFor="upload" style={{
            cursor: "pointer",
            border: `2px dashed ${isDark ? "#38bdf8" : "#0A1F44"}`,
            padding: "2rem",
            borderRadius: "10px",
            background: isDark ? "#334155" : "#f1f5f9",
            textAlign: "center",
            display: "block",
          }}>
            <FiUploadCloud style={{ fontSize: "3rem", color: isDark ? "#38bdf8" : "#0A1F44", marginBottom: "0.5rem" }} />
            <span>{image ? "Change Image" : "Click to Upload an Image"}</span>
            <input type="file" id="upload" onChange={handleImageChange} style={{ display: "none" }} />
          </label>

          {/* After image selected */}
          {image && (
            <div style={{ textAlign: "center", marginTop: "1.5rem" }}>
              <img src={URL.createObjectURL(image)} alt="preview" style={{
                width: "200px", borderRadius: "10px",
                border: `2px solid ${isDark ? "#38bdf8" : "#0A1F44"}`,
                marginBottom: "1rem"
              }} />
              <button onClick={handleUpload} style={{
                background: isDark ? "#38bdf8" : "#0A1F44",
                padding: "0.75rem 2rem", borderRadius: "25px",
                color: "white", fontWeight: "600", border: "none",
                marginTop: "1rem"
              }}>
                {loading ? "Analyzing..." : "Analyze Image"}
              </button>
            </div>
          )}

          {/* After upload */}
          {description && !loading && (
            <div style={{
              marginTop: "2rem",
              background: isDark ? "#334155" : "#f1f5f9",
              padding: "1.5rem",
              borderRadius: "10px",
              border: `1px solid ${isDark ? "#38bdf8" : "#0A1F44"}`
            }}>
              <h2 style={{
                fontSize: "1.5rem", fontWeight: "700",
                color: isDark ? "#38bdf8" : "#0A1F44"
              }}>
                <FaCheckCircle /> AI Description
              </h2>
              <ReactMarkdown
                components={{
                  strong: ({ node, ...props }) => (
                    <strong
                      style={{ color: isDark ? "#38bdf8" : "#0A1F44" }}
                      {...props}
                    />
                  )
                }}
              >
                {beautifyDescription(description)}
              </ReactMarkdown>

              <div style={{ marginTop: "1rem", textAlign: "center" }}>
                <button onClick={searchInventory} style={{
                  background: isDark ? "#38bdf8" : "#0A1F44",
                  padding: "0.75rem 2rem", borderRadius: "25px",
                  color: "white", fontWeight: "600", border: "none"
                }}>
                  🔎 Check Inventory
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* History Section */}
      {/* History Panel */}
<div
  style={{
    flex: 1,
    minWidth: "300px",
    padding: "1rem",
    background: isDark ? "#1e293b" : "rgba(0, 0, 0, 0.05)",
    borderRadius: "15px",
    border: `1px solid ${isDark ? "#38bdf8" : "#0A1F44"}`,
    overflowY: "auto",
    maxHeight: "90vh",
    marginTop: "1rem",
  }}
>
  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
    <h3 style={{ fontSize: "1.25rem", color: isDark ? "#38bdf8" : "#0A1F44" }}>History</h3>
    <div style={{ display: "flex", gap: "0.75rem" }}>
    <button onClick={downloadHistory} title="Download">
  <FaDownload />
</button>

      <button
        onClick={clearHistory}
        title="Clear All"
        style={{
          background: "none",
          color: "#f87171",
          border: "none",
          cursor: "pointer",
        }}
      >
        <FaTrash />
      </button>
    </div>
  </div>

  <hr style={{ borderColor: isDark ? "#38bdf8" : "#0A1F44", margin: "1rem 0" }} />

  {history.length === 0 && (
    <p style={{ color: isDark ? "#94a3b8" : "#475569", fontStyle: "italic" }}>
      No uploads yet...
    </p>
  )}

  {history.map((item) => (
    <div
      key={item.id}
      ref={(el) => (pdfRefs.current[item.id] = el)}
      style={{
        background: isDark ? "#334155" : "#f1f5f9",
        padding: "1rem",
        borderRadius: "10px",
        border: `1px solid ${isDark ? "#38bdf8" : "#0A1F44"}`,
        marginBottom: "1rem",
      }}
    >
      <strong style={{ color: isDark ? "#38bdf8" : "#0A1F44" }}>{item.fileName}</strong>
      <img
        src={item.image}
        alt={item.fileName}
        style={{
          width: "100%",
          maxWidth: "300px",
          marginTop: "0.5rem",
          borderRadius: "6px",
          border: `1px solid ${isDark ? "#38bdf8" : "#0A1F44"}`,
        }}
      />

      <ReactMarkdown
        components={{
          strong: ({ node, ...props }) => (
            <strong style={{ color: isDark ? "#38bdf8" : "#0A1F44" }} {...props} />
          ),
        }}
      >
        {beautifyDescription(item.description)}
      </ReactMarkdown>

      {item.tags && item.tags.length > 0 && (
        <div
          style={{
            marginTop: "0.5rem",
            display: "flex",
            flexWrap: "wrap",
            gap: "0.5rem",
          }}
        >
          {item.tags.map((tag, index) => (
            <span
              key={index}
              style={{
                background: isDark ? "#1e293b" : "#e2e8f0",
                color: isDark ? "#38bdf8" : "#0A1F44",
                padding: "0.3rem 0.7rem",
                borderRadius: "15px",
                fontSize: "0.75rem",
                border: `1px solid ${isDark ? "#38bdf8" : "#0A1F44"}`,
              }}
            >
              #{tag}
            </span>
          ))}
        </div>
      )}

      {/* Buttons Section */}
      <div
        style={{
          marginTop: "0.5rem",
          display: "flex",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <button
          onClick={() => copyToClipboard(item.description)}
          style={{
            padding: "0.4rem 1rem",
            fontSize: "0.8rem",
            background: isDark ? "#38bdf8" : "#0A1F44",
            color: "white",
            border: "none",
            borderRadius: "20px",
            cursor: "pointer",
          }}
        >
          📋 Copy
        </button>

        <button
          onClick={() => downloadPDF(item.id)}
          style={{
            padding: "0.4rem 1rem",
            fontSize: "0.8rem",
            background: isDark ? "#4ade80" : "#16a34a",
            color: "white",
            border: "none",
            borderRadius: "20px",
            cursor: "pointer",
          }}
        >
          ⬇️ PDF
        </button>

        <button
          onClick={() => searchInventoryForItem(item.description)}
          style={{
            padding: "0.4rem 1rem",
            fontSize: "0.8rem",
            background: isDark ? "#3b82f6" : "#1d4ed8",
            color: "white",
            border: "none",
            borderRadius: "20px",
            cursor: "pointer",
          }}
        >
          🔎 Search For Similar Products
        </button>
      </div>
      {/* End Buttons Section */}
    </div>
  ))}
</div>


    </div>
  );
};

export default ImageUploader;
