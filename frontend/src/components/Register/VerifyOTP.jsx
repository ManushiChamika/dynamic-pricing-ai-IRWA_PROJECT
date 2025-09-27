import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { toast } from "react-toastify";

function VerifyOTP() {
    const [otp, setOtp] = useState(["", "", "", "", "", ""]);
    const [resendDisabled, setResendDisabled] = useState(true);
    const [countdown, setCountdown] = useState(300); // 5 minutes in seconds
    const [otpExpiresAt, setOtpExpiresAt] = useState(null);
    const inputRefs = useRef([]);
    const navigate = useNavigate();

    // Handle countdown timer for resend OTP
    useEffect(() => {
        let timer;
        
        // Update countdown every second
        if (countdown > 0) {
            timer = setTimeout(() => setCountdown(countdown - 1), 1000);
        } else if (countdown === 0 && resendDisabled) {
            setResendDisabled(false);
        }
        
        return () => clearTimeout(timer);
    }, [countdown, resendDisabled]);

    // Format countdown to MM:SS
    const formatCountdown = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    const handleChange = (index, e) => {
        const value = e.target.value;
        if (!/^[0-9]?$/.test(value)) return;

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);

        if (value && index < 5) {
            inputRefs.current[index + 1].focus();
        }
    };

    const handleKeyDown = (index, e) => {
        if (e.key === "Backspace" && !otp[index] && index > 0) {
            inputRefs.current[index - 1].focus();
        }
    };

    const handleVerifyOTP = async (e) => {
        e.preventDefault();
        const enteredOTP = otp.join("");

        if (enteredOTP.length !== 6) {
            toast.error("Please enter a 6-digit OTP.", { position: "top-right" });
            return;
        }

        try {
            const response = await axios.post("http://localhost:5000/api/auth/verify-otp", {
                email: localStorage.getItem("email"),
                otp: enteredOTP
            });

            toast.success("OTP Verified Successfully!", { position: "top-right" });
            localStorage.removeItem("email"); // Clean up
            navigate("/login");
        } catch (error) {
            console.error("Error verifying OTP:", error);
            if (error.response?.data?.message?.includes('not found')) {
                toast.error("OTP not found. Please click 'Resend' for a new code.", {
                    position: "top-right",
                    autoClose: 5000
                });
                setResendDisabled(false); // Enable resend immediately
            } else {
                toast.error(
                    error.response?.data?.message || "Verification failed. Please try again.",
                    { position: "top-right" }
                );
            }
            
            // Clear OTP fields on error
            setOtp(["", "", "", "", "", ""]);
            inputRefs.current[0].focus();
        }
    };

    const handleResendOTP = async () => {
        try {
            const response = await axios.post("http://localhost:5000/api/auth/resend-otp", {
                email: localStorage.getItem("email")
            });
            
            toast.success("New OTP sent to your email!", { position: "top-right" });
            
            // Reset UI state
            setResendDisabled(true);
            setCountdown(300); // 5 minutes
            setOtp(["", "", "", "", "", ""]);
            inputRefs.current[0].focus();
            
            // Debugging
            console.log("Resend response:", response.data);
            
        } catch (error) {
            console.error("Resend error:", error.response?.data);
            toast.error(
                error.response?.data?.message || "Failed to resend OTP. Please try again.",
                { position: "top-right" }
            );
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
            <div className="bg-white p-8 rounded-xl shadow-xl w-[450px]">
                <h2 className="text-3xl font-bold text-center text-gray-700">Verify OTP</h2>
                <p className="text-gray-500 text-center mt-2">
                    Enter the 6-digit code sent to {localStorage.getItem("email")}
                </p>

                {/* OTP Expiration Timer */}
                {resendDisabled && (
                    <div className="text-center mt-2 text-sm text-gray-600">
                        OTP expires in: {formatCountdown(countdown)}
                    </div>
                )}

                <form onSubmit={handleVerifyOTP} className="mt-6 space-y-6">
                    <div className="flex justify-center gap-3">
                        {otp.map((digit, index) => (
                            <input
                                key={index}
                                ref={(el) => (inputRefs.current[index] = el)}
                                type="text"
                                maxLength="1"
                                value={digit}
                                onChange={(e) => handleChange(index, e)}
                                onKeyDown={(e) => handleKeyDown(index, e)}
                                className="w-14 h-14 text-2xl font-semibold text-center border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition duration-200 transform hover:scale-105 focus:scale-110"
                                autoFocus={index === 0}
                            />
                        ))}
                    </div>

                    <button 
                        type="submit" 
                        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold text-lg hover:bg-blue-700 transition duration-300 shadow-md hover:shadow-lg"
                    >
                        Verify OTP
                    </button>

                    <p className="text-center text-gray-500 text-sm">
                        Didn't receive the code?{" "}
                        <button
                            type="button"
                            onClick={!resendDisabled ? handleResendOTP : null}
                            disabled={resendDisabled}
                            className={`${resendDisabled 
                                ? "text-gray-400 cursor-not-allowed" 
                                : "text-blue-500 cursor-pointer hover:underline"}`}
                        >
                            {resendDisabled ? `Resend in ${formatCountdown(countdown)}` : "Resend now"}
                        </button>
                    </p>
                </form>
            </div>
        </div>
    );
}

export default VerifyOTP;