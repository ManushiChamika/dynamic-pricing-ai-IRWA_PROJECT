import React, { useState, useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../../context/authContext";
import loginImage from "../../assets/login-5.jpg";
import { ToastContainer, toast } from "react-toastify";
import "react-toastify/dist/ReactToastify.css";

const Login = () => {
    const { login } = useContext(AuthContext);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [errors, setErrors] = useState({
        email: "",
        password: "",
        general: ""
    });
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);

    const validateForm = () => {
        let valid = true;
        const newErrors = {
            email: "",
            password: "",
            general: ""
        };

        // Email validation
        if (!email) {
            newErrors.email = "Email is required";
            valid = false;
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            newErrors.email = "Please enter a valid email address";
            valid = false;
        }

        // Password validation
        if (!password) {
            newErrors.password = "Password is required";
            valid = false;
        } 

        setErrors(newErrors);
        return valid;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            toast.error("Please fix the form errors before submitting", {
                position: "top-right",
                autoClose: 5000,
                hideProgressBar: false,
                closeOnClick: true,
                pauseOnHover: true,
                draggable: true,
                progress: undefined,
            });
            return;
        }

        setLoading(true);
        setErrors({ ...errors, general: "" });

        try {
            const user = await login(email, password);
            
            if (user) {
                toast.success("Login successful! Redirecting...", {
                    position: "top-right",
                    autoClose: 3000,
                    hideProgressBar: false,
                    closeOnClick: true,
                    pauseOnHover: true,
                    draggable: true,
                    progress: undefined,
                });
                setTimeout(() => navigate("/"), 2000);
            }
        } catch (error) {
            // Handle specific error cases based on backend responses
            if (error.response) {
                const { data } = error.response;
                if (data.message === 'Invalid credentials') {
                    toast.error("Invalid email or password", {
                        position: "top-right",
                        autoClose: 5000,
                        hideProgressBar: false,
                        closeOnClick: true,
                        pauseOnHover: true,
                        draggable: true,
                        progress: undefined,
                    });
                } else if (data.message === 'Account not verified. Please verify your email first.') {
                    toast.warn("Your account is not verified. Please check your email for verification link.", {
                        position: "top-right",
                        autoClose: 8000,
                        hideProgressBar: false,
                        closeOnClick: true,
                        pauseOnHover: true,
                        draggable: true,
                        progress: undefined,
                    });
                } else {
                    toast.error("Error logging in. Please try again.", {
                        position: "top-right",
                        autoClose: 5000,
                        hideProgressBar: false,
                        closeOnClick: true,
                        pauseOnHover: true,
                        draggable: true,
                        progress: undefined,
                    });
                }
            } else {
                toast.error("Network error. Please check your connection.", {
                    position: "top-right",
                    autoClose: 5000,
                    hideProgressBar: false,
                    closeOnClick: true,
                    pauseOnHover: true,
                    draggable: true,
                    progress: undefined,
                });
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div 
            className="flex items-center justify-center min-h-screen text-white relative"
            style={{
                backgroundImage: `linear-gradient(rgba(0, 0, 0, 0.8), rgba(0, 0, 0, 0.9)), url(${loginImage})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
            }}
        >
            {/* Home Button with hover animation */}
            <Link 
                to="/" 
                className="absolute top-6 left-6 bg-red-600 p-3 rounded-lg shadow-lg hover:bg-red-700 transition-all duration-300 hover:scale-110 flex items-center justify-center group z-10"
            >
                <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className="h-6 w-6 text-white" 
                    fill="none" 
                    viewBox="0 0 24 24" 
                    stroke="currentColor"
                >
                    <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1h3a1 1 0 001-1V10M12 4.5v4" 
                    />
                </svg>
                <span className="absolute opacity-0 group-hover:opacity-100 bg-gray-900 text-white text-xs px-2 py-1 rounded-md -bottom-8 transform transition-all duration-300">Home</span>
            </Link>
    
            <ToastContainer
                position="top-right"
                autoClose={5000}
                hideProgressBar={false}
                newestOnTop={false}
                closeOnClick
                rtl={false}
                pauseOnFocusLoss
                draggable
                pauseOnHover
            />
            
            {/* Main container with subtle floating animation */}
            <div className="flex bg-gray-900 shadow-2xl rounded-lg w-3/5 overflow-hidden border border-blue-700 animate-pulse-slow hover:shadow-blue-500/30 hover:shadow-2xl transition-all duration-500">
                {/* Left side - Form */}
                <div className="w-1/2 p-8 bg-gray-900 bg-opacity-95 relative">
                    {/* Animated RGB Top Border Effect */}
                    <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-red-600 via-blue-500 to-blue-800 animate-gradient-x"></div>
                    
                    {/* Animated Corner Accents */}
                    <div className="absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 border-red-500 animate-pulse"></div>
                    <div className="absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 border-blue-500 animate-pulse"></div>
                    <div className="absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 border-blue-500 animate-pulse"></div>
                    <div className="absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 border-red-500 animate-pulse"></div>
                    
                    <h2 className="text-4xl font-bold mb-6 text-gray-100 flex items-center">
                        <span className="bg-gradient-to-r from-red-500 via-blue-500 to-blue-700 bg-clip-text text-transparent animate-pulse">
                            TECH_
                        </span>
                        <span className="text-gray-100">LOGIN</span>
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 ml-2 text-red-400 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </h2>
    
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-blue-300 text-sm font-bold mb-3 uppercase tracking-wider">EMAIL</label>
                            <div className="relative group">
                                <input 
                                    type="email" 
                                    value={email} 
                                    onChange={(e) => {
                                        setEmail(e.target.value);
                                        setErrors({ ...errors, email: "" });
                                    }} 
                                    required 
                                    placeholder="Enter your email"
                                    className={`w-full pl-10 pr-3 py-3 border-2 ${
                                        errors.email ? "border-red-500" : "border-blue-800"
                                    } bg-gray-800 rounded-lg focus:outline-none focus:ring-2 ${
                                        errors.email ? "focus:ring-red-500" : "focus:ring-blue-500"
                                    } text-white transition-all duration-300 group-hover:border-red-600`}
                                />
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-400 absolute left-3 top-3.5 group-hover:text-red-400 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                {/* Input focus animation */}
                                <div className="absolute bottom-0 left-0 h-0.5 w-0 bg-gradient-to-r from-red-500 to-blue-500 group-hover:w-full transition-all duration-500"></div>
                            </div>
                            {errors.email && (
                                <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.email}</p>
                            )}
                        </div>
                        <div>
                            <label className="block text-blue-300 text-sm font-bold mb-3 uppercase tracking-wider">PASSWORD</label>
                            <div className="relative group">
                                <input 
                                    type="password" 
                                    value={password} 
                                    onChange={(e) => {
                                        setPassword(e.target.value);
                                        setErrors({ ...errors, password: "" });
                                    }} 
                                    required 
                                    placeholder="Enter your password"
                                    className={`w-full pl-10 pr-3 py-3 border-2 ${
                                        errors.password ? "border-red-500" : "border-blue-800"
                                    } bg-gray-800 rounded-lg focus:outline-none focus:ring-2 ${
                                        errors.password ? "focus:ring-red-500" : "focus:ring-blue-500"
                                    } text-white transition-all duration-300 group-hover:border-red-600`}
                                />
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-blue-400 absolute left-3 top-3.5 group-hover:text-red-400 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                                </svg>
                                {/* Input focus animation */}
                                <div className="absolute bottom-0 left-0 h-0.5 w-0 bg-gradient-to-r from-red-500 to-blue-500 group-hover:w-full transition-all duration-500"></div>
                            </div>
                            {errors.password && (
                                <p className="text-red-500 text-sm mt-1 animate-pulse">{errors.password}</p>
                            )}
                        </div>
                        
                        {/* Remember me checkbox with updated styling */}
                        <div className="flex items-center">
                            <input 
                                type="checkbox" 
                                id="remember" 
                                className="w-4 h-4 bg-gray-800 border-blue-600 rounded focus:ring-blue-500"
                            />
                            <label htmlFor="remember" className="ml-2 text-sm text-gray-300">
                                Remember me
                            </label>
                        </div>
                        
                        {/* Animated login button */}
                        <button 
                            type="submit" 
                            className={`w-full text-white py-3 rounded-lg transition duration-300 font-bold relative overflow-hidden group ${
                                loading 
                                ? "bg-gray-600 cursor-not-allowed" 
                                : "bg-gradient-to-r from-red-600 via-blue-600 to-blue-800 hover:from-red-700 hover:via-blue-700 hover:to-blue-900 mt-6 cursor-pointer shadow-lg"
                            }`}
                            disabled={loading}
                        >
                            {loading ? 
                                <span className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    LOGGING IN
                                </span> : 
                                <>
                                    <span className="relative z-10">LOGIN</span>
                                    {/* Button hover effect */}
                                    <span className="absolute top-0 left-0 w-full h-full bg-gradient-to-r from-blue-600 to-red-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-0"></span>
                                </>
                            }
                        </button>
                    </form>
                    <p className="text-gray-400 text-center mt-4">
                        <Link to="/forgot-password" className="hover:text-red-400 transition duration-200 relative group">
                            Forgot Password?
                            <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-red-400 group-hover:w-full transition-all duration-300"></span>
                        </Link>
                    </p>
                    
                    {/* Social Login Options - Updated styling with animations */}
                    <div className="mt-6">
                        <div className="relative">
                            <div className="absolute inset-0 flex items-center">
                                <div className="w-full border-t border-gray-700"></div>
                            </div>
                            <div className="relative flex justify-center text-sm">
                                <span className="px-2 bg-gray-900 text-gray-400">Or continue with</span>
                            </div>
                        </div>
                        <div className="mt-6 grid grid-cols-3 gap-3">
                            {/* Google Icon with animation */}
                            <div>
                                <a href="#" className="w-full flex items-center justify-center px-4 py-2 border border-gray-700 rounded-md shadow-sm bg-gray-800 text-gray-300 hover:bg-gray-700 hover:border-red-600 hover:scale-110 transition-all duration-300">
                                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512">
                                        <path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"/>
                                    </svg>
                                </a>
                            </div>
                            {/* Facebook Icon with animation */}
                            <div>
                                <a href="#" className="w-full flex items-center justify-center px-4 py-2 border border-gray-700 rounded-md shadow-sm bg-gray-800 text-gray-300 hover:bg-gray-700 hover:border-blue-600 hover:scale-110 transition-all duration-300">
                                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 512">
                                        <path fill="currentColor" d="M279.14 288l14.22-92.66h-88.91v-60.13c0-25.35 12.42-50.06 52.24-50.06h40.42V6.26S260.43 0 225.36 0c-73.22 0-121.08 44.38-121.08 124.72v70.62H22.89V288h81.39v224h100.17V288z"/>
                                    </svg>
                                </a>
                            </div>
                            {/* Email Icon with animation */}
                            <div>
                                <a href="#" className="w-full flex items-center justify-center px-4 py-2 border border-gray-700 rounded-md shadow-sm bg-gray-800 text-gray-300 hover:bg-gray-700 hover:border-blue-600 hover:scale-110 transition-all duration-300">
                                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                                        <polyline points="22,6 12,13 2,6"></polyline>
                                    </svg>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                {/* Right side - Promo with updated design and animations */}
                <div className="w-1/2 bg-gradient-to-br from-black via-blue-900 to-red-900 text-white flex flex-col items-center justify-center p-6 text-center relative overflow-hidden">
                    {/* Animated particles background */}
                    <div className="absolute inset-0">
                        <div className="absolute w-2 h-2 rounded-full bg-blue-400 animate-float" style={{top: '10%', left: '20%', animationDelay: '0s'}}></div>
                        <div className="absolute w-2 h-2 rounded-full bg-red-400 animate-float" style={{top: '70%', left: '80%', animationDelay: '0.5s'}}></div>
                        <div className="absolute w-1 h-1 rounded-full bg-blue-300 animate-float" style={{top: '30%', left: '15%', animationDelay: '1s'}}></div>
                        <div className="absolute w-1 h-1 rounded-full bg-red-300 animate-float" style={{top: '60%', left: '40%', animationDelay: '1.5s'}}></div>
                        <div className="absolute w-3 h-3 rounded-full bg-blue-500 animate-float-slow" style={{top: '20%', left: '80%', animationDelay: '2s'}}></div>
                        <div className="absolute w-2 h-2 rounded-full bg-red-500 animate-float-slow" style={{top: '80%', left: '10%', animationDelay: '2.5s'}}></div>
                    </div>
                    
                    {/* Modern Circuit Board Pattern Background with animation */}
                    <div className="absolute inset-0 opacity-10 animate-pulse-slow">
                        <svg xmlns="http://www.w3.org/2000/svg" width="100%" height="100%">
                            <pattern id="circuit-pattern" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
                                <path d="M0 0h50v50H0z" fill="none" />
                                <path d="M10 10h30v30H10z" stroke="#fff" strokeWidth="0.5" fill="none" />
                                <path d="M20 10v-10M20 50v-10M10 20h-10M50 20h-10" stroke="#fff" strokeWidth="0.5" />
                                <circle cx="20" cy="20" r="3" fill="#fff" />
                                <path d="M30 10v-10M30 50v-10M10 30h-10M50 30h-10" stroke="#fff" strokeWidth="0.5" />
                                <circle cx="30" cy="30" r="3" fill="#fff" />
                            </pattern>
                            <rect x="0" y="0" width="100%" height="100%" fill="url(#circuit-pattern)"></rect>
                        </svg>
                    </div>
                    
                    {/* Animated RGB Border */}
                    <div className="absolute inset-x-6 top-6 bottom-6 border-2 border-red-500 rounded-lg opacity-50 animate-pulse-slow"></div>
                    
                    <div className="relative z-10">
                        <div className="mb-6">
                            <div className="relative">
                                <div className="absolute inset-0 blur-sm bg-blue-500 opacity-50 rounded-full animate-pulse"></div>
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-20 w-20 text-red-300 mx-auto relative animate-levitate" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                            </div>
                        </div>
                        <h2 className="text-3xl font-bold text-white mb-2 animate-text-glow">ALPHA IT SOLUTIONS</h2>
                        <p className="text-sm mb-6 text-blue-200">Your gateway to high-performance computing and cutting-edge tech</p>
                        
                        {/* Animated Pulse Line */}
                        <div className="w-16 h-1 bg-gradient-to-r from-red-500 via-blue-400 to-blue-600 mx-auto mb-6 animate-pulse"></div>
                        
                        {/* Product Feature Cards - Updated styling with hover animations */}
                        <div className="grid grid-cols-2 gap-3 mb-6">
                            <div className="bg-black bg-opacity-40 p-3 rounded-lg border border-red-800 hover:border-red-600 transition-all duration-300 hover:scale-105 group">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-400 mx-auto mb-1 group-hover:animate-spin-slow transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                                </svg>
                                <p className="text-xs text-blue-200">Latest CPUs</p>
                            </div>
                            <div className="bg-black bg-opacity-40 p-3 rounded-lg border border-blue-800 hover:border-blue-600 transition-all duration-300 hover:scale-105 group">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-blue-400 mx-auto mb-1 group-hover:animate-spin-slow transition-all" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                </svg>
                                <p className="text-xs text-blue-200">Gaming GPUs</p>
                            </div>
                        </div>
                        
                        <p className="text-blue-200 mb-4">Don't have an account?</p>
                        
                        {/* Sign up button with hover animations */}
                        <Link to="/Register" className="bg-gradient-to-r from-red-600 to-blue-600 text-white px-8 py-3 rounded-lg hover:from-red-700 hover:to-blue-700 transition duration-300 font-semibold inline-flex items-center shadow-lg hover:scale-105 group relative overflow-hidden">
                            <span className="relative z-10">SIGN UP</span>
                            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-2 relative z-10 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                            {/* Animated background effect */}
                            <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-blue-600 to-red-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
                        </Link>
                        
                        {/* Membership Benefits - Updated styling with animations */}
                        <div className="mt-6 text-left">
                            <h3 className="text-sm font-semibold uppercase tracking-wider text-red-300 mb-2">Member Benefits</h3>
                            <ul className="text-xs space-y-1 text-gray-300">
                                <li className="flex items-center group">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-400 mr-1 group-hover:text-red-400 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span className="group-hover:translate-x-1 transition-transform duration-300">Exclusive tech deals</span>
                                </li>
                                <li className="flex items-center group">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-400 mr-1 group-hover:text-red-400 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span className="group-hover:translate-x-1 transition-transform duration-300">Early access to new products</span>
                                </li>
                                <li className="flex items-center group">
                                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-blue-400 mr-1 group-hover:text-red-400 transition-colors duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                    </svg>
                                    <span className="group-hover:translate-x-1 transition-transform duration-300">Free tech support</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;