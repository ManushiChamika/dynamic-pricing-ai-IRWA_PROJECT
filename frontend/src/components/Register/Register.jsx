import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';  
import axios from 'axios';
import { toast } from "react-toastify";
import loginImage from "../../assets/login-5.jpg";

const Register = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [contactNumber, setContactNumber] = useState('');
    const [address, setAddress] = useState('');
    const navigate = useNavigate(); 

    const [nameError, setNameError] = useState('');
    const [emailError, setEmailError] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [confirmPasswordError, setConfirmPasswordError] = useState('');
    const [contactNumberError, setContactNumberError] = useState('');
    const [addressError, setAddressError] = useState('');

    const [passwordStrength, setPasswordStrength] = useState({
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        specialChar: false
    });

    const [strengthLevel, setStrengthLevel] = useState(0);
    const [strengthColor, setStrengthColor] = useState('bg-gray-500');

    // Validate name (letters only)
    const validateName = (value) => {
        if (!value) {
            setNameError("Name is required");
            return false;
        } else if (!/^[A-Za-z\s]+$/.test(value)) {
            setNameError("Name can only contain letters");
            return false;
        } else {
            setNameError("");
            return true;
        }
    };

    // Validate email
    const validateEmail = (value) => {
        if (!value) {
            setEmailError("Email is required");
            return false;
        } else if (!/^\S+@\S+\.\S+$/.test(value)) {
            setEmailError("Invalid email format");
            return false;
        } else {
            setEmailError("");
            return true;
        }
    };

    // Enhanced password validation with strength meter
    const validatePassword = (value) => {
        const newStrength = {
            length: value.length >= 8,
            uppercase: /[A-Z]/.test(value),
            lowercase: /[a-z]/.test(value),
            number: /[0-9]/.test(value),
            specialChar: /[!@#$%^&*(),.?":{}|<>]/.test(value)
        };

        setPasswordStrength(newStrength);

        // Calculate strength level (0-5)
        const level = Object.values(newStrength).filter(Boolean).length;
        setStrengthLevel(level);

        // Set strength color
        let color;
        if (level <= 1) color = 'bg-red-500';
        else if (level === 2) color = 'bg-yellow-500';
        else if (level === 3) color = 'bg-blue-500';
        else color = 'bg-green-500';
        setStrengthColor(color);

        // Set error message if needed
        if (!value) {
            setPasswordError("Password is required");
            return false;
        } else if (level < 5) {
            setPasswordError("Please meet all password requirements");
            return false;
        } else {
            setPasswordError("");
            return true;
        }
    };

    // Validate confirm password
    const validateConfirmPassword = (value) => {
        if (!value) {
            setConfirmPasswordError("Confirm password is required");
            return false;
        } else if (password !== value) {
            setConfirmPasswordError("Passwords do not match");
            return false;
        } else {
            setConfirmPasswordError("");
            return true;
        }
    };

    // Validate contact number
    const validateContactNumber = (value) => {
        if (!value) {
            setContactNumberError("Contact number is required");
            return false;
        } else if (!/^\d{10}$/.test(value)) {
            setContactNumberError("Invalid contact number. It should be 10 digits.");
            return false;
        } else {
            setContactNumberError("");
            return true;
        }
    };

    // Validate address
    const validateAddress = (value) => {
        if (!value) {
            setAddressError("Address is required");
            return false;
        } else {
            setAddressError("");
            return true;
        }
    };

    // Handle name change with validation
    const handleNameChange = (e) => {
        const value = e.target.value;
        // Only allow letters and spaces
        if (/^[A-Za-z\s]*$/.test(value)) {
            setName(value);
            validateName(value);
        }
    };

    // Validate all fields before submission
    const validateAll = () => {
        const isNameValid = validateName(name);
        const isEmailValid = validateEmail(email);
        const isPasswordValid = validatePassword(password);
        const isConfirmPasswordValid = validateConfirmPassword(confirmPassword);
        const isContactNumberValid = validateContactNumber(contactNumber);
        const isAddressValid = validateAddress(address);

        return (
            isNameValid &&
            isEmailValid &&
            isPasswordValid &&
            isConfirmPasswordValid &&
            isContactNumberValid &&
            isAddressValid
        );
    };

    const handleRegister = async (e) => {
        e.preventDefault();

        if (!validateAll()) return;

        try {
            console.log("Sending:", { name, email, password, confirmPassword, contactNumber, address });
            const response = await axios.post('http://localhost:5000/api/auth/register', { 
                name, 
                email, 
                password, 
                confirmPassword,
                contactNumber, 
                address 
            });
            
            localStorage.setItem('email', email);

            toast.success("Check your email for OTP verification!", { position: "top-right" });
            
            navigate('/verify-otp');
        } catch (error) {
            console.error('Registration failed:', error);
            if (error.response?.data?.errors) {
                error.response.data.errors.forEach(err => {
                    toast.error(`${err.field}: ${err.message}`, { position: "top-right" });
                });
            toast.error(errorMessage, { position: "top-right" });
            }
        }
    };

    // Validate confirm password whenever password changes
    useEffect(() => {
        if (confirmPassword) {
            validateConfirmPassword(confirmPassword);
        }
    }, [password]);

    return (
        <div className="flex items-center justify-center min-h-screen text-white relative"
            style={{
                backgroundImage:`url(${loginImage})`,
                backgroundSize: "cover",
                backgroundPosition: "center",
            }}
        >
            <div className="bg-gray-900 p-6 rounded-lg shadow-lg w-130 text-gray-300">
                <h2 className="text-4xl font-semibold text-center mb-4 text-gray-200">
                    <span className="bg-gradient-to-r from-red-900 to-blue-500 bg-clip-text text-transparent">
                        R
                    </span>
                    egister
                </h2>
                <form onSubmit={handleRegister} className="space-y-4">
                    <div>
                        <label className="block text-gray-300 mb-3">NAME</label>
                        <input 
                            type="text" 
                            value={name} 
                            onChange={handleNameChange} 
                            required 
                            placeholder="Enter your name"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                        />
                        {nameError && <p className="text-red-500 text-sm mt-1">{nameError}</p>}
                    </div>
                    <div>
                        <label className="block text-gray-300 mb-3 mt-5">EMAIL</label>
                        <input 
                            type="email" 
                            value={email} 
                            onChange={(e) => {
                                setEmail(e.target.value);
                                validateEmail(e.target.value);
                            }} 
                            required 
                            placeholder="Enter your email"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                        />
                        {emailError && <p className="text-red-500 text-sm mt-1">{emailError}</p>}
                    </div>
                    <div>
                        <label className="block text-gray-300 mb-3 mt-5">PASSWORD</label>
                        <input 
                            type="password" 
                            value={password} 
                            onChange={(e) => {
                                setPassword(e.target.value);
                                validatePassword(e.target.value);
                            }} 
                            required 
                            placeholder="Enter your password"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                        />
                        
                        {/* Password Strength Meter */}
                        <div className="mt-2">
                            <div className="flex items-center mb-1">
                                <div className="w-full bg-gray-700 rounded-full h-2">
                                    <div 
                                        className={`h-2 rounded-full ${strengthColor} transition-all duration-300`}
                                        style={{ width: `${strengthLevel * 20}%` }}
                                    ></div>
                                </div>
                                <span className="ml-2 text-xs">
                                    {strengthLevel <= 1 ? 'Weak' : 
                                     strengthLevel <= 3 ? 'Medium' : 'Strong'}
                                </span>
                            </div>
                            
                            {/* Creative Password Requirements */}
                            <div className="grid grid-cols-2 gap-1 text-xs">
                                <div className={`flex items-center ${passwordStrength.length ? 'text-green-400' : 'text-gray-400'}`}>
                                    <span className="mr-1">✓</span>
                                    <span>8+ characters</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.uppercase ? 'text-green-400' : 'text-gray-400'}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Uppercase letter</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.lowercase ? 'text-green-400' : 'text-gray-400'}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Lowercase letter</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.number ? 'text-green-400' : 'text-gray-400'}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Number</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.specialChar ? 'text-green-400' : 'text-gray-400'}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Special character</span>
                                </div>
                            </div>
                        </div>
                        
                        {passwordError && <p className="text-red-500 text-sm mt-1">{passwordError}</p>}
                    </div>
                    <div>
                        <label className="block text-gray-300 mb-3 mt-5">CONFIRM PASSWORD</label>
                        <input 
                            type="password" 
                            value={confirmPassword} 
                            onChange={(e) => {
                                setConfirmPassword(e.target.value);
                                validateConfirmPassword(e.target.value);
                            }} 
                            required 
                            placeholder="Confirm your password"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                        />
                        {confirmPasswordError && <p className="text-red-500 text-sm mt-1">{confirmPasswordError}</p>}
                    </div>
                    <div>
                        <label className="block text-gray-300 mb-3 mt-5">CONTACT NUMBER</label>
                        <input 
                            type="text" 
                            value={contactNumber} 
                            onChange={(e) => {
                                // Only allow numbers
                                const value = e.target.value.replace(/\D/g, '');
                                setContactNumber(value);
                                validateContactNumber(value);
                            }} 
                            required 
                            placeholder="Enter your contact number"
                            maxLength="10"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                        />
                        {contactNumberError && <p className="text-red-500 text-sm mt-1">{contactNumberError}</p>}
                    </div>
                    <div>
                        <label className="block text-gray-300 mb-3 mt-5">ADDRESS</label>
                        <input 
                            type="text" 
                            value={address} 
                            onChange={(e) => {
                                setAddress(e.target.value);
                                validateAddress(e.target.value);
                            }} 
                            required 
                            placeholder="Enter your address"
                            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-400"
                        />
                        {addressError && <p className="text-red-500 text-sm mt-1">{addressError}</p>}
                    </div>
                    <button 
                        type="submit" 
                        className="w-full bg-gradient-to-r from-blue-900 to-red-900 text-white py-2 rounded-lg transition duration-300 mt-8 cursor-pointer font-bold hover:opacity-90"
                    >
                        Create Account
                    </button>
                </form>
                <div className="text-center mt-4">
                    <p>Already have an account? <a href="/login" className="text-blue-400 hover:underline">Login</a></p>
                </div>
            </div>
        </div>
    );
};

export default Register;