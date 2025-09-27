import axios from 'axios';
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom';

function ForgotPassword() {
    const [step, setStep] = useState(1); // 1 = Verify Email, 2 = Reset Password
    const [email, setEmail] = useState("");
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [message, setMessage] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});
    const navigate = useNavigate();

    // Password strength state
    const [passwordStrength, setPasswordStrength] = useState({
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        specialChar: false
    });

    const [strengthLevel, setStrengthLevel] = useState(0);
    const [strengthColor, setStrengthColor] = useState('bg-gray-500');

    // Validate email
    const validateEmail = (value) => {
        if (!value) {
            setErrors({...errors, email: "Email is required"});
            return false;
        } else if (!/^\S+@\S+\.\S+$/.test(value)) {
            setErrors({...errors, email: "Invalid email format"});
            return false;
        } else {
            const newErrors = {...errors};
            delete newErrors.email;
            setErrors(newErrors);
            return true;
        }
    };

    // Validate password
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

        if (!value) {
            setErrors({...errors, newPassword: "Password is required"});
            return false;
        } else if (level < 5) {
            setErrors({...errors, newPassword: "Please meet all password requirements"});
            return false;
        } else {
            const newErrors = {...errors};
            delete newErrors.newPassword;
            setErrors(newErrors);
            return true;
        }
    };

    // Validate confirm password
    const validateConfirmPassword = (value) => {
        if (!value) {
            setErrors({...errors, confirmPassword: "Confirm password is required"});
            return false;
        } else if (newPassword !== value) {
            setErrors({...errors, confirmPassword: "Passwords do not match"});
            return false;
        } else {
            const newErrors = {...errors};
            delete newErrors.confirmPassword;
            setErrors(newErrors);
            return true;
        }
    };

    // Validate confirm password when password changes
    useEffect(() => {
        if (confirmPassword) {
            validateConfirmPassword(confirmPassword);
        }
    }, [newPassword]);

    // Verify Email
    const handleVerifyEmail = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage("");
        setError("");

        if (!validateEmail(email)) {
            setLoading(false);
            return;
        }

        try {
            const response = await axios.post("http://localhost:5000/api/auth/verify-email", { email });
            setMessage(response.data.message);
            setTimeout(() => {
                setStep(2); // Move to Reset Password step
            }, 2000);
        } catch (err) {
            setError(err.response?.data?.message || "Something went wrong");
            if (err.response?.data?.errors) {
                setErrors(err.response.data.errors.reduce((acc, curr) => {
                    acc[curr.field] = curr.message;
                    return acc;
                }, {}));
            }
        } finally {
            setLoading(false);
        }
    };

    // Reset Password
    const handleResetPassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage("");
        setError("");

        const isPasswordValid = validatePassword(newPassword);
        const isConfirmValid = validateConfirmPassword(confirmPassword);

        if (!isPasswordValid || !isConfirmValid) {
            setLoading(false);
            return;
        }

        try {
            const response = await axios.post("http://localhost:5000/api/auth/forgot-password", { 
                email, 
                newPassword, 
                confirmPassword 
            });
            setMessage(response.data.message);
            setTimeout(() => {
                navigate("/Login");
            }, 3000);
        } catch (err) {
            setError(err.response?.data?.message || "Something went wrong");
            if (err.response?.data?.errors) {
                setErrors(err.response.data.errors.reduce((acc, curr) => {
                    acc[curr.field] = curr.message;
                    return acc;
                }, {}));
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-900 to-red-900">
            <div className="w-full max-w-md p-8 bg-white rounded-lg shadow-lg">
                <h2 className="text-3xl font-bold text-center text-gray-700">
                    {step === 1 ? "Forgot Password?" : "Reset Your Password"}
                </h2>
                <p className="text-center text-gray-500 mt-2">
                    {step === 1 ? "No worries! Enter your email to get a reset link." : "Create a new password to secure your account."}
                </p>

                {message && <p className="mt-4 text-green-600 text-center font-semibold">{message}</p>}
                {error && <p className="mt-4 text-red-600 text-center font-semibold">{error}</p>}

                {step === 1 ? (
                    // Email Verification
                    <form onSubmit={handleVerifyEmail} className="mt-6">
                        <label className="block mb-2 text-sm font-medium text-gray-600">Enter your email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => {
                                setEmail(e.target.value);
                                validateEmail(e.target.value);
                            }}
                            required
                            className={`w-full px-4 py-3 text-sm border rounded-lg focus:outline-none focus:ring-2 ${
                                errors.email ? 'border-red-500 focus:ring-red-300' : 'border-gray-300 focus:ring-gray-400'
                            }`}
                            placeholder="Enter your email"
                        />
                        {errors.email && <p className="mt-1 text-sm text-red-500">{errors.email}</p>}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-4 py-2 mt-4 text-white bg-gradient-to-r from-blue-900 to-red-900 rounded-lg hover:bg-blue-700 transition font-semibold cursor-pointer disabled:opacity-70"
                        >
                            {loading ? "Checking..." : "Verify Email"}
                        </button>

                        <p className="text-center text-gray-500 text-sm mt-4">
                            Remembered your password?{" "}
                            <span
                                onClick={() => navigate("/Login")}
                                className="text-blue-500 hover:underline cursor-pointer"
                            >
                                Back to Login
                            </span>
                        </p>
                    </form>
                ) : (
                    // Reset Password
                    <form onSubmit={handleResetPassword} className="mt-6">
                        <label className="block mb-2 text-sm font-medium text-gray-600">New Password</label>
                        <input
                            type="password"
                            value={newPassword}
                            onChange={(e) => {
                                setNewPassword(e.target.value);
                                validatePassword(e.target.value);
                            }}
                            required
                            className={`w-full px-4 py-3 text-sm border rounded-lg focus:outline-none focus:ring-2 ${
                                errors.newPassword ? 'border-red-500 focus:ring-red-300' : 'border-gray-300 focus:ring-gray-500'
                            }`}
                            placeholder="New Password"
                        />
                        
                        {/* Password Strength Meter */}
                        <div className="mt-2">
                            <div className="flex items-center mb-1">
                                <div className="w-full bg-gray-200 rounded-full h-2">
                                    <div 
                                        className={`h-2 rounded-full ${strengthColor} transition-all duration-300`}
                                        style={{ width: `${strengthLevel * 20}%` }}
                                    ></div>
                                </div>
                                <span className="ml-2 text-xs text-gray-600">
                                    {strengthLevel <= 1 ? 'Weak' : 
                                     strengthLevel <= 3 ? 'Medium' : 'Strong'}
                                </span>
                            </div>
                            
                            {/* Password Requirements */}
                            <div className="grid grid-cols-2 gap-1 text-xs text-gray-600">
                                <div className={`flex items-center ${passwordStrength.length ? 'text-green-500' : ''}`}>
                                    <span className="mr-1">✓</span>
                                    <span>8+ characters</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.uppercase ? 'text-green-500' : ''}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Uppercase</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.lowercase ? 'text-green-500' : ''}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Lowercase</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.number ? 'text-green-500' : ''}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Number</span>
                                </div>
                                <div className={`flex items-center ${passwordStrength.specialChar ? 'text-green-500' : ''}`}>
                                    <span className="mr-1">✓</span>
                                    <span>Special char</span>
                                </div>
                            </div>
                        </div>
                        
                        {errors.newPassword && <p className="mt-1 text-sm text-red-500">{errors.newPassword}</p>}

                        <label className="block mt-4 mb-2 text-sm font-medium text-gray-600">Confirm Password</label>
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => {
                                setConfirmPassword(e.target.value);
                                validateConfirmPassword(e.target.value);
                            }}
                            required
                            className={`w-full px-4 py-3 text-sm border rounded-lg focus:outline-none focus:ring-2 ${
                                errors.confirmPassword ? 'border-red-500 focus:ring-red-300' : 'border-gray-300 focus:ring-gray-500'
                            }`}
                            placeholder="Confirm Password"
                        />
                        {errors.confirmPassword && <p className="mt-1 text-sm text-red-500">{errors.confirmPassword}</p>}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full px-4 py-2 mt-4 text-white bg-gradient-to-r from-blue-900 to-red-900 rounded-lg hover:bg-blue-900 transition font-semibold cursor-pointer disabled:opacity-70"
                        >
                            {loading ? "Updating..." : "Reset Password"}
                        </button>

                        <p className="text-center text-gray-500 text-sm mt-4">
                            Changed your mind?{" "}
                            <span
                                onClick={() => navigate("/Login")}
                                className="text-blue-900 hover:underline cursor-pointer"
                            >
                                Back to Login
                            </span>
                        </p>
                    </form>
                )}
            </div>
        </div>
    );
}

export default ForgotPassword;