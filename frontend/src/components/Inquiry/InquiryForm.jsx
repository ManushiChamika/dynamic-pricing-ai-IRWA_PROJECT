import React, { useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { AuthContext } from '../../context/authContext';
import { toast } from "react-toastify";

const InquiryForm = () => {
    const { user } = useContext(AuthContext);
    const [formData, setFormData] = useState({
        fullName: user?.name || '',
        email: user?.email || '',
        contactNumber: user?.contactNumber || '',
        inquiryType: 'General',
        productName: '',
        additionalDetails: '',
        userApproval: false,
        attachment: null,
        inquirySubject: '',
    });

    const [submittedData, setSubmittedData] = useState(null);
    const [query, setQuery] = useState("");
    const [suggestedFAQs, setSuggestedFAQs] = useState([]);

    useEffect(() => {
        if(user){
            setFormData(prev => ({
                ...prev,
                fullName: user.name || '',
                email: user.email || '',
                contactNumber: user.contactNumber || ''
            }));
        }
    }, [user]);

    const fetchSimilarFAQs = async (input) => {
        if (!input) {
            setSuggestedFAQs([]);
            return;
        }

        try {
            const response = await axios.get(`http://localhost:5000/api/faq/similar?query=${input}`);
            setSuggestedFAQs(response.data);
        } catch (error) {
            console.error("Error fetching similar FAQs:", error);
        }
    };

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prevState => ({
            ...prevState,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    const handleQueryChange = (e) => {
        setQuery(e.target.value);
        fetchSimilarFAQs(e.target.value);
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            const allowedTypes = ["image/jpeg", "image/jpg", "image/png"];
            const maxSize = 5 * 1024 * 1024; // 5MB
            
            if (!allowedTypes.includes(file.type)) {
                toast.error("Only PNG, JPG, and JPEG files are allowed.");
                e.target.value = ""; // Clear the input
                return;
            }

            if (file.size > maxSize) {
                toast.error("File size too large. Maximum 5MB allowed.");
                e.target.value = ""; // Clear the input
                return;
            }

            setFormData(prevState => ({
                ...prevState,
                attachment: file
            }));
        }
    };

    const handleRemoveFile = () => {
        setFormData(prevState => ({
            ...prevState,
            attachment: null
        }));
        document.getElementById('attachment').value = "";
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log("[DEBUG] Form submission initiated");
        console.log("[AUTH] Current token:", localStorage.getItem("token"));

        // Trim spaces and normalize input before validation
        const trimmedFullName = formData.fullName.trim();
        const trimmedEmail = formData.email.trim();

        if (!trimmedFullName) {
            toast.error('Full Name is required.');
            return;
        }

        if (!trimmedEmail || !/^\S+@\S+\.\S+$/.test(trimmedEmail)) {
            toast.error('Please enter a valid email.');
            return;
        }

        if (!formData.contactNumber.trim() || !/^\d{10}$/.test(formData.contactNumber)) {
            toast.error('Please enter a valid 10-digit contact number.');
            return;
        }

        const token = localStorage.getItem("token");
        if (!user || !token) {
            console.log("[AUTH] User not logged in or token missing");
            toast.error('You must be logged in to submit an inquiry.');
            return;
        }

        try {
            const formDataToSend = new FormData();
                
            formDataToSend.append('fullName', formData.fullName.trim());
            formDataToSend.append('email', formData.email.trim());
            formDataToSend.append('contactNumber', formData.contactNumber);
            formDataToSend.append('inquiryType', formData.inquiryType);
            formDataToSend.append('productName', formData.productName || '');
            formDataToSend.append('additionalDetails', formData.additionalDetails);
            formDataToSend.append('userApproval', formData.userApproval.toString());
            formDataToSend.append('inquirySubject', formData.inquirySubject);
                
            if (formData.attachment) {
                formDataToSend.append('attachment', formData.attachment);
            }

            for (let [key, value] of formDataToSend.entries()) {
                console.log(key, value);
            }
    
            const response = await axios.post(
                "http://localhost:5000/api/inquiries/submit", 
                formDataToSend, 
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'multipart/form-data'
                    },
                    timeout: 15000
                }
            );
    
            console.log("[API] Success response:", response.data);
            toast.success(response.data.message);
            setSubmittedData(response.data.inquiry);

            setFormData(prev => ({
                ...prev,
                inquiryType: 'General',
                productName: '',
                additionalDetails: '',
                userApproval: false,
                attachment: null,
                inquirySubject: '',
            }));
        
        } catch (error) {
            console.error("Full error details:", {
                config: error.config,
                response: error.response,
                request: error.request,
                message: error.message
            });
    
            if (error.response?.data?.message?.includes("already exists")) {
                toast.error("Duplicate inquiry detected. Please check your previous submissions.");
            } 
            else if (error.code === 'ECONNABORTED') {
                toast.error("Server timeout. Please try again.");
            }
            else if (error.response?.status === 400) {
                toast.error(`Validation error: ${error.response.data.message}`);
            }
            else {
                toast.error("Submission failed. Please try again later.");
            }
        }
    };

    return (
        <div className="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-blue-900 via-gray-900 to-black p-6">
            {/* FAQ Search Section */}
            <div className="w-full max-w-xl bg-white bg-opacity-10 backdrop-blur-lg shadow-xl rounded-xl p-6 mb-6 border border-gray-700">
                <h3 className="text-2xl font-semibold text-purple-400 flex items-center gap-2">
                    🔍 Check Before Submitting an Inquiry
                </h3>
                <p className="text-gray-1000 mb-3">Check if your question is already answered in our FAQ section.</p>
                <input
                    type="text"
                    value={query}
                    onChange={handleQueryChange}
                    placeholder="Type your inquiry..."
                    className="w-full border border-gray-700 rounded-lg px-4 py-2 focus:ring focus:ring-purple-500 bg-gray-900 text-gray-200"
                />
                {suggestedFAQs.length > 0 && (
                    <ul className="bg-gray-800 p-2 mt-3 rounded-md border border-gray-700 text-gray-300">
                        {suggestedFAQs.map((faq) => (
                            <li key={faq._id} className="p-2 border-b border-gray-700 last:border-b-0">
                                <strong className="text-purple-400">{faq.question}</strong>
                                <p className="text-gray-400 mt-1">{faq.answer}</p>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Inquiry Form Section */}
            <div className="w-full max-w-xl bg-white bg-opacity-10 backdrop-blur-lg shadow-xl rounded-xl p-6 border border-gray-700">
                <h2 className="text-3xl font-bold text-pink-400 mb-4 flex items-center gap-2">
                    ✉️ Submit an Inquiry
                </h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input type="text" name="fullName" placeholder="Full Name" value={formData.fullName} onChange={handleChange} readOnly className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500" />

                    <input type="email" name="email" placeholder="Email" value={formData.email} onChange={handleChange} readOnly className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500" />

                    <input type="text" name="contactNumber" placeholder="Contact Number" value={formData.contactNumber} onChange={handleChange} readOnly className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500" />

                    <input type="text" name="productName" placeholder="Product Name (if applicable)" value={formData.productName} onChange={handleChange} className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500" />

                    <select name="inquiryType" value={formData.inquiryType} onChange={handleChange} className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500">
                        <option value="General">General</option>
                        <option value="Product Availability">Product Availability</option>
                        <option value="Support">Support</option>
                    </select>

                    <input type="text" name="inquirySubject" placeholder="Subject" value={formData.inquirySubject} onChange={handleChange} required className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500" />

                    <textarea name="additionalDetails" placeholder="Additional Details" value={formData.additionalDetails} onChange={handleChange} required className="w-full border border-gray-700 rounded-lg px-4 py-2 bg-gray-900 text-gray-200 focus:ring focus:ring-pink-500"></textarea>

                    <label className="flex items-center text-gray-1000">
                        <input type="checkbox" name="userApproval" checked={formData.userApproval} onChange={handleChange} className="mr-2" />
                        Allow this inquiry to be added to the FAQ
                    </label>

                    {/* Updated File Upload Section */}
                    <div className="space-y-2">
                        <label className="block text-sm font-medium text-gray-900">Attachment (Optional)</label>
                        <div className="mt-1 flex items-center">
                            <label
                                htmlFor="attachment"
                                className="cursor-pointer flex flex-col items-center justify-center w-full px-4 py-6 border-2 border-gray-700 border-dashed rounded-lg bg-gray-800 hover:bg-gray-750 transition-colors duration-200"
                            >
                                <div className="flex flex-col items-center justify-center pt-5 pb-6">
                                    <svg
                                        className="w-10 h-10 mb-3 text-gray-500"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        xmlns="http://www.w3.org/2000/svg"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                                        ></path>
                                    </svg>
                                    <p className="mb-2 text-sm text-gray-400">
                                        <span className="font-semibold">Click to upload</span> or drag and drop
                                    </p>
                                    <p className="text-xs text-gray-500">
                                        PNG, JPG, JPEG (Max. 5MB)
                                    </p>
                                </div>
                                <input
                                    id="attachment"
                                    name="attachment"
                                    type="file"
                                    accept=".png,.jpg,.jpeg"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />
                            </label>
                        </div>
                        {formData.attachment && (
                            <div className="flex items-center justify-between p-3 bg-gray-800 rounded-lg">
                                <div className="flex items-center space-x-2">
                                    <svg
                                        className="w-5 h-5 text-gray-400"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        xmlns="http://www.w3.org/2000/svg"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                                        ></path>
                                    </svg>
                                    <span className="text-sm text-gray-300 truncate max-w-xs">
                                        {formData.attachment.name}
                                    </span>
                                </div>
                                <button
                                    type="button"
                                    onClick={handleRemoveFile}
                                    className="text-gray-400 hover:text-gray-200"
                                >
                                    <svg
                                        className="w-5 h-5"
                                        fill="none"
                                        stroke="currentColor"
                                        viewBox="0 0 24 24"
                                        xmlns="http://www.w3.org/2000/svg"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth="2"
                                            d="M6 18L18 6M6 6l12 12"
                                        ></path>
                                    </svg>
                                </button>
                            </div>
                        )}
                    </div>

                    <button type="submit" className="w-full bg-pink-500 text-white py-2 rounded-lg hover:bg-pink-600 hover:shadow-lg transition duration-300 transform hover:scale-105">
                        🚀 Submit Inquiry
                    </button>
                </form>
            </div>
        </div>
    );
};

export default InquiryForm;