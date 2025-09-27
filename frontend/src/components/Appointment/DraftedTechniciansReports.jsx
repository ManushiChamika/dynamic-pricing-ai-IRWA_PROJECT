import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  motion,
  AnimatePresence,
  useMotionValue,
  useTransform,
} from "framer-motion";
import {
  ArrowLeft,
  FileText,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  BookText,
} from "lucide-react";

const DraftedTechniciansReports = () => {
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState(null);

  /* ---------- sample data ---------- */
  const reports = [
    {
      id: 1,
      issue: "Computer running very slow",
      resolution: `• Restart computer to clear temp files
• Uninstall unused software
• Run disk‑cleanup & defrag
• Disable heavy startup tasks
• Upgrade RAM or switch to SSD`,
    },
    {
      id: 2,
      issue: "Wi‑Fi keeps dropping",
      resolution: `• Power‑cycle router & modem
• Move closer to access‑point
• Remove microwave / phone interference
• Update Wi‑Fi drivers
• Reset network stack`,
    },
    {
      id: 3,
      issue: "Laptop overheating & shutting down",
      resolution: `• Clean vents with compressed air
• Place on hard surface for airflow
• Use cooling pad
• Check fan RPM in BIOS
• Re‑paste CPU / GPU if needed`,
    },
    {
      id: 4,
      issue: "Printer not printing",
      resolution: `• Verify power & cable/Wi‑Fi
• Load paper & ink / toner
• Restart printer and PC
• Re‑install printer driver
• Clear stuck print queue`,
    },
    {
      id: 5,
      issue: "Screen flickering or odd colors",
      resolution: `• Reseat monitor cable
• Update GPU drivers
• Change refresh rate
• Test on another monitor
• Replace panel if faulty`,
    },
  ];

  /* ---------- theme ---------- */
  const blue = "#0af";
  const red = "#ff2860";
  const neon = (c) => `0 0 8px ${c}, 0 0 18px ${c}`;
  const glass = "blur(14px) saturate(160%)";

  /* ---------- framer variants ---------- */
  const listVariants = { hidden: { opacity: 0 }, show: { opacity: 1 } };
  const cardVariants = {
    hidden: { opacity: 0, y: 50 },
    show: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: [0.17, 0.67, 0.83, 0.67] },
    },
  };
  const detailVar = {
    open: { height: "auto", opacity: 1, transition: { duration: 0.35 } },
    closed: { height: 0, opacity: 0, transition: { duration: 0.25 } },
  };

  /* ---------- tilt helper ---------- */
  const TiltCard = ({ children, onClick, active }) => {
    const x = useMotionValue(0);
    const y = useMotionValue(0);
    const rX = useTransform(y, [-80, 80], [12, -12]);
    const rY = useTransform(x, [-200, 200], [-12, 12]);

    return (
      <motion.div
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          x.set(e.clientX - rect.left - rect.width / 2);
          y.set(e.clientY - rect.top - rect.height / 2);
        }}
        onMouseLeave={() => {
          x.set(0);
          y.set(0);
        }}
        style={{ perspective: 1000, position: "relative" }}
        onClick={onClick}
      >
        {/* halo */}
        {active && (
          <motion.div
            layoutId="halo"
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 0.55, scale: 1.05 }}
            transition={{ type: "spring", stiffness: 60, damping: 15 }}
            style={{
              position: "absolute",
              inset: -8,
              borderRadius: 28,
              background: `radial-gradient(circle at 50% 50%, ${blue}55, ${red}33 60%, transparent 75%)`,
              filter: "blur(22px)",
            }}
          />
        )}

        <motion.div
          style={{
            rotateX: rX,
            rotateY: rY,
            transformStyle: "preserve-3d",
            background: "rgba(255,255,255,0.12)",
            backdropFilter: glass,
            borderRadius: 24,
            padding: "28px 32px",
            boxShadow:
              "0 15px 40px rgba(0,0,0,0.35), inset 0 0 1px rgba(255,255,255,0.5)",
            color: "#e4eaf5",
            position: "relative",
            zIndex: 1,
          }}
        >
          {children}
        </motion.div>
      </motion.div>
    );
  };

  /* ---------- render ---------- */
  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "60px clamp(16px,6vw,100px)",
        fontFamily: "Poppins, sans-serif",
        background:
          "radial-gradient(circle at top right, #001233 0%, #000a1f 60%, #000 100%)",
      }}
    >
      {/* header */}
      <motion.button
        whileHover={{ x: -4 }}
        onClick={() => navigate(-1)}
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "transparent",
          border: "none",
          color: blue,
          fontSize: 18,
          fontWeight: 600,
          marginBottom: 48,
          textShadow: neon(blue),
          cursor: "pointer",
        }}
      >
        <ArrowLeft size={22} />
        Back
      </motion.button>

      <h1
        style={{
          fontSize: 46,
          margin: 0,
          marginBottom: 10,
          fontWeight: 700,
          color: "#fff",
          textShadow: neon(red),
        }}
      >
        Service Logs
      </h1>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          fontSize: 15,
          letterSpacing: 1,
          textTransform: "uppercase",
          color: "#9ca3af",
          marginBottom: 60,
        }}
      >
        <ClipboardList size={20} color={red} />
        Repair Insights
      </div>

      {/* list */}
      <motion.div
        variants={listVariants}
        initial="hidden"
        animate="show"
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 44,
          maxWidth: 900,
          width: "100%",
          margin: "0 auto",
        }}
      >
        <AnimatePresence>
          {reports.map((r) => {
            const active = expanded === r.id;
            return (
              <motion.div
                key={r.id}
                variants={cardVariants}
                initial="hidden"
                animate="show"
                exit={{ opacity: 0, y: 50 }}
              >
                <TiltCard
                  active={active}
                  onClick={() => setExpanded(active ? null : r.id)}
                >
                  {/* summary */}
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: 20,
                    }}
                  >
                    <div
                      style={{ display: "flex", alignItems: "center", gap: 16 }}
                    >
                      <FileText size={24} color={blue} />
                      <span style={{ fontSize: 20, fontWeight: 500 }}>
                        {r.issue}
                      </span>
                    </div>
                    {active ? (
                      <ChevronUp size={26} color={red} />
                    ) : (
                      <ChevronDown size={26} color={red} />
                    )}
                  </div>

                  {/* details */}
                  <AnimatePresence initial={false}>
                    {active && (
                      <motion.div
                        key="body"
                        variants={detailVar}
                        initial="closed"
                        animate="open"
                        exit="closed"
                        style={{ overflow: "hidden" }}
                      >
                        <div
                          style={{
                            marginTop: 26,
                            lineHeight: 1.6,
                            fontSize: 17,
                            color: "#cbd5e1",
                            whiteSpace: "pre-line",
                          }}
                        >
                          <span
                            style={{
                              display: "flex",
                              alignItems: "center",
                              gap: 8,
                              marginBottom: 12,
                              color: blue,
                              fontWeight: 600,
                              textShadow: neon(blue),
                              fontSize: 18,
                            }}
                          >
                            <BookText size={20} />
                            Fix Steps
                          </span>
                          {r.resolution}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </TiltCard>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </motion.div>
    </div>
  );
};

export default DraftedTechniciansReports;
