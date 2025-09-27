import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { FaUser, FaEnvelope, FaCalendarAlt, FaClock, FaTags, FaMapMarkerAlt, FaTools, FaCheck, FaTimes, FaFileExport } from "react-icons/fa";
import { jsPDF } from "jspdf";
import autoTable from "jspdf-autotable";
import logo from "../../../assets/AlphaITSolutionsLogo.jpg";


// Register ChartJS components
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const Admin_AppointmentDashboard = () => {
  const [appointments, setAppointments] = useState([]);
  const [filteredAppointments, setFilteredAppointments] = useState([]);
  const [selectedAppointment, setSelectedAppointment] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [currentStage, setCurrentStage] = useState(-1);
  const [rejectionReason, setRejectionReason] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [isButtonDisabled, setIsButtonDisabled] = useState(false);
  const navigate = useNavigate();

  const progressStages = [
    "Device Handover",
    "Diagnosis",
    "Repair",
    "Testing",
    "Device Ready to Pick",
  ];

  // Color scheme
  const colors = {
    primary: "#6c5ce7",
    secondary: "#a29bfe",
    accent: "#fd79a8",
    success: "#00b894",
    danger: "#d63031",
    warning: "#fdcb6e",
    info: "#0984e3",
    light: "#f5f6fa",
    dark: "#2d3436",
    white: "#ffffff",
    gray: "#dfe6e9"
  };

  // CSS styles
  const styles = {
    container: {
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      background: `linear-gradient(135deg, ${colors.light} 0%, ${colors.white} 100%)`,
      padding: "2rem",
      minHeight: "100vh",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
    },
    header: {
      background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`,
      color: colors.white,
      padding: "1.5rem 2.5rem",
      borderRadius: "12px",
      marginBottom: "2rem",
      boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
      width: "90%",
      maxWidth: "1200px",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
    },
    headerActions: {
      display: "flex",
      gap: "1rem",
      alignItems: "center",
    },
    searchBar: {
      padding: "0.75rem 1.25rem",
      borderRadius: "8px",
      border: "none",
      fontSize: "1rem",
      width: "300px",
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      transition: "all 0.3s ease",
      "&:focus": {
        outline: "none",
        boxShadow: `0 2px 12px ${colors.secondary}`
      }
    },
    chartContainer: {
      backgroundColor: colors.white,
      padding: "1.5rem",
      borderRadius: "12px",
      boxShadow: "0 4px 16px rgba(0,0,0,0.08)",
      marginBottom: "2rem",
      width: "90%",
      maxWidth: "1200px",
    },
    appointmentGrid: {
      width: "90%",
      maxWidth: "1200px",
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
      gap: "1.5rem",
    },
    appointmentCard: {
      background: colors.white,
      borderRadius: "12px",
      boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
      padding: "1.5rem",
      cursor: "pointer",
      transition: "all 0.3s ease",
      borderLeft: `4px solid ${colors.primary}`,
      "&:hover": {
        transform: "translateY(-5px)",
        boxShadow: "0 8px 24px rgba(0,0,0,0.12)"
      }
    },
    statusBadge: {
      padding: "0.25rem 0.75rem",
      borderRadius: "20px",
      fontSize: "0.75rem",
      fontWeight: "600",
      textTransform: "uppercase",
      letterSpacing: "0.5px"
    },
    modalOverlay: {
      position: "fixed",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      backgroundColor: "rgba(0,0,0,0.5)",
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      zIndex: 1000,
      backdropFilter: "blur(4px)"
    },
    modal: {
      background: colors.white,
      borderRadius: "16px",
      padding: "2rem",
      boxShadow: "0 8px 32px rgba(0,0,0,0.2)",
      width: "90%",
      maxWidth: "700px",
      maxHeight: "90vh",
      overflowY: "auto"
    },
    modalHeader: {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: "1.5rem",
      paddingBottom: "1rem",
      borderBottom: `2px solid ${colors.gray}`
    },
    closeButton: {
      background: "none",
      border: "none",
      fontSize: "1.5rem",
      cursor: "pointer",
      color: colors.dark,
      opacity: 0.7,
      transition: "all 0.2s ease",
      "&:hover": {
        opacity: 1,
        transform: "rotate(90deg)"
      }
    },
    progressContainer: {
      margin: "2rem 0",
      padding: "1.5rem",
      background: "#f8f9fa",
      borderRadius: "12px",
      border: `1px solid ${colors.gray}`
    },
    progressBar: {
      height: "8px",
      background: colors.gray,
      borderRadius: "4px",
      margin: "1rem 0",
      overflow: "hidden"
    },
    progressFill: {
      height: "100%",
      background: `linear-gradient(90deg, ${colors.primary}, ${colors.accent})`,
      borderRadius: "4px",
      transition: "width 0.5s ease",
      width: `${((currentStage + 1) / progressStages.length) * 100}%`
    },
    progressStages: {
      display: "flex",
      justifyContent: "space-between",
      marginTop: "1rem",
      position: "relative"
    },
    progressStage: {
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      position: "relative",
      zIndex: 1
    },
    stageCircle: {
      width: "32px",
      height: "32px",
      borderRadius: "50%",
      background: colors.white,
      border: `2px solid ${colors.gray}`,
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      marginBottom: "0.5rem",
      transition: "all 0.3s ease",
      "&.active": {
        background: colors.primary,
        borderColor: colors.primary,
        color: colors.white
      },
      "&:hover": {
        transform: "scale(1.1)",
        boxShadow: `0 0 0 4px ${colors.secondary}`
      }
    },
    stageLabel: {
      fontSize: "0.75rem",
      fontWeight: "600",
      textAlign: "center",
      color: colors.dark,
      maxWidth: "80px"
    },
    actionButton: {
      padding: "0.75rem 1.5rem",
      borderRadius: "8px",
      border: "none",
      fontSize: "1rem",
      fontWeight: "600",
      cursor: "pointer",
      transition: "all 0.3s ease",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "0.5rem",
      "&:disabled": {
        opacity: 0.6,
        cursor: "not-allowed"
      }
    },
    acceptButton: {
      background: `linear-gradient(135deg, ${colors.success} 0%, #00a884 100%)`,
      color: colors.white,
      "&:hover:not(:disabled)": {
        transform: "translateY(-2px)",
        boxShadow: `0 4px 12px ${colors.success}`
      }
    },
    rejectButton: {
      background: `linear-gradient(135deg, ${colors.danger} 0%, #c0392b 100%)`,
      color: colors.white,
      "&:hover:not(:disabled)": {
        transform: "translateY(-2px)",
        boxShadow: `0 4px 12px ${colors.danger}`
      }
    },
    detailItem: {
      display: "flex",
      marginBottom: "0.75rem",
      "& strong": {
        minWidth: "150px",
        color: colors.dark,
        fontWeight: "600"
      },
      "& span": {
        color: colors.dark,
        flex: 1
      }
    },
    textArea: {
      width: "100%",
      padding: "1rem",
      borderRadius: "8px",
      border: `1px solid ${colors.gray}`,
      fontSize: "1rem",
      marginTop: "1rem",
      minHeight: "100px",
      resize: "vertical",
      transition: "all 0.3s ease",
      "&:focus": {
        outline: "none",
        borderColor: colors.primary,
        boxShadow: `0 0 0 3px ${colors.secondary}`
      }
    },
    exportButton: {
      background: `linear-gradient(135deg, ${colors.info} 0%, #0984e3 100%)`,
      color: colors.white,
      padding: "0.75rem 1.5rem",
      borderRadius: "8px",
      border: "none",
      fontSize: "1rem",
      fontWeight: "600",
      cursor: "pointer",
      transition: "all 0.3s ease",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "0.5rem",
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
      "&:hover": {
        transform: "translateY(-2px)",
        boxShadow: `0 4px 12px ${colors.info}`
      }
    },
    clearButton: {
      background: `linear-gradient(135deg, ${colors.info} 0%, #0984e3 100%)`,
      color: colors.white,
      "&:hover:not(:disabled)": {
        transform: "translateY(-2px)",
        boxShadow: `0 4px 12px ${colors.info}`
      }
    }
  };

  // Prepare chart data
  const getChartData = () => {
    const statusCounts = {
      pending: 0,
      accepted: 0,
      rejected: 0,
    };

    appointments.forEach((appointment) => {
      if (statusCounts.hasOwnProperty(appointment.status)) {
        statusCounts[appointment.status] = (statusCounts[appointment.status] || 0) + 1;
      }
    });

    return {
      labels: ["Pending", "Accepted", "Rejected"],
      datasets: [
        {
          label: "Appointments by Status",
          data: [
            statusCounts.pending,
            statusCounts.accepted,
            statusCounts.rejected,
          ],
          backgroundColor: [
            colors.warning,
            colors.success,
            colors.danger,
          ],
          borderColor: [
            colors.warning,
            colors.success,
            colors.danger,
          ],
          borderWidth: 1,
          borderRadius: 4,
          hoverBackgroundColor: [
            `${colors.warning}dd`,
            `${colors.success}dd`,
            `${colors.danger}dd`,
          ],
        },
      ],
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: "top",
        labels: {
          font: {
            family: "'Inter', sans-serif",
            size: 14,
          },
          color: colors.dark,
          usePointStyle: true,
          padding: 20,
        },
      },
      title: {
        display: true,
        text: "Appointment Status Distribution",
        font: {
          family: "'Inter', sans-serif",
          size: 18,
          weight: "600",
        },
        color: colors.dark,
        padding: {
          bottom: 20,
        },
      },
      tooltip: {
        backgroundColor: colors.white,
        titleColor: colors.dark,
        bodyColor: colors.dark,
        borderColor: colors.gray,
        borderWidth: 1,
        padding: 12,
        boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
        cornerRadius: 8,
        displayColors: true,
        usePointStyle: true,
        callbacks: {
          label: function(context) {
            return `${context.dataset.label}: ${context.raw}`;
          }
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: `${colors.gray}33`,
          drawBorder: false,
        },
        ticks: {
          color: colors.dark,
          font: {
            family: "'Inter', sans-serif",
          },
          stepSize: 1,
        },
      },
      x: {
        grid: {
          display: false,
          drawBorder: false,
        },
        ticks: {
          color: colors.dark,
          font: {
            family: "'Inter', sans-serif",
          },
        },
      },
    },
  };

  // Fetch appointments
  useEffect(() => {
    const fetchAppointments = async () => {
      try {
        const token = localStorage.getItem("token");
        if (!token) {
          console.error("No authentication token found. Redirecting to login...");
          navigate("/login");
          return;
        }

        const response = await fetch("http://localhost:5000/api/appointments/all", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch appointments: ${response.status}`);
        }

        const data = await response.json();
        setAppointments(data);
        setFilteredAppointments(data);
      } catch (error) {
        console.error("Error fetching appointments:", error);
      }
    };

    fetchAppointments();
  }, [navigate]);

  // Handle search
  useEffect(() => {
    const filtered = appointments.filter(
      (appointment) =>
        appointment.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        appointment.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        appointment.issueDescription.toLowerCase().includes(searchQuery.toLowerCase())
    );
    setFilteredAppointments(filtered);
  }, [searchQuery, appointments]);

  // Handle row/card click to open modal
  const handleRowClick = (appointment) => {
    setSelectedAppointment(appointment);
    setIsModalOpen(true);
    setCurrentStage(appointment.progress || -1);
    setRejectionReason(appointment.rejectionReason || "");
    setIsButtonDisabled(appointment.status === "accepted" || appointment.status === "rejected");
  };

  // Update appointment status
  const updateAppointmentStatus = async (status, reason = "") => {
    try {
      setIsButtonDisabled(true);
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:5000/api/appointments/${selectedAppointment._id}/status`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ status, rejectionReason: reason }),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update appointment status");
      }

      const updatedAppointment = await response.json();
      setAppointments((prev) =>
        prev.map((app) => (app._id === updatedAppointment._id ? updatedAppointment : app))
      );
      setFilteredAppointments((prev) =>
        prev.map((app) => (app._id === updatedAppointment._id ? updatedAppointment : app))
      );
      setIsModalOpen(false);
    } catch (error) {
      console.error("Error updating appointment status:", error);
      setIsButtonDisabled(false);
    }
  };

  // Update appointment progress
  const updateProgress = async (stageIndex) => {
    try {
      const token = localStorage.getItem("token");
      const url = `http://localhost:5000/api/appointments/${selectedAppointment._id}/progress`;
      const payload = JSON.stringify({ progress: stageIndex });

      const response = await fetch(url, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: payload,
      });

      if (!response.ok) {
        throw new Error("Failed to update progress");
      }

      const updatedAppointment = await response.json();
      setSelectedAppointment(updatedAppointment);
      setCurrentStage(stageIndex);
      setAppointments((prev) =>
        prev.map((app) => (app._id === updatedAppointment._id ? updatedAppointment : app))
      );
      setFilteredAppointments((prev) =>
        prev.map((app) => (app._id === updatedAppointment._id ? updatedAppointment : app))
      );
    } catch (error) {
      console.error("Error updating progress:", error);
    }
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case "pending":
        return {
          background: `${colors.warning}20`,
          color: colors.warning,
          border: `1px solid ${colors.warning}`
        };
      case "accepted":
        return {
          background: `${colors.success}20`,
          color: colors.success,
          border: `1px solid ${colors.success}`
        };
      case "rejected":
        return {
          background: `${colors.danger}20`,
          color: colors.danger,
          border: `1px solid ${colors.danger}`
        };
      case "completed":
        return {
          background: `${colors.info}20`,
          color: colors.info,
          border: `1px solid ${colors.info}`
        };
      default:
        return {
          background: `${colors.gray}20`,
          color: colors.gray,
          border: `1px solid ${colors.gray}`
        };
    }
  };

  const clearTimeslot = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(
        `http://localhost:5000/api/appointments/${selectedAppointment._id}/clear-timeslot`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error("Failed to clear timeslot");
      }

      const updatedAppointment = await response.json();
      setAppointments((prev) =>
        prev.map((app) => (app._id === updatedAppointment._id ? updatedAppointment : app))
      );
      setFilteredAppointments((prev) =>
        prev.map((app) => (app._id === updatedAppointment._id ? updatedAppointment : app))
      );
      setSelectedAppointment(updatedAppointment);
    } catch (error) {
      console.error("Error clearing timeslot:", error);
    }
  };

  const generatePDFReport = () => {
    try {
      const dataToExport = searchQuery ? filteredAppointments : appointments;
      if (dataToExport.length === 0) {
        alert("No data to export!");
        return;
      }
  
      // Colors
      const primaryColor = "#2c3e50";
      const secondaryColor = "#7f8c8d";
      const accentColor = "#e74c3c";
      const darkColor = "#1F2937";
      const lightColor = "#F9FAFB";
  
      const doc = new jsPDF();
      doc.setFont("helvetica");
  
      // --- HEADER ---
      const logoWidth = 30;
      const logoHeight = 30;
      doc.addImage(logo, "JPEG", 15, 10, logoWidth, logoHeight);
  
      doc.setFontSize(12);
      doc.setTextColor(primaryColor);
      doc.text("Alpha IT Solutions", 180, 15, { align: "right" });
      doc.setFontSize(10);
      doc.setTextColor(secondaryColor);
      doc.text("123 Galle Road, Colombo", 180, 20, { align: "right" });
      doc.text("Phone: +94 112 345 678", 180, 25, { align: "right" });
  
      // --- TITLE ---
      doc.setFontSize(18);
      doc.setTextColor(primaryColor);
      doc.setFont(undefined, "bold");
      doc.text("Appointments Report", 105, 45, { align: "center" });
  
      // --- SUMMARY INFO ---
      doc.setFontSize(10);
      doc.setTextColor(secondaryColor);
      let summaryStart = 55;
      doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 15, summaryStart);
      doc.text(`Total Appointments: ${dataToExport.length}`, 15, summaryStart + 6);
      if (searchQuery) {
        doc.text(`Search Filter: "${searchQuery}"`, 15, summaryStart + 12);
      }
  
      // --- SEPARATOR LINE ---
      doc.setDrawColor(primaryColor);
      doc.setLineWidth(0.5);
      doc.line(15, summaryStart + 20, 195, summaryStart + 20);
  
      // --- TABLE OF APPOINTMENTS ---
      const tableStartY = summaryStart + 25;
      const tableData = dataToExport.map(appointment => [
        appointment.name,
        appointment.deviceType,
        appointment.date,
        appointment.timeSlot,
        appointment.status,
      ]);
  
      autoTable(doc, {
        startY: tableStartY,
        head: [['Name', 'Device', 'Date', 'Time', 'Status']],
        body: tableData,
        headStyles: {
          fillColor: primaryColor,
          textColor: lightColor,
          fontStyle: 'bold',
        },
        alternateRowStyles: {
          fillColor: [lightColor],
        },
        styles: {
          fontSize: 9,
          cellPadding: 2,
        },
        columnStyles: {
          0: { cellWidth: 40 },
          1: { cellWidth: 30 },
          2: { cellWidth: 25 },
          3: { cellWidth: 25 },
          4: { cellWidth: 30 },
        },
        margin: { left: 15, right: 15 },
      });
  
      // --- DETAILED SECTIONS ---
      let yPosition = doc.lastAutoTable.finalY + 15;
      dataToExport.forEach((appointment, index) => {
        if (yPosition > 230) { // Lower threshold for spacing
          doc.addPage();
          yPosition = 20;
        }
  
        // Title for Each Appointment
        doc.setFontSize(14);
        doc.setFont(undefined, "bold");
        doc.setTextColor(primaryColor);
        doc.text(`Appointment #${index + 1}`, 15, yPosition);
  
        // Status Badge
        const statusColors = {
          pending: { bg: [255, 193, 7], text: [0, 0, 0] },
          accepted: { bg: [46, 125, 50], text: [255, 255, 255] },
          rejected: { bg: [211, 47, 47], text: [255, 255, 255] },
          completed: { bg: [25, 118, 210], text: [255, 255, 255] }
        };
        const status = appointment.status.toLowerCase();
        const color = statusColors[status] || { bg: [158, 158, 158], text: [255, 255, 255] };
  
        doc.setFillColor(color.bg[0], color.bg[1], color.bg[2]);
        doc.setTextColor(color.text[0], color.text[1], color.text[2]);
        doc.roundedRect(160, yPosition - 7, 30, 10, 2, 2, 'F');
        doc.text(status.toUpperCase(), 175, yPosition, { align: "center" });
  
        yPosition += 10;
  
        // Customer Info
        doc.setFontSize(10);
        doc.setFont(undefined, "normal");
        doc.setTextColor(darkColor);
        doc.text(`Name: ${appointment.name}`, 15, yPosition += 10);
        doc.text(`Email: ${appointment.email}`, 15, yPosition += 6);
        doc.text(`Phone: ${appointment.phone}`, 15, yPosition += 6);
        doc.text(`Address: ${appointment.address}`, 15, yPosition += 6);
  
        // Device Info
        doc.text(`Device Type: ${appointment.deviceType}`, 100, yPosition - 18);
        doc.text(`Issue: ${appointment.issueDescription.substring(0, 60)}${appointment.issueDescription.length > 60 ? '...' : ''}`, 100, yPosition - 12);
        doc.text(`Date & Time: ${appointment.date} @ ${appointment.timeSlot}`, 100, yPosition - 6);
  
        // Progress if Accepted
        if (appointment.status.toLowerCase() === 'accepted') {
          doc.text(`Progress: ${appointment.progress !== undefined ? progressStages[appointment.progress] : 'Not started'}`, 100, yPosition);
        }
  
        // Horizontal Line
        doc.setDrawColor(220, 220, 220);
        doc.setLineWidth(0.2);
        doc.line(15, yPosition + 8, 195, yPosition + 8);
  
        yPosition += 15;
      });
  
      // --- FOOTER ---
      doc.setFontSize(8);
      doc.setTextColor(secondaryColor);
      doc.text("Confidential - Alpha IT Solutions", 105, 285, { align: "center" });
      doc.text(`Generated on ${new Date().toLocaleString()}`, 105, 290, { align: "center" });
  
      // --- SAVE PDF ---
      const today = new Date();
      const dateString = `${today.getFullYear()}-${(today.getMonth() + 1).toString().padStart(2, '0')}-${today.getDate().toString().padStart(2, '0')}`;
      doc.save(`Appointments_Report_${dateString}.pdf`);
  
    } catch (error) {
      console.error("Error generating PDF report:", error);
      alert("Failed to generate PDF report. Please check the console for details.");
    }
  };
  

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={{ margin: 0, fontSize: "1.8rem", fontWeight: "700" }}>
          Appointment Dashboard
        </h1>
        <div style={styles.headerActions}>
          <input
            type="text"
            placeholder="Search appointments..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={styles.searchBar}
            className="search-bar"
          />
          <button 
            style={styles.exportButton} 
            onClick={generatePDFReport}
            title="Export to PDF"
          >
            <FaFileExport /> Export
          </button>
        </div>
      </div>

      {/* Chart Section */}
      <div style={styles.chartContainer}>
        <div style={{ height: "300px" }}>
          <Bar data={getChartData()} options={chartOptions} />
        </div>
      </div>

      {/* Appointment Cards */}
      <div style={styles.appointmentGrid}>
        {filteredAppointments.length > 0 ? (
          filteredAppointments.map((appointment) => {
            const statusStyle = getStatusColor(appointment.status);

            return (
              <div
                key={appointment._id}
                onClick={() => handleRowClick(appointment)}
                style={styles.appointmentCard}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                  <h3 style={{ margin: 0, color: colors.primary, fontWeight: "600" }}>
                    {appointment.name}
                  </h3>
                  <div style={{
                    ...styles.statusBadge,
                    ...statusStyle
                  }}>
                    {appointment.status}
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                  <FaEnvelope style={{ marginRight: "0.5rem", color: colors.secondary }} />
                  <span style={{ color: colors.dark }}>{appointment.email}</span>
                </div>

                <div style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                  <FaCalendarAlt style={{ marginRight: "0.5rem", color: colors.secondary }} />
                  <span style={{ color: colors.dark }}>{appointment.date}</span>
                </div>

                <div style={{ display: "flex", alignItems: "center", marginBottom: "0.5rem" }}>
                  <FaClock style={{ marginRight: "0.5rem", color: colors.secondary }} />
                  <span style={{ color: colors.dark }}>{appointment.timeSlot}</span>
                </div>

                <div style={{ display: "flex", alignItems: "flex-start", marginBottom: "1rem" }}>
                  <FaTags style={{ marginRight: "0.5rem", color: colors.secondary, marginTop: "0.25rem" }} />
                  <span style={{ color: colors.dark }}>
                    {appointment.issueDescription.substring(0, 60)}
                    {appointment.issueDescription.length > 60 && "..."}
                  </span>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "1rem", borderTop: `1px solid ${colors.gray}` }}>
                  <div style={{ display: "flex", alignItems: "center" }}>
                    <FaTools style={{ marginRight: "0.5rem", color: colors.secondary }} />
                    <span style={{ color: colors.dark, fontSize: "0.875rem" }}>{appointment.deviceType}</span>
                  </div>
                  <FaMapMarkerAlt style={{ color: colors.secondary }} />
                </div>
              </div>
            );
          })
        ) : (
          <div style={{
            gridColumn: "1 / -1",
            textAlign: "center",
            padding: "2rem",
            color: colors.gray,
            background: colors.white,
            borderRadius: "12px",
            boxShadow: "0 4px 12px rgba(0,0,0,0.08)"
          }}>
            <p style={{ fontSize: "1.2rem", marginBottom: "1rem" }}>No appointments found</p>
            <p style={{ color: colors.secondary }}>Try adjusting your search query</p>
          </div>
        )}
      </div>

      {/* Modal */}
      {isModalOpen && selectedAppointment && (
        <div style={styles.modalOverlay}>
          <div style={styles.modal}>
            <div style={styles.modalHeader}>
              <h2 style={{ margin: 0, color: colors.primary, fontWeight: "600" }}>
                Appointment Details
              </h2>
              <button
                style={styles.closeButton}
                onClick={() => setIsModalOpen(false)}
              >
                &times;
              </button>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <div style={styles.detailItem}>
                <strong>Name:</strong>
                <span>{selectedAppointment.name}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Email:</strong>
                <span>{selectedAppointment.email}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Phone:</strong>
                <span>{selectedAppointment.phone}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Address:</strong>
                <span>{selectedAppointment.address}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Device Type:</strong>
                <span>{selectedAppointment.deviceType}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Issue:</strong>
                <span>{selectedAppointment.issueDescription}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Date:</strong>
                <span>{selectedAppointment.date}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Time Slot:</strong>
                <span>{selectedAppointment.timeSlot}</span>
              </div>
              <div style={styles.detailItem}>
                <strong>Status:</strong>
                <span style={{
                  display: "inline-block",
                  padding: "0.25rem 0.75rem",
                  borderRadius: "20px",
                  ...getStatusColor(selectedAppointment.status)
                }}>
                  {selectedAppointment.status}
                </span>
              </div>
            </div>

            {selectedAppointment.status === "accepted" && (
              <div style={styles.progressContainer}>
                <h3 style={{ marginTop: 0, color: colors.primary, fontWeight: "600" }}>
                  Repair Progress
                </h3>

                {/* Progress bar */}
                <div style={styles.progressBar}>
                  <div style={styles.progressFill}></div>
                </div>

                {/* Progress stages */}
                <div style={styles.progressStages}>
                  {progressStages.map((stage, index) => (
                    <div
                      key={index}
                      style={styles.progressStage}
                      onClick={() => updateProgress(index)}
                    >
                      <div
                        style={{
                          ...styles.stageCircle,
                          ...(index <= currentStage ? {
                            background: colors.primary,
                            borderColor: colors.primary,
                            color: colors.white
                          } : {})
                        }}
                        className={index <= currentStage ? "active" : ""}
                      >
                        {index <= currentStage ? <FaCheck size={12} /> : index + 1}
                      </div>
                      <div style={styles.stageLabel}>{stage}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedAppointment.status === "pending" && (
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="Provide a reason for rejection (optional)"
                style={styles.textArea}
              />
            )}

            <div className="modal-actions" style={{ display: "flex", gap: "1rem", marginTop: "1.5rem" }}>
              {selectedAppointment.status === "pending" && (
                <>
                  <button
                    style={{ ...styles.actionButton, ...styles.acceptButton }}
                    onClick={() => updateAppointmentStatus("accepted")}
                    disabled={isButtonDisabled}
                  >
                    <FaCheck /> Accept
                  </button>
                  <button
                    style={{ ...styles.actionButton, ...styles.rejectButton }}
                    onClick={() => updateAppointmentStatus("rejected", rejectionReason)}
                    disabled={isButtonDisabled}
                  >
                    <FaTimes /> Reject
                  </button>
                </>
              )}
              {selectedAppointment.status === "rejected" && (
                <button
                  style={{ 
                    ...styles.actionButton, 
                    background: `linear-gradient(135deg, ${colors.info} 0%, #0984e3 100%)`,
                    color: colors.white,
                    "&:hover:not(:disabled)": {
                      transform: "translateY(-2px)",
                      boxShadow: `0 4px 12px ${colors.info}`
                    }
                  }}
                  onClick={clearTimeslot}
                >
                  <FaClock /> Clear Timeslot
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Admin_AppointmentDashboard;