import React, { useState, useEffect } from "react";

const styles = {
  wrapper: {
    fontFamily: "Inter, sans-serif",
    padding: "24px",
    maxWidth: "960px",
    margin: "0 auto",
    color: "#374151",
    background: "linear-gradient(135deg, #fdd8d8, #cce5ff)",
    minHeight: "100vh",
  },
  heading: {
    textAlign: "center",
    fontSize: "2.4rem",
    fontWeight: 700,
    color: "#4338ca",
    marginBottom: "40px",
    textShadow: "1px 1px 2px rgba(0, 0, 0, 0.1)",
  },
  appointmentList: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "20px",
  },
  card: {
    background: "#fff",
    borderRadius: "12px",
    boxShadow: "0 6px 15px rgba(0, 0, 0, 0.1)",
    padding: "24px",
    transition: "transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out",
    cursor: "pointer",
    borderLeft: "8px solid #3f51b5",
    "&:hover": {
      transform: "scale(1.03)",
      boxShadow: "0 8px 20px rgba(0, 0, 0, 0.15)",
    },
  },
  cardTitle: {
    fontSize: "1.2rem",
    fontWeight: 600,
    color: "#4338ca",
    marginBottom: "10px",
  },
  cardInfo: {
    fontSize: "0.95rem",
    color: "#4b5563",
    marginBottom: "8px",
    lineHeight: 1.6,
    "& strong": {
      fontWeight: 700,
      color: "#1e3a8a",
    },
  },
  statusBadge: (status) => ({
    display: "inline-block",
    padding: "8px 12px",
    borderRadius: "8px",
    fontWeight: 500,
    fontSize: "0.85rem",
    color: "#fff",
    background:
      status === "Pending"
        ? "#f44336"
        : status === "In Progress"
        ? "#2196f3"
        : status === "Completed"
        ? "#4caf50"
        : status === "Cancelled"
        ? "#757575"
        : "#3f51b5",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
  }),
  modalOverlay: {
    position: "fixed",
    inset: 0,
    background: "rgba(67, 56, 164, 0.6)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 1000,
    animation: "fadeIn 0.3s ease",
  },
  modalBox: {
    width: "90%",
    maxWidth: "540px",
    background: "#fff",
    borderRadius: "16px",
    padding: "32px",
    boxShadow: "0 8px 20px rgba(0, 0, 0, 0.15)",
    position: "relative",
    animation: "slideUp 0.3s ease",
  },
  closeBtn: {
    position: "absolute",
    right: "20px",
    top: "16px",
    fontSize: "2rem",
    background: "none",
    border: "none",
    color: "#777",
    cursor: "pointer",
    opacity: 0.7,
    transition: "opacity 0.2s ease-in-out, color 0.2s ease-in-out",
    "&:hover": {
      opacity: 1,
      color: "#1e3a8a",
    },
  },
  modalHeading: {
    fontSize: "1.8rem",
    fontWeight: 600,
    color: "#4338ca",
    marginBottom: "25px",
    textAlign: "center",
    textShadow: "1px 1px 2px rgba(0, 0, 0, 0.05)",
  },
  modalInfo: {
    fontSize: "1rem",
    color: "#4b5563",
    marginBottom: "12px",
    lineHeight: 1.7,
    "& strong": {
      fontWeight: 700,
      color: "#1e3a8a",
    },
  },
  progressContainer: {
    background: "#f3f4f6",
    borderRadius: "12px",
    padding: "20px",
    marginTop: "30px",
    boxShadow: "inset 0 1px 3px rgba(0, 0, 0, 0.05)",
  },
  progressTitle: {
    fontWeight: 600,
    color: "#4338ca",
    marginBottom: "15px",
    fontSize: "1.1rem",
    textAlign: "center",
  },
  progressBarWrapper: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    position: "relative",
    height: "60px",
  },
  progressBarTrack: {
    position: "absolute",
    top: "50%",
    left: "0",
    right: "0",
    height: "6px",
    background: "#d1d5db",
    borderRadius: "3px",
    transform: "translateY(-50%)",
    zIndex: 0,
  },
  progressBarFill: (progress) => ({ // Style for the progress fill
    position: "absolute",
    top: "50%",
    left: "0",
    height: "6px",
    background: "#2196f3", // Blue color for the fill
    borderRadius: "3px",
    transform: "translateY(-50%)",
    zIndex: 1,
    width: `${(progress / 4) * 100}%`, // Calculate width based on progress (0-4)
    transition: "width 0.3s ease-in-out",
  }),
  progressStep: (active, completed) => ({
    flex: 1,
    textAlign: "center",
    position: "relative",
    zIndex: 2, // Ensure steps are above the fill
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    "&::before": {
      content: '""',
      position: "relative",
      width: "28px",
      height: "28px",
      borderRadius: "50%",
      background: completed ? "#f44336" : active ? "#2196f3" : "#fff",
      border: `3px solid ${active ? "#2196f3" : "#d1d5db"}`,
      boxShadow: "0 2px 5px rgba(0, 0, 0, 0.08)",
      transition: "background 0.3s ease-in-out, border-color 0.3s ease-in-out",
    },
    "&:hover::before": {
      transform: "scale(1.08)",
      boxShadow: "0 3px 7px rgba(0, 0, 0, 0.12)",
    },
    "& small": {
      marginTop: "6px",
      fontSize: "0.8rem",
      color: "#6b7280",
      textAlign: "center",
    },
  }),
};

