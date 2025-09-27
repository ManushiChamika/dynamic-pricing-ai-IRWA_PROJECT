import React, { useEffect, useState } from "react";
import axios from "axios";
import { jsPDF } from "jspdf";
import 'jspdf-autotable';

function InquiryManage() {
    const [inquiries, setInquiries] = useState([]);
    const [categorizedInquiries, setCategorizedInquiries] = useState({
        General: [],
        ProductAvailability: [],
        Support: [],
    });
    const [loading, setLoading] = useState(false);
    const [faqForm, setFaqForm] = useState({ id: null, answer: "", userApproval: false });
    const [message, setMessage] = useState({ type: "", text: "" });
    const [searchTerm, setSearchTerm] = useState("");
    const [searchResults, setSearchResults] = useState([]);

    useEffect(() => {
        fetchInquiries();
    }, []);

    useEffect(() => {
        if (searchTerm.trim() === "") {
            setSearchResults([]);
        } else {
            const results = [];
            Object.values(categorizedInquiries).forEach(category => {
                category.forEach(inquiry => {
                    if (inquiry.fullName.toLowerCase().includes(searchTerm.toLowerCase())) {
                        results.push(inquiry);
                    }
                });
            });
            setSearchResults(results);
        }
    }, [searchTerm, categorizedInquiries]);

    const fetchInquiries = async () => {
        try {
            const token = localStorage.getItem("token");
            const { data } = await axios.get("http://localhost:5000/api/inquiries/all-inquiries", {
                headers: { Authorization: `Bearer ${token}` }
            });

            setInquiries(data.inquiries);
            setCategorizedInquiries(data.categorizedInquiries);
        } catch (error) {
            setMessage({ type: "error", text: "Failed to fetch inquiries." });
            console.error("Fetch error:", error.response?.data || error.message);
        }
    };

    const handleResolveInquiry = async (id) => {
        try {
            setLoading(true);
            const token = localStorage.getItem("token");
            const response = await axios.put(
                `http://localhost:5000/api/inquiries/resolve/${id}`,
                { status: "Resolved" },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            console.log("Resolve Inquiry Response:", response.data);

            setCategorizedInquiries(prev => {
                const updated = {...prev};
                for (const category in updated) {
                    updated[category] = updated[category].map(inquiry => 
                        inquiry._id === id ? { ...inquiry, status: "Resolved", resolvedAt: new Date() } : inquiry
                    );
                }
                return updated;
            });

            setMessage({ type: "success", text: "Inquiry resolved successfully." });
            
        } catch (error) {
            setMessage({ type: "error", text: "Failed to resolve inquiry." });
            console.error("Resolve error:", error.response?.data || error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAddToFAQ = async (id) => {
        if (!faqForm.answer.trim()) {
            setMessage({ type: "error", text: "Please enter an answer before submitting." });
            return;
        }
    
        try {
            setLoading(true);
            const token = localStorage.getItem("token");
    
            const response = await axios.post(
                `http://localhost:5000/api/inquiries/add-to-faq/${id}`,
                { userApproval: true, answer: faqForm.answer },
                { headers: { Authorization: `Bearer ${token}` } }
            );
    
            console.log("API Response:", response.data);
    
            if (response.status === 201) {
                setMessage({ type: "success", text: "Inquiry added to FAQ successfully." });
                setFaqForm({ id: null, answer: "" });
                fetchInquiries();
            } else {
                setMessage({ type: "error", text: response.data.message || "Failed to add inquiry to FAQ." });
            }
        } catch (error) {
            setMessage({ type: "error", text: error.response?.data?.message || "Failed to add inquiry to FAQ." });
            console.error("API Error:", error.response?.data || error.message);
        } finally {
            setLoading(false);
        }
    };    

    const handleDeleteInquiry = async (id) => {
        try {
            setLoading(true);
            const token = localStorage.getItem("token");
            const response = await axios.delete(`http://localhost:5000/api/inquiries/delete-resolved/${id}`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setCategorizedInquiries(prev => {
                const updated = {...prev};
                for (const category in updated) {
                    updated[category] = updated[category].filter(inquiry => inquiry._id !== id);
                }
                return updated;
            });

            setMessage({ type: "success", text: response.data.message });

        } catch (error) {
            setMessage({ type: "error", text: error.response?.data?.message || "Failed to delete inquiry." });
            console.error("Delete Inquiry Error:", error);
        } finally {
            setLoading(false);
        }
    };

    const generateSearchResultsReport = () => {
        const doc = new jsPDF();
        
        const logoUrl = `${window.location.origin}/Logo.jpg`;
        
        new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = "Anonymous";
            img.onload = () => {
                const logoWidth = 35;
                const logoHeight = logoWidth * (img.height / img.width);
                doc.addImage(img, "JPEG", 15, 15, logoWidth, logoHeight);
                resolve();
            };
            img.src = logoUrl;
        }).then(() => {
            // Colors
            const primaryColor = "#2c3e50";
            const secondaryColor = "#7f8c8d";
            const accentColor = "#e74c3c";
            const darkColor = "#1F2937";
            const lightColor = "#F9FAFB";
            
            // Set default font
            doc.setFont("helvetica");
            
            // Company info (right-aligned)
            doc.setFontSize(10);
            doc.setTextColor(secondaryColor);
            doc.text("Alpha IT Solutions", 180, 20, { align: "right" });
            doc.text("26/C/3 Biyagama Road, Talwatta", 180, 25, { align: "right" });
            doc.text("Gonawala, Kelaniya 11600", 180, 30, { align: "right" });
            doc.text("Tel: 077 625 2822", 180, 35, { align: "right" });
            
            // Document title (centered below logo)
            doc.setFontSize(16);
            doc.setTextColor(primaryColor);
            doc.setFont(undefined, "bold");
            doc.text("SEARCH RESULTS REPORT", 105, 60, { align: "center" });
            
            // Search criteria
            let yPos = 75;
            doc.setFontSize(12);
            doc.setTextColor(secondaryColor);
            doc.text(`Search Criteria: "${searchTerm}"`, 15, yPos);
            doc.text(`Total Results: ${searchResults.length}`, 15, yPos + 7);
            yPos += 20;
            
            // Table header
            const headers = [
                { title: "Full Name", dataKey: "fullName" },
                { title: "Email", dataKey: "email" },
                { title: "Contact", dataKey: "contactNumber" },
                { title: "Type", dataKey: "inquiryType" },
                { title: "Status", dataKey: "status" }
            ];
            
            // Prepare data for the table
            const tableData = searchResults.map(inquiry => ({
                fullName: inquiry.fullName,
                email: inquiry.email,
                contactNumber: inquiry.contactNumber,
                inquiryType: inquiry.inquiryType,
                status: inquiry.status
            }));
            
            // Add the table
            doc.autoTable({
                startY: yPos,
                head: [headers.map(h => h.title)],
                body: tableData.map(row => headers.map(h => row[h.dataKey])),
                margin: { left: 15 },
                headStyles: {
                    fillColor: [41, 128, 185],
                    textColor: 255,
                    fontStyle: 'bold'
                },
                alternateRowStyles: {
                    fillColor: [245, 245, 245]
                },
                styles: {
                    cellPadding: 3,
                    fontSize: 9,
                    valign: 'middle'
                },
                columnStyles: {
                    0: { cellWidth: 30 },
                    1: { cellWidth: 40 },
                    2: { cellWidth: 25 },
                    3: { cellWidth: 30 },
                    4: { cellWidth: 25 }
                }
            });
            
            // Get the final Y position after the table
            yPos = doc.lastAutoTable.finalY + 10;
            
            // Summary section
            const resolvedCount = searchResults.filter(i => i.status === "Resolved").length;
            const pendingCount = searchResults.length - resolvedCount;
            
            doc.setFontSize(12);
            doc.setTextColor(primaryColor);
            doc.text("Summary Statistics:", 15, yPos);
            yPos += 7;
            
            doc.setFontSize(10);
            doc.setTextColor(darkColor);
            doc.text(`- Total Inquiries: ${searchResults.length}`, 20, yPos);
            yPos += 6;
            doc.text(`- Resolved: ${resolvedCount}`, 20, yPos);
            yPos += 6;
            doc.text(`- Pending: ${pendingCount}`, 20, yPos);
            yPos += 15;
            
            // Footer
            doc.setFontSize(8);
            doc.setTextColor(secondaryColor);
            doc.text("Alpha IT Solutions - Inquiry Management System", 
                    105, yPos, { align: "center" });
            yPos += 5;
            doc.text(`Report generated on: ${new Date().toLocaleDateString()}`, 
                    105, yPos, { align: "center" });
            
            // Page border
            doc.setDrawColor(lightColor);
            doc.setLineWidth(0.5);
            doc.rect(5, 5, 200, 287);
            
            // Save the PDF
            doc.save(`Search_Results_Report_${new Date().toISOString().slice(0,10)}.pdf`);
        }).catch((error) => {
            console.error("Error generating PDF:", error);
            setMessage({ type: "error", text: "Failed to generate PDF. Please try again." });
        });
    };

    return (
        <div className="p-8 bg-gray-50 min-h-screen">
            <MessageDisplay message={message} />
            <h3 className="text-4xl font-extrabold mb-6 text-gray-800 uppercase tracking-wide text-center relative">
                <span className="bg-gradient-to-r from-blue-500 to-purple-500 text-transparent bg-clip-text">
                    🛠️ Inquiry Management
                </span>
            </h3>

            {/* Search Bar */}
            <div className="mb-8 p-6 bg-white shadow-lg rounded-2xl border border-gray-200">
                <div className="flex flex-col md:flex-row gap-4 items-center">
                    <input
                        type="text"
                        placeholder="Search by full name..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="flex-grow p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                    {searchTerm && (
                        <>
                            <button 
                                onClick={() => setSearchTerm("")}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-all"
                            >
                                Clear
                            </button>
                            {searchResults.length > 0 && (
                                <button
                                    onClick={generateSearchResultsReport}
                                    className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-all"
                                >
                                    Generate All Results Report
                                </button>
                            )}
                        </>
                    )}
                </div>

                {/* Search Results */}
                {searchResults.length > 0 && (
                    <div className="mt-6">
                        <div className="flex justify-between items-center mb-4">
                            <h4 className="text-xl font-semibold text-gray-700">
                                Search Results ({searchResults.length})
                            </h4>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full border-collapse">
                                <thead>
                                    <tr className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-left">
                                        <th className="border px-6 py-3">Full Name</th>
                                        <th className="border px-6 py-3">Email</th>
                                        <th className="border px-6 py-3">Inquiry Type</th>
                                        <th className="border px-6 py-3">Status</th>
                                        <th className="border px-6 py-3">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {searchResults.map((inquiry) => (
                                        <tr key={inquiry._id} className="border hover:bg-gray-100 transition-all">
                                            <td className="border px-6 py-4">{inquiry.fullName}</td>
                                            <td className="border px-6 py-4">{inquiry.email}</td>
                                            <td className="border px-6 py-4">{inquiry.inquiryType}</td>
                                            <td className="border px-6 py-4">
                                                {inquiry.status === "Resolved" ? (
                                                    <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
                                                        Resolved
                                                    </span>
                                                ) : (
                                                    <span className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-sm font-medium">
                                                        Pending
                                                    </span>
                                                )}
                                            </td>
                                            <td className="border px-6 py-4">
                                                <button
                                                    onClick={() => generateInquiryReport(inquiry)}
                                                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all mr-2"
                                                >
                                                    Single Report
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>

            {/* Categorized Inquiries */}
            {Object.keys(categorizedInquiries).map((category) => (
                <div key={category} className="mb-8 p-6 bg-white shadow-lg rounded-2xl border border-gray-200">
                    <h3 className="text-2xl font-semibold mb-4 text-gray-700 border-b pb-2">
                        {category} Inquiries 📩
                    </h3>

                    <div className="overflow-x-auto">
                        <table className="w-full border-collapse">
                            <thead>
                                <tr className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white text-left">
                                    <th className="border px-6 py-3">Full Name</th>
                                    <th className="border px-6 py-3">Email</th>
                                    <th className="border px-6 py-3">Contact</th>
                                    <th className="border px-6 py-3">Product</th>
                                    <th className="border px-6 py-3">Inquiry Subject</th>
                                    <th className="border px-6 py-3">Details</th>
                                    <th className="border px-6 py-3">Status</th>
                                    <th className="border px-6 py-3">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {categorizedInquiries[category].length > 0 ? (
                                    categorizedInquiries[category].map((inquiry) => (
                                        <tr key={inquiry._id} className="border hover:bg-gray-100 transition-all">
                                            <td className="border px-6 py-4">{inquiry.fullName}</td>
                                            <td className="border px-6 py-4">{inquiry.email}</td>
                                            <td className="border px-6 py-4">{inquiry.contactNumber}</td>
                                            <td className="border px-6 py-4">{inquiry.productName || "N/A"}</td>
                                            <td className="border px-6 py-4">{inquiry.inquirySubject || "N/A"}</td>
                                            <td className="border px-6 py-4">{inquiry.additionalDetails}</td>
                                            <td className="border px-6 py-4">
                                                {inquiry.status === "Resolved" ? (
                                                    <span className="px-3 py-1 text-yellow-700 rounded-full text-sm font-medium">
                                                        Scheduled for Deletion
                                                    </span>
                                                ) : (
                                                    <span className="px-3 py-1 text-green-700 bg-green-200 rounded-full text-sm font-medium">
                                                        Pending
                                                    </span>
                                                )}
                                            </td>
                                            <td className="border px-6 py-4 flex flex-wrap gap-2">
                                                {inquiry.status !== "Resolved" ? (
                                                    <button
                                                        onClick={() => handleResolveInquiry(inquiry._id)}
                                                        className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-all disabled:bg-blue-300"
                                                        disabled={loading}
                                                    >
                                                        {loading ? "Processing..." : "Resolve"}
                                                    </button>
                                                ) : (
                                                    <>
                                                        <button
                                                            onClick={() => handleDeleteInquiry(inquiry._id)}
                                                            className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all disabled:bg-red-300"
                                                            disabled={loading}
                                                        >
                                                            {loading ? "Deleting..." : "Delete"}
                                                        </button>
                                                        <button
                                                            onClick={() => {
                                                                if (!inquiry.userApproval) {
                                                                    alert("User approval is required to add this inquiry to FAQ.");
                                                                    return;
                                                                }
                                                                setFaqForm({ id: inquiry._id, answer: "" });
                                                            }}
                                                            className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
                                                        >
                                                            Add to FAQ
                                                        </button>
                                                        {faqForm.id === inquiry._id && inquiry.userApproval === true && (
                                                            <div className="mt-2 flex flex-wrap gap-2">
                                                                <input
                                                                    type="text"
                                                                    placeholder="Enter answer"
                                                                    value={faqForm.answer}
                                                                    onChange={(e) => setFaqForm({ ...faqForm, answer: e.target.value })}
                                                                    className="border p-2 rounded-lg w-full md:w-auto"
                                                                />
                                                                <button
                                                                    onClick={() => handleAddToFAQ(inquiry._id)}
                                                                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all"
                                                                >
                                                                    ✅ Submit
                                                                </button>
                                                            </div>
                                                        )}
                                                    </>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="7" className="text-center text-gray-600 py-6">🚫 No inquiries in this category.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            ))}
        </div>
    );
};

// Message Component
const MessageDisplay = ({ message }) => {
    if (!message.text) return null;

    return (
        <div className={`p-4 my-4 text-white rounded-lg ${message.type === "success" ? "bg-green-500" : "bg-red-500"}`}>
            {message.text}
        </div>
    );
};

export default InquiryManage;