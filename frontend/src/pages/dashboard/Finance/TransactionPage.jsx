import { useEffect, useState, useRef } from "react";

const TransactionPage = () => {
    const [transactions, setTransactions] = useState([]);
    const [error, setError] = useState(null);
    const [formData, setFormData] = useState({ amount: "", type: "Expense", category: "", date: "", description: "" });
    const [editingTransaction, setEditingTransaction] = useState(null);
    const [selectedCategory, setSelectedCategory] = useState("All");
    const [selectedType, setSelectedType] = useState("All");
    const [reportData, setReportData] = useState([]);
    const [totalAmount, setTotalAmount] = useState(0); // Store the total amount (income - expenses)
    const reportRef = useRef();

    useEffect(() => {
        fetchTransactions();
    }, []);

    const fetchTransactions = async () => {
        try {
            const res = await fetch("http://localhost:5000/api/transactions/all");
            const data = await res.json();
            setTransactions(data);
        } catch (error) {
            setError("Error fetching transactions");
            console.error(error);
        }
    };

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const addTransaction = async (e) => {
        e.preventDefault();
        try {
            await fetch("http://localhost:5000/api/transactions/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            setFormData({ amount: "", type: "Expense", category: "", date: "", description: "" });
            fetchTransactions();
        } catch (error) {
            setError("Error adding transaction");
            console.error(error);
        }
    };

    const deleteTransaction = async (id) => {
        const transaction = transactions.find(txn => txn._id === id);

        if (transaction.category === "Invoice") {
            if (!window.confirm("This is an Invoice transaction. Deleting it will also remove the Invoice. Are you sure?")) {
                return;
            }
            // Delete the Invoice automatically here if needed
            try {
                await fetch(`http://localhost:5000/api/invoices/${id}`, { method: "DELETE" }); 
                console.log("Linked invoice deleted successfully!");
            } catch (error) {
                console.error("Failed to delete linked invoice:", error);
            }
        } else {
            if (!window.confirm("Are you sure you want to delete this transaction?")) {
                return;
            }
        }
        try {
            await fetch(`http://localhost:5000/api/transactions/${id}`, { method: "DELETE" });
            setTransactions(transactions.filter(transaction => transaction._id !== id));
        } catch (error) {
            setError("Error deleting transaction");
            console.error(error);
        }
    };

    const handleEditClick = (transaction) => {
        if (!window.confirm("Do you want to edit this transaction?")) return;
        setEditingTransaction(transaction._id);
        setFormData({
            amount: transaction.amount,
            type: transaction.type,
            category: transaction.category,
            date: transaction.date.split("T")[0],
            description: transaction.description,
        });
    };

    const updateTransaction = async (e) => {
        e.preventDefault();
        try {
            // Protect Invoice category
            const existingTransaction = transactions.find(txn => txn._id === editingTransaction);
            if (existingTransaction.category === "Invoice" && formData.category !== "Invoice") {
                alert("Category 'Invoice' cannot be changed!");
                return;
            }
            //protect sales category
            if (existingTransaction.category === "sales" && formData.category !== "sales") {
                alert("Category 'sales' cannot be changed!");
                return;
            }
            await fetch(`http://localhost:5000/api/transactions/${editingTransaction}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });

            // If Invoice related, update Invoice too
            if (existingTransaction.category === "Invoice") {
                try {
                    await fetch(`http://localhost:5000/api/invoices/${editingTransaction}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            amount: formData.amount,
                            date: formData.date,
                            description: formData.description
                        }),
                    });
                    console.log("Linked invoice updated successfully!");
                } catch (error) {
                    console.error("Failed to update linked invoice:", error);
                }
            }
            setEditingTransaction(null);
            setFormData({ amount: "", type: "Expense", category: "", date: "", description: "" });
            fetchTransactions();
        } catch (error) {
            setError("Error updating transaction");
            console.error(error);
        }
    };

    const generateReport = () => {
        let filtered = transactions;

        if (selectedCategory !== "All") {
            filtered = filtered.filter(txn => txn.category === selectedCategory);
        }
        if (selectedType !== "All") {
            filtered = filtered.filter(txn => txn.type === selectedType);
        }

        setReportData(filtered);

        // Calculate total amount (income - expenses)
        const incomeTotal = filtered.filter(txn => txn.type === "Income").reduce((sum, txn) => sum + Number(txn.amount), 0);
        const expenseTotal = filtered.filter(txn => txn.type === "Expense").reduce((sum, txn) => sum + Number(txn.amount), 0);
        const total = incomeTotal - expenseTotal;
        setTotalAmount(total);

    };

    // Calculate and display Current Balance when selectedCategory and selectedType are "All"
    const getCurrentBalance = () => {
        // Calculate the overall balance (income - expenses) even when filters are applied
        const incomeTotal = transactions.filter(txn => txn.type === "Income").reduce((sum, txn) => sum + Number(txn.amount), 0);
        const expenseTotal = transactions.filter(txn => txn.type === "Expense").reduce((sum, txn) => sum + Number(txn.amount), 0);
        const balance = (incomeTotal - expenseTotal).toFixed(2); // Ensure two decimal points
        
        // Check if the balance is negative and alert the user
        if (parseFloat(balance) < 0) {
            alert("Warning: Your curent balance is negative!");
        }
    
        return balance;
    };

    const handlePrint = () => {
        const printContents = reportRef.current.innerHTML;
        const originalContents = document.body.innerHTML;
        document.body.innerHTML = printContents;
        window.print();
        document.body.innerHTML = originalContents;
        window.location.reload();
    };

    const getTotalAmount = () => totalAmount.toFixed(2); // Return the calculated total amount with 2 decimal places

    return (
        <div style={styles.container}>
            <style>{`
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    color: #e0e0e0;
                }

                h1, h2, h3 {
                    color: #ffffff;
                }

                form input, form select {
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
                    transition: background-color 0.3s ease;
                }

                form button:hover {
                    background-color: #0056b3;
                }

                .report-section {
                    margin-top: 40px;
                    padding: 20px;
                    background-color: #1e1e1e;
                    border-radius: 12px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                }

                .report-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }

                .report-table th, .report-table td {
                    padding: 12px 15px;
                    text-align: left;
                    border-bottom: 1px solid #333;
                }

                .report-table th {
                    background-color: #007BFF;
                    color: white;
                }

                .report-table tr:nth-child(even) {
                    background-color: #2a2a2a;
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

                .generate-btn, .print-btn {
                    background-color: #28a745;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-right: 10px;
                    transition: background-color 0.3s ease;
                }

                .generate-btn:hover, .print-btn:hover {
                    background-color: #218838;
                }

                .button-container {
                    display: flex;
                    gap: 20px;
                    margin-bottom: 20px;
                }

                .total-amount {
                    font-size: 20px;
                    margin-top: 10px;
                    color: #ff6f61;
                }

                .current-balance {
                    background-color: #007BFF;
                    padding: 20px;
                    border-radius: 12px;
                    margin-bottom: 20px;
                    color: white;
                    font-size: 2rem;
                    font-weight: bold;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                }
            `}</style>

            <h1>Transactions of <b>Alpha IT Solutions</b></h1>
            {error && <p style={{ color: "red" }}>{error}</p>}

            {/* Display Current Balance when both filters are "All" */}
            <div className="current-balance">
                <h3>Current Balance: LKR {getCurrentBalance()}</h3>
            </div>

            <div className="total-amount">
                Total Amount (Income - Expenses): LKR {getTotalAmount()}
            </div>

            <form onSubmit={editingTransaction ? updateTransaction : addTransaction} style={styles.form}>
                <input type="number" name="amount" value={formData.amount} onChange={handleChange} placeholder="Amount" required />

                <select name="type" value={formData.type} onChange={handleChange} required>
                    <option value="Income">Income</option>
                    <option value="Expense">Expense</option>
                </select>

                <input type="text" name="category" value={formData.category} onChange={handleChange} placeholder="Category" required />
                <input type="date" name="date" value={formData.date} onChange={handleChange} required />
                <input type="text" name="description" value={formData.description} onChange={handleChange} placeholder="Description" required />

                <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
                    <button type="submit">{editingTransaction ? "Update Transaction" : "Add Transaction"}</button>
                    {editingTransaction && <button type="button" onClick={() => setEditingTransaction(null)}>Cancel</button>}
                </div>
            </form>

            {/* Report Section */}
            <div className="report-section" ref={reportRef}>
                <h2>Transaction Report</h2>

                <div style={{ marginBottom: "10px" }}>
                    <label>Filter by Category: </label>
                    <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)} style={{ marginRight: "10px" }}>
                        <option value="All">All</option>
                        {Array.from(new Set(transactions.map(txn => txn.category))).map(category => (
                            <option key={category} value={category}>{category}</option>
                        ))}
                    </select>

                    <label>Filter by Type: </label>
                    <select value={selectedType} onChange={(e) => setSelectedType(e.target.value)}>
                        <option value="All">All</option>
                        <option value="Income">Income</option>
                        <option value="Expense">Expense</option>
                    </select>
                </div>

                <div className="button-container">
                    <button className="generate-btn" onClick={generateReport}>Generate Report</button>
                    <button className="print-btn" onClick={handlePrint}>Print Report</button>
                </div>

                {reportData.length > 0 && (
                    <div style={{ marginTop: "20px" }}>
                        <h3>Category: {selectedCategory} | Type: {selectedType}</h3>
                        <table className="report-table">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Category</th>
                                    <th>Amount (LKR)</th>
                                    <th>Date</th>
                                    <th>Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                {reportData.map(txn => (
                                    <tr key={txn._id}>
                                        <td>{txn.type}</td>
                                        <td>{txn.category}</td>
                                        <td>LKR {txn.amount}</td>
                                        <td>{txn.date.split("T")[0]}</td>
                                        <td>{txn.description}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                        <h3 style={{ marginTop: "10px" }}>Total Amount: LKR {getTotalAmount()}</h3>
                    </div>
                )}
            </div>

            <ul style={styles.list}>
                {transactions.map(txn => (
                    <li key={txn._id} style={styles.listItem}>
                        <span>{txn.type} - {txn.category}: <br/>LKR {txn.amount} - {txn.date.split("T")[0]} - {txn.description}</span>
                        <div>
                            <button className="edit-btn" onClick={() => handleEditClick(txn)}>Edit</button>
                            <button className="delete-btn" onClick={() => deleteTransaction(txn._id)}>Delete</button>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

const styles = {
    container: {
        maxWidth: "900px",
        margin: "20px auto",
        padding: "20px",
        background: "#1a1a1a",
        borderRadius: "12px",
        boxShadow: "0 6px 15px rgba(0, 0, 0, 0.7)",
        textAlign: "center",
    },
    form: {
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        background: "#262626",
        padding: "20px",
        borderRadius: "10px",
    },
    list: {
        listStyleType: "none",
        padding: "0",
        marginTop: "30px",
    },
    listItem: {
        background: "#2a2a2a",
        padding: "12px",
        borderRadius: "8px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        margin: "8px 0",
        color: "white",
    },
};

export default TransactionPage;
