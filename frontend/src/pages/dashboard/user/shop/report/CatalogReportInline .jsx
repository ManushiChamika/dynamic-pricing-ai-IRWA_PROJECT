import React from 'react';
import { useAuth } from '../../../../../context/authContext'; 

const CatalogReportInline = () => {
  const { user } = useAuth();

  console.log("Logged-in user:", user);

  const handleGenerateReport = () => {
    if (!user || !user.email) {
      alert("User email is required to generate the report.");
      return;
    }
  
    window.open(`http://localhost:5000/api/reports/catalog-report?userEmail=${user.email}`, '_blank');
  };

  // Dark mode inline styles
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    marginTop: '50px',
    fontFamily: 'Arial, sans-serif',
    backgroundColor: '#121212',
    color: '#e0e0e0',
    minHeight: '100vh',
    padding: '20px',
  };

  const headingStyle = {
    marginBottom: '30px',
    fontSize: '24px',
  };

  const buttonStyle = {
    backgroundColor: '#1e88e5',
    color: '#fff',
    border: 'none',
    padding: '10px 20px',
    borderRadius: '4px',
    fontSize: '16px',
    cursor: 'pointer',
    transition: 'background-color 0.3s',
  };

  const buttonHoverStyle = {
    backgroundColor: '#1565c0',
  };

  return (
    <div style={containerStyle}>
      <h1 style={headingStyle}>Product Catalog Report</h1>
      <button
        style={buttonStyle}
        onMouseEnter={e => e.currentTarget.style.backgroundColor = buttonHoverStyle.backgroundColor}
        onMouseLeave={e => e.currentTarget.style.backgroundColor = buttonStyle.backgroundColor}
        onClick={handleGenerateReport}
      >
        Generate Report
      </button>
    </div>
  );
};

export default CatalogReportInline;
