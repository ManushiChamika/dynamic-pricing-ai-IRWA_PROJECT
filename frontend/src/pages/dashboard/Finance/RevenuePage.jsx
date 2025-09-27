import React, { useEffect, useState } from 'react';
import axios from 'axios';

const RevenuePage = () => {
  const [transactions, setTransactions] = useState([]);
  const [grossRevenue, setGrossRevenue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchRevenue = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/transactions/revenue');
        setTransactions(response.data);

        // Calculate Gross Revenue
        const total = response.data.reduce((acc, transaction) => acc + (transaction.amount || 0), 0);
        setGrossRevenue(total);

      } catch (error) {
        console.error('Error fetching revenue:', error);
      }
    };

    fetchRevenue();
  }, []);

  // Filter transactions based on search query
  const filteredTransactions = transactions.filter((tx) =>
    tx._id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    tx.amount.toString().includes(searchQuery)
  );

  // Function to generate CSV report
  const generateReport = () => {
    const headers = ['Transaction ID', 'Amount', 'Date'];
    const rows = filteredTransactions.map(tx => [
      tx._id,
      `LKR ${tx.amount.toFixed(2)}`,
      new Date(tx.date).toLocaleDateString()
    ]);
    
    let csvContent = 'data:text/csv;charset=utf-8,';
    csvContent += headers.join(',') + '\n';
    rows.forEach(row => {
      csvContent += row.join(',') + '\n';
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', 'revenue_report.csv');
    link.click();
  };

  return (
    <div style={styles.page}>
      <h1 style={styles.title}>Revenue Report</h1>

      <div style={styles.searchContainer}>
        <input
          type="text"
          placeholder="Search by ID or Amount"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={styles.searchInput}
        />
      </div>

      <div style={styles.grossRevenue}>
        Gross Revenue: ${grossRevenue.toFixed(2)}
      </div>

      <div>
        <ul>
          <li>Transaction Type: Income</li>
          <li>Category: Sales</li>
        </ul>
      </div>

      <br />
      <div style={styles.tableContainer}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Transaction ID</th>
              <th style={styles.th}>Amount</th>
              <th style={styles.th}>Date</th>
            </tr>
          </thead>
          <tbody>
            {filteredTransactions.map((tx) => (
              <tr key={tx._id}>
                <td style={styles.td}>{tx._id}</td>
                <td style={styles.td}>LKR {tx.amount.toFixed(2)}</td>
                <td style={styles.td}>{new Date(tx.date).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={styles.reportButtonContainer}>
        <button onClick={generateReport} style={styles.reportButton}>
          Generate Report
        </button>
      </div>
    </div>
  );
};

// Inline dark mode styles
const styles = {
  page: {
    backgroundColor: '#121212',
    color: '#e0e0e0',
    minHeight: '100vh',
    padding: '2rem',
    fontFamily: 'Arial, sans-serif',
  },
  title: {
    textAlign: 'center',
    marginBottom: '2rem',
    fontSize: '2rem',
  },
  grossRevenue: {
    backgroundColor: '#1f1f1f',
    padding: '1rem',
    marginBottom: '2rem',
    borderRadius: '8px',
    textAlign: 'center',
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#4caf50',
  },
  searchContainer: {
    marginBottom: '1rem',
    textAlign: 'center',
  },
  searchInput: {
    padding: '0.5rem',
    fontSize: '1rem',
    width: '80%',
    maxWidth: '400px',
    borderRadius: '4px',
    border: '1px solid #333',
    backgroundColor: '#1e1e1e',
    color: '#e0e0e0',
  },
  tableContainer: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    backgroundColor: '#1e1e1e',
  },
  th: {
    borderBottom: '1px solid #333',
    padding: '12px',
    textAlign: 'left',
  },
  td: {
    borderBottom: '1px solid #333',
    padding: '12px',
  },
  reportButtonContainer: {
    textAlign: 'center',
    marginTop: '2rem',
  },
  reportButton: {
    padding: '1rem 2rem',
    fontSize: '1rem',
    backgroundColor: '#4caf50',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
};

export default RevenuePage;