/* keyframe helpers (inject once) */
const injectKeyframes = () => {
  if (document.getElementById("appt-keyframes")) return;
  const sheet = document.createElement("style");
  sheet.id = "appt-keyframes";
  sheet.innerHTML = `
    @keyframes fadeIn{from{opacity:0}to{opacity:1}}
    @keyframes slideUp{from{transform:translateY(15px);opacity:0}
                    to{transform:translateY(0);opacity:1}}
  `;
  document.head.appendChild(sheet);
};

const AppointmentProfileView = () => {
  const [appointments, setAppointments] = useState([]);
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    injectKeyframes();
    (async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch("http://localhost:5000/api/appointments", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!res.ok) throw new Error("fetch failed");
        const data = await res.json();
        setAppointments(data.map(appt => ({ ...appt, progress: appt.progress || 0 })));
      } catch (err) {
        console.error(err);
      }
    })();
  }, []);

  const progressStages = [
    "Handover",
    "Diagnosis",
    "Repair",
    "Testing",
    "Ready",
  ];

  return (
    <div style={styles.wrapper}>
      <h1 style={styles.heading}>My Appointments</h1>

      <div style={styles.appointmentList}>
        {appointments.length ? (
          appointments.map((a) => (
            <div
              key={a._id}
              style={styles.card}
              onClick={() => {
                setSelected(a);
                setShowModal(true);
              }}
            >
              <h2 style={styles.cardTitle}>{a.issueDescription}</h2>
              <p style={styles.cardInfo}>
                <strong>Date:</strong> {a.date}
              </p>
              <p style={styles.cardInfo}>
                <strong>Time:</strong> {a.timeSlot}
              </p>
              <p style={styles.cardInfo}>
                <strong>Status:</strong>{" "}
                <span style={styles.statusBadge(a.status)}>{a.status}</span>
              </p>
            </div>
          ))
        ) : (
          <p style={{ textAlign: "center", fontSize: "0.9rem", color: "#6b7280" }}>
            No appointments found.
          </p>
        )}
      </div>

      {/* modal */}
      {showModal && selected && (
        <div style={styles.modalOverlay} onClick={() => setShowModal(false)}>
          <div style={styles.modalBox} onClick={(e) => e.stopPropagation()}>
            <button style={styles.closeBtn} onClick={() => setShowModal(false)}>
              &times;
            </button>
            <h2 style={styles.modalHeading}>Appointment Details</h2>

            <p style={styles.modalInfo}>
              <strong>Name:</strong> {selected.name}
            </p>
            <p style={styles.modalInfo}>
              <strong>Email:</strong> {selected.email}
            </p>
            <p style={styles.modalInfo}>
              <strong>Phone:</strong> {selected.phone}
            </p>
            <p style={styles.modalInfo}>
              <strong>Address:</strong> {selected.address}
            </p>
            <p style={styles.modalInfo}>
              <strong>Device:</strong> {selected.deviceType}
            </p>
            <p style={styles.modalInfo}>
              <strong>Issue:</strong> {selected.issueDescription}
            </p>
            <p style={styles.modalInfo}>
              <strong>Date:</strong> {selected.date}
            </p>
            <p style={styles.modalInfo}>
              <strong>Time Slot:</strong> {selected.timeSlot}
            </p>
            <p style={styles.modalInfo}>
              <strong>Status:</strong>{" "}
              <span style={styles.statusBadge(selected.status)}>
                {selected.status}
              </span>
            </p>

            {/* Upgraded Progress Bar with Text Below */}
            <div style={styles.progressContainer}>
              <h3 style={styles.progressTitle}>Repair Progress</h3>
              <div style={styles.progressBarWrapper}>
                <div style={styles.progressBarTrack} />
                <div style={styles.progressBarFill(selected.progress)} /> {/* The progress fill */}
                {progressStages.map((stage, idx) => (
                  <div key={idx} style={styles.progressStep(idx <= selected.progress, idx < selected.progress)}>
                    <small>{stage}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AppointmentProfileView;