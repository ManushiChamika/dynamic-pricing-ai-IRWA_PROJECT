import { useEffect, useState, useRef } from "react";

const PettyCashPage = () => {
    const [pettyCash, setPettyCash] = useState([]);
    const [error, setError] = useState(null);
    const [formData, setFormData] = useState({ amount: "", date: "", description: "" });
    const [editingCashId, setEditingCashId] = useState(null);
    const [searchQuery, setSearchQuery] = useState(""); // New State for Search
    const [monthlyTotal, setMonthlyTotal] = useState(0);
    const reportRef = useRef();

    useEffect(() => {
        fetchPettyCash();
    }, []);

    useEffect(() => {
        calculateMonthlyTotal();
    }, [pettyCash]);

    const fetchPettyCash = async () => {
        try {
            const res = await fetch("http://localhost:5000/api/pettycash/all");
            const data = await res.json();
            setPettyCash(data);
        } catch (error) {
            setError("Error fetching petty cash records");
            console.error(error);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const addPettyCash = async (e) => {
        e.preventDefault();
        try {
            await fetch("http://localhost:5000/api/pettycash/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            setFormData({ amount: "", date: "", description: "" });
            fetchPettyCash();
        } catch (error) {
            setError("Error adding petty cash");
            console.error(error);
        }
    };

    const deletePettyCash = async (id) => {
        if (!window.confirm("Are you sure you want to delete this petty cash record?")) return;
        try {
            await fetch(`http://localhost:5000/api/pettycash/${id}`, { method: "DELETE" });
            setPettyCash(pettyCash.filter(cash => cash._id !== id));
        } catch (error) {
            setError("Error deleting petty cash");
            console.error(error);
        }
    };

    const handleEditClick = (cash) => {
        if (!window.confirm("Do you want to edit this petty cash record?")) return;
        setEditingCashId(cash._id);
        setFormData({
            amount: cash.amount,
            date: cash.date.split("T")[0],
            description: cash.description,
        });
    };

    const updatePettyCash = async (e) => {
        e.preventDefault();
        try {
            await fetch(`http://localhost:5000/api/pettycash/${editingCashId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            setEditingCashId(null);
            setFormData({ amount: "", date: "", description: "" });
            fetchPettyCash();
        } catch (error) {
            setError("Error updating petty cash");
            console.error(error);
        }
    };

    const calculateMonthlyTotal = () => {
        const now = new Date();
        const currentMonth = now.getMonth();
        const currentYear = now.getFullYear();
        const total = pettyCash
            .filter(cash => {
                const cashDate = new Date(cash.date);
                return cashDate.getMonth() === currentMonth && cashDate.getFullYear() === currentYear;
            })
            .reduce((sum, cash) => sum + Number(cash.amount), 0);

        setMonthlyTotal(total);
    };

    const handlePrint = () => {
        const pettyCashRecords = pettyCash
            .filter(cash => 
                cash.description.toLowerCase().includes(searchQuery.toLowerCase()) || 
                cash.date.includes(searchQuery)
            );
    
        const tableRows = pettyCashRecords.map(cash => `
            <tr>
                <td style="border: 1px solid #333; padding: 8px;">${cash.date}</td>
                <td style="border: 1px solid #333; padding: 8px;">${cash.description}</td>
                <td style="border: 1px solid #333; padding: 8px;">${cash.amount}</td>
            </tr>
        `).join('');
    
        const printContents = `
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="text-align: center;">
                    <img src="/assets/AlphaITSolutionsLogo.jpg" alt="Company Logo" style="max-width: 200px; height: auto; margin-bottom: 20px;" />
                </div>
                <h2 style="text-align: center;">Petty Cash Report</h2>
                <p style="text-align: center;">Month: ${new Date().toLocaleString('default', { month: 'long', year: 'numeric' })}</p>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <thead>
                        <tr>
                            <th style="border: 1px solid #333; padding: 8px;">Date</th>
                            <th style="border: 1px solid #333; padding: 8px;">Description</th>
                            <th style="border: 1px solid #333; padding: 8px;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${tableRows}
                    </tbody>
                </table>
                <h3 style="margin-top: 30px; text-align: right;">Total: Rs. ${monthlyTotal.toFixed(2)}</h3>
            </div>
        `;
    
        const originalContents = document.body.innerHTML;
        document.body.innerHTML = printContents;
        window.print();
        document.body.innerHTML = originalContents;
        window.location.reload();
    };    
    
    return (
        <div style={styles.container}>
            <style>{`
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #e0e0e0;
                    background-color:rgb(0, 0, 0);
                }

                h1, h2 {
                    color: #ffffff;
                }

                form input {
                    padding: 10px;
                    margin: 8px 0;
                    border: 1px solid #333;
                    border-radius: 8px;
                    width: 100%;
                    box-sizing: border-box;
                    background-color: #1f1f1f;
                    color: #e0e0e0;
                }

                form button {
                    background-color: #007BFF;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-top: 10px;
                    transition: background-color 0.3s ease;
                }

                form button:hover {
                    background-color: #0056b3;
                }

                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }

                th, td {
                    color: black;
                    padding: 12px;
                    border-bottom: 1px solid #333;
                }

                th {
                    background-color: #007BFF;
                }

                tr:nth-child(even) {
                    background-color:rgba(192, 158, 158, 0.35);
                }

                .edit-btn, .delete-btn {
                    margin-left: 10px;
                    padding: 6px 12px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                }

                .edit-btn {
                    background-color: #f39c12;
                    color: white;
                }

                .edit-btn:hover {
                    background-color: #d68910;
                }

                .delete-btn {
                    background-color: #e74c3c;
                    color: white;
                }

                .delete-btn:hover {
                    background-color: #c0392b;
                }

                .print-btn {
                    background-color: #28a745;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-top: 20px;
                    transition: background-color 0.3s ease;
                }

                .print-btn:hover {
                    background-color: #218838;
                }

                .monthly-total {
                    background-color: #28a745;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    color: white;
                    font-size: 1.8rem;
                    font-weight: bold;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                }
            `}</style>

            <h1 style={styles.header}>
              <span style={styles.gradientText}>Alpha IT Solutions</span> 
            </h1>
            <p style={styles.header}>Petty Cash Management</p>

            {error && <p style={{ color: "red" }}>{error}</p>}

            {/* Current Month Total */}
            <div className="monthly-total">
                Total Petty Cash for {new Date().toLocaleString('default', { month: 'long' })}: LKR {monthlyTotal.toFixed(2)}
            </div>

            {/* Petty Cash Form */}
            <form onSubmit={editingCashId ? updatePettyCash : addPettyCash} style={styles.form}>
                <input type="number" name="amount" value={formData.amount} onChange={handleChange} placeholder="Amount" required />
                <input type="date" name="date" value={formData.date} onChange={handleChange} required />
                <input type="text" name="description" value={formData.description} onChange={handleChange} placeholder="Description" required />
                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button type="submit">{editingCashId ? "Update Record" : "Add Petty Cash"}</button>
                    {editingCashId && <button type="button" onClick={() => setEditingCashId(null)}>Cancel</button>}
                </div>
            </form>

            <div style={{ marginTop: "20px", marginBottom: "20px" }}>
            <input
                type="text"
                placeholder="Search by description or date..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                    width: "100%",
                    padding: "10px",
                    borderRadius: "8px",
                    border: "1px solid #333",
                    backgroundColor: "#1f1f1f",
                    color: "#e0e0e0",
                }}
            />
            </div>

            {/* Petty Cash Report */}
            <div ref={reportRef}>
                <h2>Petty Cash Records</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Amount (LKR)</th>
                            <th>Date</th>
                            <th>Description</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                    {pettyCash
                        .filter(cash => 
                            cash.description.toLowerCase().includes(searchQuery.toLowerCase()) || 
                            cash.date.includes(searchQuery)
                        )
                        .map(cash => (
                            <tr key={cash._id}>
                                <td>LKR {cash.amount}</td>
                                <td>{cash.date.split("T")[0]}</td>
                                <td>{cash.description}</td>
                                <td>
                                    <button className="edit-btn" onClick={() => handleEditClick(cash)}>Edit</button>
                                    <button className="delete-btn" onClick={() => deletePettyCash(cash._id)}>Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                <button className="print-btn" onClick={handlePrint}>Print Records</button>
            </div>
        </div>
    );
};

const styles = {
    container: {
        padding: "20px",
        maxWidth: "1200px",
        margin: "auto",
    },
    header: {
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        color: "#000000",
        fontSize: "2rem",
        fontWeight: "bold",
        textAlign: "center",
        marginBottom: "20px",
    },
    gradientText: {
        background: "linear-gradient(to right,rgb(12, 61, 112),rgb(121, 22, 11))", 
        color: "transparent",  
        WebkitBackgroundClip: "text",
        backgroundClip: "text",  
    },
};

export default PettyCashPage;
