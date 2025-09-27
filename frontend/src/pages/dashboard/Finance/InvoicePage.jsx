import React, { useState, useEffect } from 'react';
import axios from 'axios';
import "../../../styles/FinanceManagement/invoicePage.css"

const InvoicePage = () => {
    const [invoices, setInvoices] = useState([]);
    const [selectedInvoice, setSelectedInvoice] = useState(null);
    const [customerName, setCustomerName] = useState('');
    const [items, setItems] = useState([{ name: '', price: 1, quantity: 1 }]);
    const [totalAmount, setTotalAmount] = useState(0);
    const [status, setStatus] = useState('Pending');
    const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
    const [filter, setFilter] = useState('All');
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchInvoices();
    }, []);

    const fetchInvoices = () => {
        axios.get('http://localhost:5000/api/invoices/all')
            .then(response => setInvoices(response.data))
            .catch(err => console.error('Error fetching invoices', err));
    };

    useEffect(() => {
        if (selectedInvoice) {
            axios.get(`http://localhost:5000/api/invoices/${selectedInvoice}`)
                .then(response => {
                    const invoice = response.data;
                    setCustomerName(invoice.customerName);
                    setItems(invoice.items.map(item => ({
                        ...item,
                        price: item.price || 1,
                        quantity: item.quantity || 1
                    })));
                    setTotalAmount(invoice.totalAmount);
                    setStatus(invoice.status);
                    setDate(invoice.date.split('T')[0]);
                })
                .catch(err => console.error('Error fetching invoice', err));
        }
    }, [selectedInvoice]);

    const handleItemChange = (index, field, value) => {
        const newItems = [...items];
        newItems[index][field] = value;
        setItems(newItems);
        updateTotalAmount(newItems);
    };

    const handleAddItem = () => {
        setItems([...items, { name: '', price: 1, quantity: 1 }]);
    };

    const handleRemoveItem = (index) => {
        const newItems = items.filter((_, i) => i !== index);
        setItems(newItems);
        updateTotalAmount(newItems);
    };

    const updateTotalAmount = (itemsList) => {
        const total = itemsList.reduce((sum, item) => sum + (item.price * item.quantity), 0);
        setTotalAmount(total);
    };

    const createTransaction = (invoice) => {
        const transactionData = {
            amount: invoice.totalAmount,
            type: 'Income',  // For Paid invoices
            category: 'Invoice', // Category for this transaction
            date: invoice.date, // Date from the invoice
            description: `Payment for invoice #${invoice._id} from ${invoice.customerName}` // Description
        };

        axios.post('http://localhost:5000/api/transactions/add', transactionData)
            .then(() => console.log('Transaction created successfully'))
            .catch(err => console.error('Error creating transaction', err));
    };

    const handleSubmit = (e) => {
        e.preventDefault();

        const hasInvalidItem = items.some(item => item.price <= 0 || item.quantity <= 0);
        if (hasInvalidItem) {
            alert('Each item must have a price and quantity greater than 0.');
            return;
        }

        const invoiceData = { customerName, items, totalAmount, status, date };

        if (selectedInvoice) {
            axios.put(`http://localhost:5000/api/invoices/${selectedInvoice}`, invoiceData)
                .then(response => {
                    alert('Invoice updated successfully!');
                    setInvoices(invoices.map(invoice => invoice._id === response.data._id ? response.data : invoice));

                    if (response.data.status === 'Paid') {
                        createTransaction(response.data); // Only create transaction if Paid
                    }

                    resetForm();
                })
                .catch(err => console.error('Error updating invoice', err));
        } else {
            axios.post('http://localhost:5000/api/invoices', invoiceData)
                .then(response => {
                    alert('Invoice created successfully!');
                    setInvoices([...invoices, response.data]);

                    if (response.data.status === 'Paid') {
                        createTransaction(response.data); // Only create transaction if Paid
                    }

                    resetForm();
                })
                .catch(err => console.error('Error creating invoice', err));
        }
    };

    const handleDeleteInvoice = (invoiceId) => {
        const invoiceToDelete = invoices.find(inv => inv._id === invoiceId);
        if (invoiceToDelete && window.confirm(`Are you sure you want to delete this invoice and its associated transaction?`)) {
            // Delete the transaction if it exists
            if (invoiceToDelete.status === 'Paid') {
                axios.delete(`http://localhost:5000/api/transactions/${invoiceId}`)
                    .then(() => {
                        console.log('Transaction deleted successfully');
                    })
                    .catch(err => console.error('Error deleting transaction', err));
            }

            // Delete the invoice
            axios.delete(`http://localhost:5000/api/invoices/${invoiceId}`)
                .then(() => {
                    alert('Invoice deleted successfully!');
                    setInvoices(invoices.filter(invoice => invoice._id !== invoiceId));
                })
                .catch(err => console.error('Error deleting invoice', err));
        }
    };

    const resetForm = () => {
        setCustomerName('');
        setItems([{ name: '', price: 1, quantity: 1 }]);
        setTotalAmount(0);
        setStatus('Pending');
        setDate(new Date().toISOString().split('T')[0]);
        setSelectedInvoice(null);
    };

    const handleCancelEdit = () => {
        if (window.confirm('Cancel editing? Changes will be lost.')) {
            window.location.reload();
        }
    };

    const filteredInvoices = invoices.filter(invoice => {
        if (filter === 'All') return true;
        return invoice.status === filter;
    }).filter(invoice =>
        invoice.customerName.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const totalEarnings = invoices.filter(inv => inv.status === 'Paid').reduce((sum, inv) => sum + inv.totalAmount, 0);
    const totalPending = invoices.filter(inv => inv.status === 'Pending').reduce((sum, inv) => sum + inv.totalAmount, 0);

    const generateReport = () => {
        const reportData = filteredInvoices.map(invoice => (
            `<tr>
                <td>${invoice.customerName}</td>
                <td>LKR ${invoice.totalAmount}</td>
                <td>${invoice.status}</td>
                <td>${invoice.date}</td>
                <td>
                    ${invoice.items.map(item => `${item.name} (Price: LKR ${item.price}, Qty: ${item.quantity})`).join('<br>')}
                </td>
            </tr>`
        )).join('');
    
        const reportHtml = `
            <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .report-table { width: 100%; border-collapse: collapse; }
                        .report-table th, .report-table td { border: 1px solid #000; padding: 8px; text-align: left; }
                        .report-table th { background-color: #f2f2f2; }
                        h2 { text-align: center; }
                    </style>
                </head>
                <body>
                    <h2>Invoice Report</h2>
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Customer Name</th>
                                <th>Total Amount</th>
                                <th>Status</th>
                                <th>Date</th>
                                <th>Items</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${reportData}
                        </tbody>
                    </table>
                    <br />
                    <button onclick="window.print()">Print Report</button>
                </body>
            </html>
        `;
    
        const printWindow = window.open('', '_blank');
        printWindow.document.write(reportHtml);
        printWindow.document.close();
    };
    

    return (
        <div className="invoice-management-container">
            {/* Report Section */}
            <div className="report-section">
                <h2>Invoice Report</h2>
                <p><strong>Total Earnings:</strong> LKR {totalEarnings}</p>
                <p><strong>Total Pending:</strong> LKR {totalPending}</p>
            </div>

            {/* Filter Buttons */}
            <div className="filter-buttons">
                <button onClick={() => setFilter('All')} className={filter === 'All' ? 'active' : ''}>All</button>
                <button onClick={() => setFilter('Pending')} className={filter === 'Pending' ? 'active' : ''}>Pending</button>
                <button onClick={() => setFilter('Paid')} className={filter === 'Paid' ? 'active' : ''}>Paid</button>
            </div>

            <div className="top-controls">
                {/* Search Bar */}
                <div className="search-bar">
                <input
                    type="text"
                    placeholder="Search by Customer Name"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                />
                </div>

                {/* Generate Report Button */}
                <div className="generate-report">
                    <button onClick={generateReport}>Generate Report</button>
                </div>
            </div>

            {/* Content Grid */}
            <div className="content-grid">
                {/* Left side - Form */}
                <div className="invoice-form">
                    <h2>{selectedInvoice ? 'Edit Invoice' : 'Create Invoice'}</h2>
                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Customer Name</label>
                            <input
                                type="text"
                                value={customerName}
                                onChange={(e) => setCustomerName(e.target.value)}
                                required
                            />
                        </div>

                        {items.map((item, index) => (
                            <div key={index} className="form-group">
                                <label>Item {index + 1}</label>
                                <label>Item Name</label>
                                <input
                                    type="text"
                                    placeholder="Item Name"
                                    value={item.name}
                                    onChange={(e) => handleItemChange(index, 'name', e.target.value)}
                                    required
                                />
                                <label>Item Price</label>
                                <input
                                    type="number"
                                    placeholder="Price"
                                    value={item.price}
                                    min="1"
                                    onChange={(e) => handleItemChange(index, 'price', Number(e.target.value))}
                                    required
                                />
                                <label>Item Quantity</label>
                                <input
                                    type="number"
                                    placeholder="Quantity"
                                    value={item.quantity}
                                    min="1"
                                    onChange={(e) => handleItemChange(index, 'quantity', Number(e.target.value))}
                                    required
                                />
                                <button type="button" className="remove-btn" onClick={() => handleRemoveItem(index)}>Remove</button>
                            </div>
                        ))}
                        <button type="button" className="add-btn" onClick={handleAddItem}>Add Item</button>

                        <div className="form-group">
                            <label>Total Amount: LKR {totalAmount}</label>
                        </div>

                        <div className="form-group">
                            <label>Status</label>
                            <select
                                value={status}
                                onChange={(e) => setStatus(e.target.value)}
                                required
                            >
                                <option value="Pending">Pending</option>
                                <option value="Paid">Paid</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Date</label>
                            <input
                                type="date"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                                required
                            />
                        </div>

                        <div className="button-group">
                            <button type="submit" className="submit-btn">{selectedInvoice ? 'Update' : 'Create'} Invoice</button>
                            {selectedInvoice && (
                                <button type="button" className="cancel-btn" onClick={handleCancelEdit}>Cancel</button>
                            )}
                        </div>
                    </form>
                </div>

                {/* Right side - Invoice List */}
                <div className="invoice-list">
                    <h2>Invoices</h2>
                    {filteredInvoices.length > 0 ? (
                        filteredInvoices.map(invoice => (
                            <div key={invoice._id} className="invoice-item">
                                <h3>{invoice.customerName}</h3>
                                <p><strong>Total:</strong> LKR {invoice.totalAmount}</p>
                                <p><strong>Status:</strong> {invoice.status}</p>
                                <div className="item-details">
                                    {invoice.items.map((item, idx) => (
                                        <div key={idx}>
                                            <span>{item.name}</span> - 
                                            <span>Price: LKR {item.price}</span> - 
                                            <span>Qty: {item.quantity}</span>
                                        </div>
                                    ))}
                                </div>
                                <div className="button-group">
                                    <button onClick={() => setSelectedInvoice(invoice._id)}>Edit</button>
                                    <button className="delete-btn" onClick={() => handleDeleteInvoice(invoice._id)}>Delete</button>
                                </div>
                            </div>
                        ))
                    ) : (
                        <p>No invoices to display.</p>
                    )}
                </div>
            </div>
        </div>
    );
};

export default InvoicePage;
