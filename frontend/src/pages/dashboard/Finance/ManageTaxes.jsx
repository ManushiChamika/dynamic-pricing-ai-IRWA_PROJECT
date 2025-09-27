import { useState, useEffect } from "react";
import axios from "axios";

function ManageTaxes() {
  const [totalAmount, setTotalAmount] = useState('');
  const [taxAmount, setTaxAmount] = useState('');
  const [taxRate, setTaxRate] = useState('0.05');
  const [taxes, setTaxes] = useState([]);
  const [showTaxes, setShowTaxes] = useState(false);
  const [totalTaxAmount, setTotalTaxAmount] = useState(0);

  const fetchTaxes = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/taxes/all');
      if (response.data.success) {
        setTaxes(response.data.taxes);
        const total = response.data.taxes.reduce((sum, tax) => sum + tax.taxAmount, 0);
        setTotalTaxAmount(total);
      }
    } catch (error) {
      console.error("Error fetching taxes:", error);
    }
  };

  useEffect(() => {
    fetchTaxes();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:5000/api/taxes/create', { 
        totalAmount: Number(totalAmount), 
        taxAmount: Number(taxAmount), 
        taxRate: Number(taxRate) 
      });
      setTotalAmount('');
      setTaxAmount('');
      setTaxRate('0.05');
      fetchTaxes();
    } catch (error) {
      console.error("Error adding tax:", error);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      backgroundColor: "#121212",
      color: "#FFFFFF",
      padding: "30px",
      fontFamily: "Arial, sans-serif"
    }}>
      {/* Top Card showing total tax amount */}
      <div style={{
        background: "#1e1e1e",
        padding: "20px",
        borderRadius: "10px",
        marginBottom: "30px",
        textAlign: "center",
        boxShadow: "0px 4px 12px rgba(0,0,0,0.5)"
      }}>
        <h2 style={{ marginBottom: "10px", color: "#BB86FC" }}>Total Tax Amount</h2>
        <h1 style={{ fontSize: "36px", color: "#03DAC6" }}>LKR {totalTaxAmount.toFixed(2)}</h1>
      </div>

      {/* Two Column Layout */}
      <div style={{ display: "flex", gap: "30px" }}>
        {/* Left Column: Form */}
        <div style={{
          flex: 1,
          background: "#1e1e1e",
          padding: "20px",
          borderRadius: "10px",
          boxShadow: "0px 4px 12px rgba(0,0,0,0.5)"
        }}>
          <h2 style={{ marginBottom: "20px", color: "#BB86FC" }}>Add Tax</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: "15px" }}>
              <input 
                type="number" 
                placeholder="Total Amount (before tax)" 
                value={totalAmount} 
                onChange={(e) => setTotalAmount(e.target.value)}
                required 
                style={{
                  width: "100%",
                  padding: "10px",
                  borderRadius: "5px",
                  border: "1px solid #333",
                  backgroundColor: "#2c2c2c",
                  color: "#fff"
                }}
              />
            </div>
            <div style={{ marginBottom: "15px" }}>
              <input 
                type="number" 
                placeholder="Tax Amount" 
                value={taxAmount} 
                onChange={(e) => setTaxAmount(e.target.value)}
                required 
                style={{
                  width: "100%",
                  padding: "10px",
                  borderRadius: "5px",
                  border: "1px solid #333",
                  backgroundColor: "#2c2c2c",
                  color: "#fff"
                }}
              />
            </div>
            <div style={{ marginBottom: "15px" }}>
              <input 
                type="number" 
                step="0.01"
                placeholder="Tax Rate (Default 0.05)" 
                value={taxRate} 
                onChange={(e) => setTaxRate(e.target.value)}
                style={{
                  width: "100%",
                  padding: "10px",
                  borderRadius: "5px",
                  border: "1px solid #333",
                  backgroundColor: "#2c2c2c",
                  color: "#fff"
                }}
              />
            </div>
            <button type="submit" style={{
              width: "100%",
              padding: "12px",
              backgroundColor: "#BB86FC",
              color: "#121212",
              border: "none",
              borderRadius: "5px",
              fontWeight: "bold",
              cursor: "pointer"
            }}>
              Add Tax
            </button>
          </form>
        </div>

        {/* Right Column: Show Taxes */}
        <div style={{
          flex: 2,
          background: "#1e1e1e",
          padding: "20px",
          borderRadius: "10px",
          boxShadow: "0px 4px 12px rgba(0,0,0,0.5)"
        }}>
          <button 
            onClick={() => setShowTaxes(!showTaxes)} 
            style={{
              backgroundColor: "#03DAC6",
              color: "#121212",
              padding: "10px 20px",
              border: "none",
              borderRadius: "5px",
              marginBottom: "20px",
              cursor: "pointer",
              fontWeight: "bold"
            }}
          >
            {showTaxes ? "Hide Taxes" : "Show Taxes"}
          </button>

          {showTaxes && (
            <table style={{
              width: "100%",
              borderCollapse: "collapse",
              color: "#FFFFFF"
            }}>
              <thead>
                <tr style={{ backgroundColor: "#333" }}>
                  <th style={{ padding: "12px", border: "1px solid #555" }}>Order ID</th>
                  <th style={{ padding: "12px", border: "1px solid #555" }}>Total Amount</th>
                  <th style={{ padding: "12px", border: "1px solid #555" }}>Tax Amount</th>
                  <th style={{ padding: "12px", border: "1px solid #555" }}>Tax Rate</th>
                  <th style={{ padding: "12px", border: "1px solid #555" }}>Created At</th>
                </tr>
              </thead>
              <tbody>
                {taxes.map((tax) => (
                  <tr key={tax._id}>
                    <td style={{ padding: "10px", border: "1px solid #555" }}>
                      {tax.successOrderId || 'Not from Order'}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #555" }}>
                      LKR {tax.totalAmount.toFixed(2)}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #555" }}>
                      LKR {tax.taxAmount.toFixed(2)}
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #555" }}>
                      {(tax.taxRate * 100).toFixed(2)}%
                    </td>
                    <td style={{ padding: "10px", border: "1px solid #555" }}>
                      {new Date(tax.createdAt).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}

export default ManageTaxes;
