import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

function ContactUs() {
    const [message, setMessage] = useState('');
    const [conversation, setConversation] = useState([
        { 
            sender: 'bot', 
            text: 'Hello! I\'m TechNova\'s virtual assistant. 🤖\n\nHow can I help you today? You can ask about:\n\n• Store hours & locations\n• Product availability\n• PC configuration advice\n• Order status\n• Technical support' 
        }
    ]);
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const chatContainerRef = useRef(null);
    const isInitialMount = useRef(true);

    // Scroll to bottom of chat container only
    const scrollToBottom = () => {
        if (messagesEndRef.current && chatContainerRef.current) {
            // Calculate if we're near the bottom before scrolling
            const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
            const isNearBottom = scrollHeight - (scrollTop + clientHeight) < 100;
            
            // Only scroll if we're near the bottom or it's a new bot message
            if (isNearBottom || isInitialMount.current) {
                messagesEndRef.current.scrollIntoView({
                    behavior: "smooth",
                    block: "nearest",
                    inline: "start"
                });
            }
        }
    };

    useEffect(() => {
        if (isInitialMount.current) {
            isInitialMount.current = false;
            return;
        }
        scrollToBottom();
    }, [conversation]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!message.trim()) return;

        // Add user message to conversation without scrolling
        setConversation(prev => [...prev, { sender: 'user', text: message }]);
        setMessage('');
        setIsTyping(true);

        try {
            const response = await axios.post('http://localhost:5001/chat', 
                { message },
                { headers: { 'Content-Type': 'application/json' } }
            );
            
            // Add bot response
            setConversation(prev => [...prev, { sender: 'bot', text: response.data.response }]);
        } catch (error) {
            console.error('Error:', error);
            setConversation(prev => [...prev, { 
                sender: 'bot', 
                text: "⚠️ Connection error. For immediate help, please call: (555) 123-4567" 
            }]);
        } finally {
            setIsTyping(false);
        }
    };

    // Modify the message rendering part to use ReactMarkdown
    const renderMessageContent = (text) => {
        return <ReactMarkdown>{text}</ReactMarkdown>;
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-600 via-gray-100 to-blue-200 py-12 px-4 sm:px-6 lg:px-8">
            {/* Enhanced Page Header */}
            <div className="text-center mb-16 animate-fade-in">
                <h1 className="text-6xl font-extrabold bg-gradient-to-r from-indigo-900 via-purple-800 to-blue-800 text-transparent bg-clip-text drop-shadow-lg tracking-wider animate-pulse mb-6">
                    Contact Us
                </h1>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto relative">
                    <span className="absolute -left-6 top-1/2 transform -translate-y-1/2 text-blue-500">❯</span>
                    We're here to help with all your tech needs
                    <span className="absolute -right-6 top-1/2 transform -translate-y-1/2 text-indigo-300">❮</span>
                </p>
                <div className="mt-6 h-1 w-24 bg-gradient-to-r from-indigo-400 to-purple-400 mx-auto rounded-full"></div>
            </div>

            {/* Contact Info + Chat Container */}
            <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8 mb-16">
                {/* Enhanced Contact Information Card */}
                <div className="bg-white rounded-2xl shadow-xl p-8 h-fit transform transition-all hover:scale-[1.02] hover:shadow-2xl">
                    <div className="flex items-center mb-8">
                        <div className="p-3 rounded-xl bg-indigo-100 mr-4">
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                        <h2 className="text-2xl font-bold text-gray-800">Visit Us</h2>
                    </div>
                    
                    <div className="space-y-6">
                        <div className="bg-indigo-50 p-4 rounded-lg border-l-4 border-indigo-400">
                            <h3 className="font-semibold text-gray-700 mb-1 flex items-center">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                </svg>
                                Main Store
                            </h3>
                            <p className="text-gray-600 pl-7">26/C/3 Biyagama Road,<br/>Talwatta Gonawala</p>
                        </div>
                    </div>

                    <div className="mt-12">
                        <div className="flex items-center mb-8">
                            <div className="p-3 rounded-xl bg-indigo-100 mr-4">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-gray-800">Contact Info</h2>
                        </div>
                        <div className="space-y-6">
                            <div className="flex items-start">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-500 mr-3 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                <div>
                                    <p className="font-semibold text-gray-700">Email</p>
                                    <p className="text-gray-600">alphaitsolutions@gmail.com</p>
                                </div>
                            </div>
                            <div className="flex items-start">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-500 mr-3 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                                </svg>
                                <div>
                                    <p className="font-semibold text-gray-700">Phone</p>
                                    <p className="text-gray-600">077 625 2822</p>
                                </div>
                            </div>
                            <div className="flex items-start">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-indigo-500 mr-3 mt-1 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <div>
                                    <p className="font-semibold text-gray-700">Business Hours</p>
                                    <p className="text-gray-600">
                                        Mon-Fri: 9AM - 7PM<br/>
                                        Sat: 10AM - 6PM<br/>
                                        Sun: 11AM - 5PM
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="mt-12">
                        <div className="flex items-center mb-4">
                            <div className="p-3 rounded-xl bg-indigo-100 mr-4">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                            </div>
                            <h2 className="text-2xl font-bold text-gray-800">Holiday Hours</h2>
                        </div>
                        <p className="text-gray-600 pl-16">
                            Closed on Thanksgiving, Christmas, and New Year's Day. Special hours apply during major holidays.
                        </p>
                    </div>
                </div>

                {/* Enhanced Chatbot Section */}
                <div className="lg:col-span-2">
                    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl shadow-2xl overflow-hidden h-full transform transition-all hover:shadow-3xl">
                        {/* Chat Header */}
                        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 flex items-center">
                            <div className="bg-white p-3 rounded-xl mr-4 shadow-md">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-10 w-10 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                                </svg>
                            </div>
                            <div>
                                <h2 className="text-2xl font-bold text-white">TechNova Support</h2>
                                <p className="text-indigo-200">Instant help with products, orders, and tech advice</p>
                            </div>
                            <div className="ml-auto flex space-x-2">
                                <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
                                <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                                <div className="w-3 h-3 bg-red-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                            </div>
                        </div>

                        {/* Chat Messages */}
                        <div 
                            ref={chatContainerRef}
                            className="h-[32rem] p-6 overflow-y-auto bg-gray-800 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-gray-800"
                        >
                            {conversation.map((msg, index) => (
                                <div key={index} className={`flex mb-6 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-xs lg:max-w-md px-5 py-3 rounded-2xl ${msg.sender === 'user' 
                                        ? 'bg-gradient-to-br from-indigo-600 to-purple-600 text-white rounded-br-none shadow-lg' 
                                        : 'bg-gray-700 text-gray-100 rounded-bl-none shadow-lg'}`}>
                                        {msg.sender === 'bot' && (
                                            <div className="flex items-center mb-2">
                                                <div className="bg-indigo-500 p-1 rounded-full mr-2">
                                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                                    </svg>
                                                </div>
                                                <span className="text-xs text-indigo-300">TechNova Bot</span>
                                            </div>
                                        )}
                                        <div className="whitespace-pre-wrap">{renderMessageContent(msg.text)}</div>
                                    </div>
                                </div>
                            ))}
                            {isTyping && (
                                <div className="flex mb-6 justify-start">
                                    <div className="bg-gray-700 text-gray-100 px-5 py-3 rounded-2xl rounded-bl-none max-w-xs shadow-lg">
                                        <div className="flex space-x-2">
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Chat Input */}
                        <form onSubmit={handleSubmit} className="bg-gray-700 p-4 flex border-t border-gray-600">
                            <input
                                type="text"
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                placeholder="Ask about products, store hours, or tech support..."
                                className="flex-1 bg-gray-600 text-white px-5 py-4 rounded-l-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-400"
                            />
                            <button 
                                type="submit" 
                                disabled={!message.trim()}
                                className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-6 py-4 rounded-r-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 flex items-center shadow-md hover:shadow-lg"
                            >
                                <span className="mr-2 font-medium">Send</span>
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                                </svg>
                            </button>
                        </form>

                        {/* Quick Suggestions */}
                        <div className="bg-gray-800 p-4 flex overflow-x-auto space-x-3 border-t border-gray-700 scrollbar-hide">
                            <button 
                                onClick={() => setMessage("What are your store hours?")}
                                className="bg-gray-700 hover:bg-gray-600 text-sm text-gray-300 px-5 py-2 rounded-full whitespace-nowrap transition-colors flex items-center shadow-sm hover:shadow-md"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                Store Hours
                            </button>
                            <button 
                                onClick={() => setMessage("Do you have RTX 4080 in stock?")}
                                className="bg-gray-700 hover:bg-gray-600 text-sm text-gray-300 px-5 py-2 rounded-full whitespace-nowrap transition-colors flex items-center shadow-sm hover:shadow-md"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                                </svg>
                                Product Availability
                            </button>
                            <button 
                                onClick={() => setMessage("Can you help me build a gaming PC?")}
                                className="bg-gray-700 hover:bg-gray-600 text-sm text-gray-300 px-5 py-2 rounded-full whitespace-nowrap transition-colors flex items-center shadow-sm hover:shadow-md"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                                </svg>
                                PC Building Help
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Enhanced Map Section */}
            <div className="max-w-7xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="p-8">
                    <h2 className="text-3xl font-bold text-gray-800 mb-6 flex items-center">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-indigo-600 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        Our Locations
                    </h2>
                    <div className="aspect-w-16 aspect-h-9 rounded-xl overflow-hidden border-2 border-gray-200 shadow-md">
                        <iframe 
                            src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2027786.7872855498!2d77.49990205625!3d6.947693!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ae25715a95172c5%3A0x19200bec0f99b32e!2sAlpha%20IT%20Solution!5e0!3m2!1sen!2slk!4v1744645444523!5m2!1sen!2slk"
                            width="100%" 
                            height="450" 
                            style={{ border: 0 }} 
                            allowFullScreen="" 
                            loading="lazy"
                            className="w-full h-[450px]"
                        ></iframe>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ContactUs;