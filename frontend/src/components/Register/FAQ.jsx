import axios from 'axios';
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

function FAQ() { 
    const [faqs, setFaqs] = useState([]);
    const [openIndex, setOpenIndex] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        fetchFAQs();
    }, []);

    const fetchFAQs = async () => {
        try {
            const response = await axios.get("http://localhost:5000/api/faq/get-faqs");
            setFaqs(response.data);
        } catch (error) {
            console.error("Error fetching FAQs: ", error);
        }
    };

    const handleFAQClick = async (index, id) => {
        if (openIndex === index) {
            setOpenIndex(null);
            return;
        }

        setOpenIndex(index);

        setFaqs((prevFaqs) =>
            prevFaqs.map((faq) =>
                faq._id === id ? { ...faq, views: faq.views + 1 } : faq
            )
        );

        try {
            await axios.put(`http://localhost:5000/api/faq/increment-views/${id}`);
        } catch (error) {
            console.error("Error updating FAQ views: ", error);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0a192f] via-[#020c1b] to-[#001f3f] text-white px-6">
    {/* Header Section */}
    <div className="text-center py-12">
        <h1 className="text-5xl font-extrabold text-cyan-400 drop-shadow-lg neon-glow">Frequently Asked Questions</h1>
        <p className="text-gray-300 mt-3 text-lg">Find answers to common questions below.</p>
    </div>

    {/* FAQ Section */}
    <div className="max-w-4xl mx-auto p-8 bg-white/10 backdrop-blur-md shadow-2xl rounded-xl border border-cyan-500 neon-border">
        <ul className="space-y-6">
            {faqs.map((faq, index) => (
                <li key={faq._id} className="border-b border-cyan-500 pb-4 last:border-none">
                    <button
                        onClick={() => handleFAQClick(index, faq._id)}
                        className="w-full flex justify-between items-center text-xl font-semibold text-gray-200 hover:text-cyan-300 transition-all duration-300 cursor-pointer"
                    >
                        {faq.question}
                        <span className="text-cyan-400 text-2xl transition-transform transform hover:scale-125">
                            {openIndex === index ? "−" : "+"}
                        </span>
                    </button>
                    {openIndex === index && (
                        <p className="mt-4 text-gray-200 bg-blue-900/50 p-5 rounded-lg shadow-lg border border-cyan-500 transition-all duration-500">
                            {faq.answer}
                        </p>
                    )}
                </li>
            ))}
        </ul>
    </div>

    {/* Call-to-Action Buttons */}
    <div className="flex justify-center gap-8 mt-14">
        <button
            onClick={() => navigate('/InquiryForm')}
            className="bg-cyan-500 hover:bg-cyan-400 text-white font-bold py-3 px-10 rounded-xl shadow-lg transition-all duration-300 transform hover:scale-110 pulse"
        >
            Add An Inquiry
        </button>
        <button
            onClick={() => navigate('/ReviewForm')}
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-10 rounded-xl shadow-lg transition-all duration-300 transform hover:scale-110 pulse"
        >
            Add A Review
        </button>
    </div>
</div>



)};

export default FAQ;
