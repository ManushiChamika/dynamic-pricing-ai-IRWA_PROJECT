import User from '../models/userModel.js';  
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import sendEmail from '../config/nodemailer.js'; 
import { otpTemplate } from '../emailTemplates/otpTemplate.js';
import { welcomeTemplate } from '../emailTemplates/welcomeTemplate.js';
import { forgotPasswordTemplate } from '../emailTemplates/forgotPasswordTemplate.js';
import { body, validationResult } from 'express-validator';
import { resetOTPTemplate } from '../emailTemplates/resetOTPTemplate.js';

export const register = async (req, res) => {
    try {
        // Run all validations first
        await Promise.all([
            body('name')
                .notEmpty().withMessage('Name is required').bail()
                .matches(/^[A-Za-z\s]+$/).withMessage('Name can only contain letters').run(req),
            
            body('email')
                .notEmpty().withMessage('Email is required').bail()
                .isEmail().withMessage('Invalid email format').run(req),
            
            body('password')
                .notEmpty().withMessage('Password is required').bail()
                .isLength({ min: 8 }).withMessage('Password must be at least 8 characters long').bail()
                .matches(/[A-Z]/).withMessage('Password must contain at least one uppercase letter').bail()
                .matches(/[a-z]/).withMessage('Password must contain at least one lowercase letter').bail()
                .matches(/[0-9]/).withMessage('Password must contain at least one number').bail()
                .matches(/[!@#$%^&*(),.?":{}|<>]/).withMessage('Password must contain at least one special character').run(req),
            
            body('confirmPassword')
                .notEmpty().withMessage('Confirm password is required').bail()
                .custom((value, { req }) => value === req.body.password).withMessage('Passwords do not match').run(req),
            
            body('contactNumber')
                .notEmpty().withMessage('Contact number is required').bail()
                .isLength({ min: 10, max: 10 }).withMessage('Contact number must be 10 digits').bail()
                .isNumeric().withMessage('Contact number must contain only numbers').run(req),
            
            body('address')
                .notEmpty().withMessage('Address is required').run(req)
        ]);

        // ✅ Get validation errors properly
        const validationErrors = validationResult(req); // Changed from `errors` to `validationErrors`
        
        if (!validationErrors.isEmpty()) { // Changed from `errors` to `validationErrors`
            return res.status(400).json({ 
                success: false,
                errors: validationErrors.array().map(err => ({ // Changed from `errors` to `validationErrors`
                    field: err.path,
                    message: err.msg
                }))
            });
        }

        const { name, email, password, contactNumber, address } = req.body;

        // Check if the user already exists
        const existingUser = await User.findOne({ email });
        if (existingUser) {
            return res.status(400).json({ 
                success: false,
                errors: [{
                    field: 'email',
                    message: 'Email already in use'
                }]
            });
        }
        
        const hashedPassword = await bcrypt.hash(password, 10);
        const otp = Math.floor(100000 + Math.random() * 900000).toString();
        const otpCreatedAt = new Date();

        const newUser = new User({ name, email, password: hashedPassword, otp, otpCreatedAt, isVerified: false, contactNumber, address });
        await newUser.save();

        const htmlContent = otpTemplate(name, otp);
        await sendEmail(email, 'OTP Verification', htmlContent);

        return res.json({ success: true, message: 'OTP sent to email', otpExpiresIn: '5 minutes' });
    } catch (error) {
        console.error("Registration Error:", error);
        return res.status(500).json({ success: false, message: 'Error registering user', error: error.message });
    }
};

export const verifyOTP = async (req, res) => {
    try {
        const { email, otp } = req.body;
        
        // Explicitly include OTP fields which are normally hidden
        const user = await User.findOne({ email })
            .select('+otp +otpCreatedAt');

        if (!user) {
            return res.status(404).json({ 
                success: false,
                message: 'User not found' 
            });
        }

        // Debug logging
        console.log('Stored OTP:', user.otp);
        console.log('Current time:', new Date());
        console.log('OTP created at:', user.otpCreatedAt);

        if (!user.otp) {
            return res.status(400).json({ 
                success: false,
                message: 'OTP not found. Please request a new one.' 
            });
        }

        const otpExpirationTime = 5 * 60 * 1000; // 5 minutes
        const currentTime = new Date();
        const otpCreatedAt = new Date(user.otpCreatedAt);

        if ((currentTime - otpCreatedAt) > otpExpirationTime) {
            // Auto-clear expired OTP
            user.otp = undefined;
            user.otpCreatedAt = undefined;
            await user.save();
            
            return res.status(400).json({ 
                success: false,
                message: 'OTP has expired. Please request a new one.' 
            });
        }

        if (user.otp !== otp) {
            return res.status(400).json({ 
                success: false,
                message: 'Invalid OTP' 
            });
        }

        // Successful verification
        user.isVerified = true;
        user.otp = undefined;
        user.otpCreatedAt = undefined;
        await user.save();

        const htmlContent = welcomeTemplate(user.name);
        await sendEmail(email, 'Welcome!', htmlContent);

        return res.json({ 
            success: true,
            message: 'User Verified' 
        });

    } catch (error) {
        console.error("OTP Verification Error:", error);
        return res.status(500).json({ 
            success: false,
            message: 'Error verifying OTP', 
            error: error.message 
        });
    }
};

export const login = async (req, res) => {
    try {
        const { email, password, contactNumber, address } = req.body;
        const user = await User.findOne({ email });

        if (!user || !(await bcrypt.compare(password, user.password))) {
            return res.status(400).json({ 
                success: false,
                message: 'Invalid credentials' 
            });
        }

        if (!user.isVerified) {
            return res.status(403).json({
                success: false,
                message: 'Account not verified. Please verify your email first.'
            });
        }

        const token = jwt.sign(
            { id: user._id, role: user.role, name: user.name, email: user.email, contactNumber: user.contactNumber, address: user.address },
            process.env.JWT_SECRET,
            { expiresIn: '1h' }
        );

        // Send the login response and return immediately
        return res.json({
            success: true,
            message: "Login Successful", 
            token, 
            user: { _id: user._id ,role: user.role, name: user.name, email: user.email, contactNumber: user.contactNumber, address: user.address} 
        });
    } catch (error) {
        return res.status(500).json({ success: false, message: 'Error logging in', error: error.message });
    }
};

export const verifyEmail = async (req, res) => {
    try {
        const { email } = req.body;
        const user = await User.findOne({ email });

        if (!user) {
            return res.status(404).json({ 
                success: false,
                message: "User not found" 
            });
        }

        return res.json({ success: true, message: "Email verified, proceed to reset password" });
    } catch (error) {
        return res.status(500).json({ success: false, message: 'Error verifying email', error: error.message });
    }
};

export const forgotPassword = async (req, res) => {
    try {
        const { email, newPassword, confirmPassword } = req.body;

        if (newPassword !== confirmPassword) {
            return res.status(400).json({ 
                success: false,
                errors: [{
                    field: 'confirmPassword',
                    message: 'Passwords do not match'
                }]
            });
        }

        // Validate new password strength
        await Promise.all([
            body('newPassword')
                .notEmpty().withMessage('Password is required').bail()
                .isLength({ min: 8 }).withMessage('Password must be at least 8 characters long').bail()
                .matches(/[A-Z]/).withMessage('Password must contain at least one uppercase letter').bail()
                .matches(/[a-z]/).withMessage('Password must contain at least one lowercase letter').bail()
                .matches(/[0-9]/).withMessage('Password must contain at least one number').bail()
                .matches(/[!@#$%^&*(),.?":{}|<>]/).withMessage('Password must contain at least one special character').run(req)
        ]);

        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ 
                success: false,
                errors: errors.array().map(err => ({
                    field: err.path,
                    message: err.msg
                }))
            });
        }

        const user = await User.findOne({ email });
        if (!user) {
            return res.status(404).json({ success: false, message: "User not found" });
        }

        user.password = await bcrypt.hash(newPassword, 10);
        await user.save();

        const htmlContent = forgotPasswordTemplate(user.name);
        await sendEmail(email, 'Password Changed', htmlContent);

        return res.json({ success: true, message: "Password updated successfully, redirecting to login" });
    } catch (error) {
        return res.status(500).json({ success: false, message: 'Error resetting password', error: error.message });
    }
};

export const resendOTP = async (req, res) => {
    try {
        const { email } = req.body;
        const user = await User.findOne({ email });

        if (!user) {
            return res.status(404).json({
                success: false,
                message: 'User not found'
            });
        }

        // Generate and save new OTP
        const newOTP = Math.floor(100000 + Math.random() * 900000).toString();
        user.otp = newOTP;
        user.otpCreatedAt = new Date();
        
        // Explicitly mark as modified
        user.markModified('otp');
        user.markModified('otpCreatedAt');
        
        await user.save();

        // Debug logging
        console.log('New OTP saved:', newOTP);
        console.log('For user:', email);

        const htmlContent = resetOTPTemplate(user.name, newOTP);
        await sendEmail(email, 'Your New Verification Code', htmlContent);

        return res.json({
            success: true,
            message: 'New OTP sent successfully',
            otp: newOTP // For debugging
        });

    } catch (error) {
        console.error("Resend OTP Error:", error);
        return res.status(500).json({
            success: false,
            message: 'Error resending OTP',
            error: error.message
        });
    }
};