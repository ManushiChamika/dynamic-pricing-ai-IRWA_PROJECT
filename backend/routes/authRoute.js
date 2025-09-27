import express from 'express';
import { register, verifyOTP, login, forgotPassword, verifyEmail, resendOTP } from '../controller/authController.js';

const router = express.Router();

router.post('/register', register);
router.post('/verify-otp', verifyOTP);
router.post('/login', login);
router.post('/forgot-password', forgotPassword);
router.post('/verify-email', verifyEmail);
router.post('/resend-otp', resendOTP);

export default router;

