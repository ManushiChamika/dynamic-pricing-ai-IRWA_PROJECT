import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import jsPDF from "jspdf";
import logo from "../../assets/AlphaITSolutionsLogo.jpg";
import sign from "../../assets/sign.png";

const AppointmentDashboard = () => {
  const [appointments, setAppointments] = useState([]);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const navigate = useNavigate();
  const [isEditMode, setIsEditMode] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [dateError, setDateError] = useState("");
  const [timeError, setTimeError] = useState("");

  const progressStages = [
    "Device Handover",
    "Diagnosis",
    "Repair",
    "Testing",
    "Device Ready to Pick",
  ];

  // Define available time slots
  const availableTimeSlots = [
    "09:00 AM ",
    "10:00 AM",
    "11:00 AM ",
    "02:00 PM ",
    "03:00 PM ",
    "04:00 PM "
  ];

  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch("http://localhost:5000/api/appointments", {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        if (!response.ok) throw new Error("Failed to fetch data");
        const data = await response.json();
        setAppointments(data);
      } catch (error) {
        console.error("Error fetching appointments:", error);
      }
    };

    fetchAppointments();
  }, []);

  const handleRowClick = (appointment) => {
    setSelectedAppointment(appointment);
    setIsModalOpen(true);
    setIsEditMode(appointment.status === "pending");
    setCurrentStage(appointment.progress || -1);
    setDateError("");
    setTimeError("");
  };

  const handleInputChange = (e) => {
    if (isEditMode) {
      setSelectedAppointment({ 
        ...selectedAppointment, 
        [e.target.name]: e.target.value 
      });
      
      // Clear errors when changing values
      if (e.target.name === 'date') {
        setDateError("");
      }
      if (e.target.name === 'timeSlot') {
        setTimeError("");
      }
    }
  };

  const validateAppointmentTime = () => {
    if (!selectedAppointment) return false;
    
    const { date, timeSlot, _id } = selectedAppointment;
    let isValid = true;
    
    // Check if date is in the past
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const selectedDate = new Date(date);
    
    if (selectedDate < today) {
      setDateError("Cannot select a date in the past");
      isValid = false;
    }
    
    // Check if date is more than 1 year in the future
    const oneYearLater = new Date();
    oneYearLater.setFullYear(oneYearLater.getFullYear() + 1);
    
    if (selectedDate > oneYearLater) {
      setDateError("Cannot select a date more than one year in advance");
      isValid = false;
    }
    
    // Check for conflicting appointments (same date and time)
    const hasConflict = appointments.some(appt => 
      appt._id !== _id && 
      appt.date === date && 
      appt.timeSlot === timeSlot
    );
    
    if (hasConflict) {
      setTimeError("This time slot is already booked. Please choose another.");
      isValid = false;
    }
    
    return isValid;
  };

  const handleUpdate = async () => {
    if (!validateAppointmentTime()) {
      return;
    }
  
    // Check for time conflicts before sending update
    const isConflict = appointments.some(appointment => 
      appointment._id !== selectedAppointment._id && 
      appointment.date === selectedAppointment.date && 
      appointment.time === selectedAppointment.time
    );
  
    if (isConflict) {
      alert("Another appointment already exists at the selected time. Please choose a different time.");
      return;
    }
  
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/appointments/${selectedAppointment._id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(selectedAppointment),
      });
  
      if (!response.ok) throw new Error("Failed to update appointment");
  
      const updatedAppointments = appointments.map((appointment) =>
        appointment._id === selectedAppointment._id ? selectedAppointment : appointment
      );
      setAppointments(updatedAppointments);
      setIsModalOpen(false);
    } catch (error) {
      console.error("Error updating appointment:", error);
    }
  };
  

  const handleDelete = async () => {
    const isConfirmed = window.confirm("Are you sure you want to delete this appointment?");
    if (!isConfirmed) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:5000/api/appointments/${selectedAppointment._id}`, {
        method: "DELETE",
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error("Failed to delete appointment");

      setAppointments(appointments.filter((appointment) => appointment._id !== selectedAppointment._id));
      setIsModalOpen(false);
    } catch (error) {
      console.error("Error deleting appointment:", error);
    }
  };

  const generateReport = () => {
    try {
        if (!selectedAppointment) {
            alert("No appointment selected!");
            return;
        }

        const doc = new jsPDF();
        
        // Colors
        const primaryColor = "#2c3e50";
        const secondaryColor = "#7f8c8d";
        const accentColor = "#e74c3c";
        const darkColor = "#1F2937";
        const lightColor = "#F9FAFB";
        
        // Set compact layout
        const compact = true;
        const lineHeight = compact ? 5 : 7;
        const sectionSpacing = compact ? 8 : 15;
        
        // Set default font
        doc.setFont("helvetica");
        
        // Add logo
        const logoWidth = 30; // Smaller logo
        const logoHeight = 30;
        doc.addImage(logo, "JPEG", 15, 10, logoWidth, logoHeight);
            
        // Company info
        doc.setFontSize(9); // Smaller font
        doc.setTextColor(secondaryColor);
        doc.text("Alpha IT Solutions", 180, 15, { align: "right" });
        doc.text("123 Galle Road, Colombo", 180, 20, { align: "right" });
        doc.text("Phone: +94 112 345 678", 180, 25, { align: "right" });
        
        // Document title
        doc.setFontSize(14); // Smaller title
        doc.setTextColor(primaryColor);
        doc.setFont(undefined, "bold");
        doc.text("APPOINTMENT REPORT", 105, 45, { align: "center" });
        
        // Document reference section
        let yPos = 60;
        
        // Horizontal line
        doc.setDrawColor(primaryColor);
        doc.setLineWidth(0.3);
        doc.line(15, yPos, 195, yPos);
        yPos += 8;
        
        // Reference information
        doc.setFontSize(9);
        doc.setTextColor(secondaryColor);
        doc.text("Date:", 15, yPos);
        doc.text("Time:", 15, yPos + lineHeight);
        
        doc.setFontSize(10);
        doc.setTextColor(primaryColor);
        doc.text(selectedAppointment.date, 40, yPos);
        doc.text(selectedAppointment.timeSlot, 40, yPos + lineHeight);
        
        // Status badge
        doc.setFillColor("#ffeeee");
        doc.setDrawColor(accentColor);
        doc.roundedRect(160, yPos - 3, 25, 8, 2, 2, 'FD');
        doc.setTextColor(accentColor);
        doc.setFontSize(8);
        doc.text("ACTIVE", 172.5, yPos + 2, { align: "center" });
        yPos += lineHeight * 2 + sectionSpacing;
        
        // Customer information section
        doc.setFontSize(12);
        doc.setTextColor(primaryColor);
        doc.text("Customer Info", 15, yPos);
        yPos += 6;
        
        // Customer details table
        const customerFields = [
            { label: "Name", value: selectedAppointment.name || "N/A" },
            { label: "Email", value: selectedAppointment.email || "N/A" },
            { label: "Phone", value: selectedAppointment.phone || "N/A" },
            { label: "Address", value: selectedAppointment.address || "N/A" }
        ];
        
        customerFields.forEach((field) => {
            doc.setFontSize(9);
            doc.setTextColor(secondaryColor);
            doc.text(`${field.label}:`, 15, yPos);
            
            doc.setFontSize(10);
            doc.setTextColor(darkColor);
            doc.text(field.value, 40, yPos);
            yPos += lineHeight;
        });
        yPos += sectionSpacing;
        
        // Device information section
        doc.setFontSize(12);
        doc.setTextColor(primaryColor);
        doc.text("Device Info", 15, yPos);
        yPos += 6;
        
        // Device details table
        const deviceFields = [
            { label: "Type", value: selectedAppointment.deviceType || "N/A" },
            { label: "Problem", value: selectedAppointment.problemType || "N/A" },
            { label: "Service", value: selectedAppointment.pickupOrDropoff || "N/A" },
            { label: "Chip Repair", value: selectedAppointment.chipLevelRepair ? "Yes" : "No" }
        ];
        
        deviceFields.forEach((field) => {
            doc.setFontSize(9);
            doc.setTextColor(secondaryColor);
            doc.text(`${field.label}:`, 15, yPos);
            
            doc.setFontSize(10);
            doc.setTextColor(darkColor);
            doc.text(field.value, 40, yPos);
            yPos += lineHeight;
        });
        yPos += sectionSpacing;
        
        // Issue description section
        doc.setFontSize(12);
        doc.setTextColor(primaryColor);
        doc.text("Issue", 15, yPos);
        yPos += 6;
        
        doc.setFontSize(9);
        doc.setTextColor(darkColor);
        const issueText = selectedAppointment.issueDescription || "No description provided";
        const issueLines = doc.splitTextToSize(issueText, 180);
        
        // Limit to 5 lines maximum
        const maxLines = 5;
        const displayLines = issueLines.slice(0, maxLines);
        displayLines.forEach(line => {
            doc.text(line, 15, yPos);
            yPos += lineHeight - 1;
        });
        
        if (issueLines.length > maxLines) {
            doc.setTextColor(secondaryColor);
            doc.text(`... (${issueLines.length - maxLines} more lines)`, 15, yPos);
            yPos += lineHeight;
        }
        yPos += sectionSpacing;
        
        // Additional information section
        doc.setFontSize(11);
        doc.setTextColor(primaryColor);
        doc.text("Additional Info", 15, yPos);
        yPos += 6;
        
        const additionalFields = [
            { label: "Attempted Fixes", value: selectedAppointment.attemptedFixes ? "Yes" : "No" },
            { label: "Backup Data", value: selectedAppointment.backupData ? "Yes" : "No" },
            { label: "Contact Method", value: selectedAppointment.contactMethod || "N/A" }
        ];
        
        additionalFields.forEach((field) => {
            doc.setFontSize(9);
            doc.setTextColor(secondaryColor);
            doc.text(`${field.label}:`, 15, yPos);
            
            doc.setFontSize(10);
            doc.setTextColor(darkColor);
            doc.text(field.value, 50, yPos);
            yPos += lineHeight;
        });
        yPos += sectionSpacing;
        
        // Progress status section (compact version)
        doc.setFontSize(12);
        doc.setTextColor(primaryColor);
        doc.text("Repair Progress", 15, yPos);
        yPos += 6;
        
        const circleRadius = 3;
        const circleSpacing = 25;
        const startX = 20;
        const progressY = yPos + 8;

        progressStages.forEach((stage, index) => {
            const x = startX + index * circleSpacing;
            const isActive = index <= currentStage;

            if (index > 0) {
                const prevX = startX + (index - 1) * circleSpacing;
                doc.setDrawColor(200, 200, 200);
                doc.setLineWidth(0.5);
                doc.line(prevX + circleRadius, progressY, x - circleRadius, progressY);
            }

            doc.setFillColor(isActive ? accentColor : "#eeeeee");
            doc.circle(x, progressY, circleRadius, "F");

            doc.setTextColor(isActive ? accentColor : secondaryColor);
            doc.setFontSize(7);
            doc.text(stage, x, progressY + circleRadius + 4, { align: "center" });
        });
        yPos += 20;
        
        // Signature section
        if (sign) {
            const signatureWidth = 25;
            const signatureHeight = 12;
            const signatureX = 160;
            const signatureY = yPos;
            doc.addImage(sign, "PNG", signatureX, signatureY, signatureWidth, signatureHeight);

            doc.setFontSize(9);
            doc.setTextColor(secondaryColor);
            doc.text("Signature:", 15, yPos + 8);
            
            doc.setFontSize(10);
            doc.setTextColor(darkColor);
            doc.text("John Doe", 160, yPos + signatureHeight + 4);
            yPos += 20;
        }
        
        // Footer
        doc.setFontSize(7);
        doc.setTextColor(secondaryColor);
        doc.text("Please show this report when the device is handed over.", 105, 280, { align: "center" });
        doc.text("For any questions, please call our support line at +94 112 345 678", 105, 285, { align: "center" });
        
        // Page border
        doc.setDrawColor(lightColor);
        doc.setLineWidth(0.5);
        doc.rect(5, 5, 200, 287);
        
        // Save the PDF
        doc.save(`Appointment_Report_${selectedAppointment.name.replace(/\s+/g, '_')}.pdf`);
    } catch (error) {
        console.error("Error generating report:", error);
        alert("Failed to generate report. Please check the console for details.");
    }
};
  // Calculate min and max dates for the date picker
  const today = new Date();
  const oneYearLater = new Date();
  oneYearLater.setFullYear(today.getFullYear() + 1);

  const formatDateForInput = (date) => {
    return date.toISOString().split('T')[0];
  };

  const minDate = formatDateForInput(today);
  const maxDate = formatDateForInput(oneYearLater);

  // Inline styles (same as before)
  const styles = {
    container: {
      fontFamily: "'Orbitron', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
      padding: "20px",
      maxWidth: "100%",
      margin: "0 auto",
      backgroundColor: "#0d1117",
      color: "#c9d1d9",
      minHeight: "100vh",
    },
    header: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "30px",
      padding: "20px",
      background: "linear-gradient(135deg, #6f00ff 0%, #00d2ff 100%)",
      borderRadius: "12px",
      color: "white",
      fontSize:"32px",
      boxShadow: "0 8px 20px rgba(0, 0, 0, 0.5)",
    },
    actionButtons: {
      display: "flex",
      gap: "12px",
    },
    button: {
      padding: "12px 20px",
      borderRadius: "8px",
      border: "none",
      cursor: "pointer",
      fontWeight: "700",
      fontSize: "18px",
      transition: "all 0.3s ease",
      background: "#1f1f1f",
      color: "#00ffe7",
      boxShadow: "0 4px 10px rgba(0, 255, 231, 0.3)",
      "&:hover": {
        background: "#00ffe7",
        color: "#1f1f1f",
        transform: "translateY(-2px)",
      },
    },
    primaryButton: {
      background: "linear-gradient(45deg, #ff0057, #ff7b00)",
      color: "white",
    },
    secondaryButton: {
      background: "linear-gradient(45deg, #00d2ff, #3a47d5)",
      color: "white",
    },
    tertiaryButton: {
      background: "linear-gradient(45deg, #00ffab, #00c2ff)",
      color: "white",
    },
    appointmentCards: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
      gap: "25px",
      marginTop: "30px",
    },
    card: {
      background: "#161b22",
      borderRadius: "10px",
      padding: "20px",
      boxShadow: "0 6px 15px rgba(0, 255, 255, 0.1)",
      borderLeft: "4px solid #00ffe7",
      transition: "transform 0.3s ease, box-shadow 0.3s ease",
      "&:hover": {
        transform: "translateY(-5px)",
        boxShadow: "0 8px 20px rgba(0, 255, 255, 0.2)",
      },
    },
    disabledCard: {
      background: "#2c2f33",
      borderColor: "#555",
      color: "#777",
    },
    cardHeader: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      borderBottom: "1px solid #30363d",
      marginBottom: "15px",
    },
    cardTitle: {
      fontSize: "24px",
      fontWeight: "600",
      color: "#00ffe7",
    },
    cardStatus: {
      padding: "6px 14px",
      borderRadius: "20px",
      fontSize: "16px",
      fontWeight: "700",
      textTransform: "uppercase",
      backgroundColor: "#21262d",
      color: "#00ffe7",
    },
    statusAccepted: {
      backgroundColor: "#0d6848",
      color: "#00ffb3",
    },
    statusPending: {
      backgroundColor: "#8a6d3b",
      color: "#ffd700",
    },
    statusRejected: {
      backgroundColor: "#6e0b14",
      color: "#ff4b5c",
    },
    cardContent: {
      marginBottom: "10px",
    },
    cardField: {
      display: "flex",
      fontSize: "18px",
      marginBottom: "8px",
      color: "#8b949e",
    },
    fieldLabel: {
      minWidth: "110px",
      fontWeight: "500",
      color: "#c9d1d9",
    },
    fieldValue: {
      color: "#58a6ff",
    },
    modalOverlay: {
      position: "fixed",
      top: "0",
      left: "0",
      right: "0",
      bottom: "0",
      backgroundColor: "rgba(0, 0, 0, 0.8)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: "1000",
      padding: "20px", // add padding to avoid touching edges
    },
    modal: {
      background: "#1a1a2e", // dark gaming theme
      borderRadius: "15px",
      width: "90%",       // smaller and responsive
      maxWidth: "600px",  // not too wide
      maxHeight: "80vh",  // fit within screen
      overflowY: "auto",
      boxShadow: "0 0 20px #00f2fe, 0 0 30px #4facfe",
      padding: "20px",
      color: "#f0f0f0",
      fontFamily: "'Orbitron', sans-serif", // futuristic font
    },
    modalHeader: {
      padding: "15px 20px",
      borderBottom: "1px solid #333",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      background: "linear-gradient(135deg, #4facfe, #00f2fe)",
      color: "#0d0d0d",
      fontSize: "20px",
      fontWeight: "bold",
      borderTopLeftRadius: "15px",
      borderTopRightRadius: "15px",
    },
    modalBody: {
      padding: "20px",
      backgroundColor: "#0f0f1c",
      borderBottomLeftRadius: "15px",
      borderBottomRightRadius: "15px",
    },
    closeButton: {
      background: "none",
      border: "none",
      fontSize: "28px",
      cursor: "pointer",
      color: "#0d0d0d",
    },
    
    inputGroup: {
      marginBottom: "20px",
    },
    label: {
      display: "block",
      marginBottom: "6px",
      fontWeight: "600",
      color: "#8b949e",
    },
    input: {
      width: "100%",
      padding: "10px",
      borderRadius: "6px",
      border: "1px solid #30363d",
      backgroundColor: "#0d1117",
      color: "#c9d1d9",
      fontSize: "14px",
    },
    inputReadOnly: {
      backgroundColor: "#21262d",
      color: "#777",
      cursor: "not-allowed",
    },
    textarea: {
      width: "100%",
      padding: "10px",
      borderRadius: "6px",
      border: "1px solid #30363d",
      backgroundColor: "#0d1117",
      color: "#c9d1d9",
      fontSize: "14px",
      minHeight: "120px",
      resize: "vertical",
    },
    select: {
      width: "100%",
      padding: "10px",
      borderRadius: "6px",
      backgroundColor: "#0d1117",
      color: "#c9d1d9",
      border: "1px solid #30363d",
    },
    modalFooter: {
      padding: "20px",
      borderTop: "1px solid #333",
      display: "flex",
      justifyContent: "flex-end",
      gap: "10px",
    },
    emptyState: {
      textAlign: "center",
      padding: "40px",
      backgroundColor: "#21262d",
      borderRadius: "8px",
      color: "#8b949e",
      fontStyle: "italic",
    },
    errorText: {
      color: "#ff4b5c",
      fontSize: "13px",
      marginTop: "5px",
    },
    progressBar: {
      margin: "30px 0",
    },
    progressTitle: {
      fontSize: "16px",
      fontWeight: "500",
      marginBottom: "15px",
      color: "#333",
    },
    progressStages: {
      display: "flex",
      justifyContent: "space-between",
      position: "relative",
      marginBottom: "40px",
    },
    progressStage: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      flex: "1",
      position: "relative",
    },
    circle: {
      width: "20px",
      height: "20px",
      borderRadius: "50%",
      backgroundColor: "#ddd",
      marginBottom: "10px",
      position: "relative",
      zIndex: "2",
    },
    activeCircle: {
      backgroundColor: "#00bcd4",
      boxShadow: "0 0 0 3px rgba(0, 188, 212, 0.3)",
    },
    stageLabel: {
      fontSize: "12px",
      textAlign: "center",
      color: "#666",
      position: "absolute",
      bottom: "-25px",
      width: "100%",
    },
    progressLine: {
      position: "absolute",
      top: "10px",
      left: "0",
      right: "0",
      height: "2px",
      backgroundColor: "#ddd",
      zIndex: "1",
    },
     generateReportBtn: {
      background: "linear-gradient(90deg, #00f7ff, #0e5fd8)",
      color: "black",
      border: "none",
      padding: "12px 26px",
      fontSize: "14px",
      fontWeight: "bold",
      borderRadius: "25px",
      cursor: "pointer",
      boxShadow: "0 0 15px #00f7ff, 0 0 30px #0e5fd8",
      transition: "transform 0.3s ease, box-shadow 0.3s ease, opacity 0.3s ease",
      zIndex: 2,
    },
   "&:disabled": {
  background: "#d3d3d3",  // Light grey background
  color: "#aaa",  // Lighter grey text color
  cursor: "not-allowed",  // Not allowed cursor style
  boxShadow: "none",  // No shadow for disabled button
  opacity: 0.6,  // Reduced opacity for a disabled effect
}

    
  };
  
  return (
    <div style={styles.container}>
      {/* Header with Action Buttons */}
      <div style={styles.header}>
        <h1 style={{ margin: 0 }}>Appointment Dashboard</h1>
        <div style={styles.actionButtons}>
          <button
            style={{ ...styles.button, ...styles.primaryButton }}
            onClick={() => navigate("/appointment-form")}
          >
            Make an Appointment
          </button>
          <button
            style={{ ...styles.button, ...styles.secondaryButton }}
            onClick={() => navigate("/draftedTechnicianReport")}
          >
            Drafted Reports
          </button>
          <button
            style={{ ...styles.button, ...styles.tertiaryButton }}
            onClick={() => navigate("/AppointmenentAI")}
          >
            Self Diagnosis
          </button>
        </div>
      </div>

      {/* Appointment Cards Section */}
      <div>
        <h2 style={{ color: "#333", marginBottom: "20px" }}>Appointment Details</h2>
        {appointments.length > 0 ? (
          <div style={styles.appointmentCards}>
            {appointments.map((appointment) => (
              <div
                key={appointment._id}
                style={{
                  ...styles.card,
                  ...(appointment.status === "pending" || appointment.status === "rejected" ? styles.disabledCard : {})
                }}
                onClick={() => handleRowClick(appointment)}
              >
                <div style={styles.cardHeader}>
                  <h3 style={styles.cardTitle}>{appointment.name}</h3>
                  <span style={{
                    ...styles.cardStatus,
                    ...(appointment.status === "accepted" ? styles.statusAccepted :
                      appointment.status === "rejected" ? styles.statusRejected :
                        styles.statusPending)
                  }}>
                    {appointment.status}
                  </span>
                </div>
                <div style={styles.cardContent}>
                  <div style={styles.cardField}>
                    <span style={styles.fieldLabel}>Device:</span>
                    <span style={styles.fieldValue}>{appointment.deviceType}</span>
                  </div>
                  <div style={styles.cardField}>
                    <span style={styles.fieldLabel}>Issue:</span>
                    <span style={styles.fieldValue}>{appointment.issueDescription.substring(0, 50)}...</span>
                  </div>
                  <div style={styles.cardField}>
                    <span style={styles.fieldLabel}>Date:</span>
                    <span style={styles.fieldValue}>{appointment.date} at {appointment.timeSlot}</span>
                  </div>
                  {appointment.status === "rejected" && (
                    <div style={styles.cardField}>
                      <span style={styles.fieldLabel}>Reason:</span>
                      <span style={{ ...styles.fieldValue, color: "#e53935" }}>
                        {appointment.rejectionReason}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={styles.emptyState}>
            <h3>No appointments found</h3>
            <p>Create your first appointment by clicking the button above</p>
          </div>
        )}
      </div>

      {/* Modal for Detailed View and Editing */}
      {isModalOpen && selectedAppointment && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <div style={styles.modalHeader}>
              <h2 style={{ margin: 0 }}>Edit Appointment</h2>
              <button style={styles.closeButton} onClick={() => setIsModalOpen(false)}>
                &times;
              </button>
            </div>
            <div style={styles.modalBody}>
              {/* Input Fields */}
              <div style={styles.inputGroup}>
                <label style={styles.label}>Name:</label>
                <input
                  type="text"
                  name="name"
                  value={selectedAppointment.name}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Email:</label>
                <input
                  type="email"
                  name="email"
                  value={selectedAppointment.email}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Phone:</label>
                <input
                  type="text"
                  name="phone"
                  value={selectedAppointment.phone}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Address:</label>
                <input
                  type="text"
                  name="address"
                  value={selectedAppointment.address}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Device Type:</label>
                <input
                  type="text"
                  name="deviceType"
                  value={selectedAppointment.deviceType}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Issue Description:</label>
                <textarea
                  name="issueDescription"
                  value={selectedAppointment.issueDescription}
                  onChange={handleInputChange}
                  style={{ ...styles.textarea, ...(!isEditMode ? styles.textareaReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Contact Method:</label>
                <input
                  type="text"
                  name="contactMethod"
                  value={selectedAppointment.contactMethod}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Date:</label>
                <input
                  type="date"
                  name="date"
                  value={selectedAppointment.date}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                  min={minDate}
                  max={maxDate}
                />
                {dateError && <p style={styles.errorText}>{dateError}</p>}
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Time Slot:</label>
                <select
                  name="timeSlot"
                  value={selectedAppointment.timeSlot}
                  onChange={handleInputChange}
                  style={{ ...styles.select, ...(!isEditMode ? styles.selectReadOnly : {}) }}
                  disabled={!isEditMode}
                >
                  {availableTimeSlots.map((slot, index) => (
                    <option key={index} value={slot}>{slot}</option>
                  ))}
                </select>
                {timeError && <p style={styles.errorText}>{timeError}</p>}
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Problem Type:</label>
                <input
                  type="text"
                  name="problemType"
                  value={selectedAppointment.problemType}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.inputGroup}>
                <label style={styles.label}>Pickup/Dropoff:</label>
                <input
                  type="text"
                  name="pickupOrDropoff"
                  value={selectedAppointment.pickupOrDropoff}
                  onChange={handleInputChange}
                  style={{ ...styles.input, ...(!isEditMode ? styles.inputReadOnly : {}) }}
                  readOnly={!isEditMode}
                />
              </div>

              <div style={styles.checkboxGroup}>
                <input
                  type="checkbox"
                  name="chipLevelRepair"
                  checked={selectedAppointment.chipLevelRepair}
                  onChange={(e) => isEditMode && setSelectedAppointment({ ...selectedAppointment, chipLevelRepair: e.target.checked })}
                  style={styles.checkbox}
                  readOnly={!isEditMode}
                />
                <label style={styles.label}>Chip-Level Repair</label>
              </div>

              <div style={styles.checkboxGroup}>
                <input
                  type="checkbox"
                  name="attemptedFixes"
                  checked={selectedAppointment.attemptedFixes}
                  onChange={(e) => isEditMode && setSelectedAppointment({ ...selectedAppointment, attemptedFixes: e.target.checked })}
                  style={styles.checkbox}
                  readOnly={!isEditMode}
                />
                <label style={styles.label}>Attempted Fixes</label>
              </div>

              <div style={styles.checkboxGroup}>
                <input
                  type="checkbox"
                  name="backupData"
                  checked={selectedAppointment.backupData}
                  onChange={(e) => isEditMode && setSelectedAppointment({ ...selectedAppointment, backupData: e.target.checked })}
                  style={styles.checkbox}
                  readOnly={!isEditMode}
                />
                <label style={styles.label}>Backup Data</label>
              </div>

              {/* Status Info */}
              <div style={{ margin: "20px 0" }}>
                <p style={{ fontWeight: "500" }}>
                  Status:{" "}
                  <span style={{
                    ...(selectedAppointment.status === "accepted" ? styles.statusAccepted :
                      selectedAppointment.status === "rejected" ? styles.statusRejected :
                        styles.statusPending),
                    padding: "6px 12px",
                    borderRadius: "20px"
                  }}>
                    {selectedAppointment.status}
                  </span>
                </p>
                {selectedAppointment.status === "rejected" && (
                  <p>
                    <strong>Reason for Rejection:</strong> {selectedAppointment.rejectionReason}
                  </p>
                )}
              </div>

              {/* Progress Bar */}
              <div style={styles.progressBar}>
                <h3 style={styles.progressTitle}>Progress</h3>
                <div style={styles.progressStages}>
                  <div style={styles.progressLine}></div>
                  {progressStages.map((stage, index) => (
                    <div key={index} style={styles.progressStage}>
                      <div style={{
                        ...styles.circle,
                        ...(index <= currentStage ? styles.activeCircle : {})
                      }}></div>
                      <span style={styles.stageLabel}>{stage}</span>
                    </div>
                  ))}
                </div>
              </div>
              <br></br>
              {/* Generate Report Button */}
              <button
  style={{
    ...styles.generateReportBtn,
    ...(selectedAppointment.status === "pending" || selectedAppointment.status === "rejected"
      ? {
          backgroundColor: "#d3d3d3", // Grey color
          color: "#aaa", // Lighter text color
          cursor: "not-allowed", // Prevent cursor change to pointer
          opacity: 0.6, // Make it look disabled
          boxShadow: "none", // Remove shadow
        }
      : {}),
  }}
  onClick={generateReport}
  disabled={selectedAppointment.status === "pending" || selectedAppointment.status === "rejected"}
>
  {selectedAppointment.status === "pending" || selectedAppointment.status === "rejected" 
    ? "Report Not Available" 
    : "Generate Report"}
</button>

              <br></br>
              <br></br>
              {(selectedAppointment.status === "accepted" || selectedAppointment.status === "rejected") && (
                <p style={styles.modalNote}>
                  Appointment details cannot be edited after it has been accepted or rejected.
                </p>
              )}
            </div>

            {/* Modal Footer */}
            <div style={styles.modalFooter}>
              <button
                style={{
                  ...styles.button,
                  ...(selectedAppointment.status === "accepted" || selectedAppointment.status === "rejected" ? styles.disabledButton : styles.primaryButton)
                }}
                onClick={handleUpdate}
                disabled={selectedAppointment.status === "accepted" || selectedAppointment.status === "rejected"}
              >
                Save Changes
              </button>
              <button
                style={{
                  ...styles.button,
                  ...(selectedAppointment.status === "accepted" || selectedAppointment.status === "rejected" ? styles.disabledButton : styles.secondaryButton)
                }}
                onClick={handleDelete}
                disabled={selectedAppointment.status === "accepted" || selectedAppointment.status === "rejected"}
              >
               
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AppointmentDashboard;