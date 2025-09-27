import mongoose from 'mongoose';
import bcrypt from 'bcryptjs';

const UserSchema = new mongoose.Schema({
    name: {type: String, required: [true, 'Name is required'], trim: true, maxlength: [50, 'Name cannot exceed 50 characters']},
    email: { type: String, required: [true, 'Email is required'], unique: true, trim: true, lowercase: true, validate: {validator: function(v) {return /^\S+@\S+\.\S+$/.test(v);}, message: props => `${props.value} is not a valid email address!`}},
    password: {type: String, required: [true, 'Password is required'], minlength: [8, 'Password must be at least 8 characters long']},
    role: { type: String, enum: ['admin', 'customer'], default: 'customer' , required: true},
    otp: {type: String, select: false},
    otpCreatedAt: { type: Date , select: false},
    isVerified: { type: Boolean, default: false, required: true },
    contactNumber: {type: String, required: [true, 'Contact number is required'], validate: {validator: function(v) {return /^\d{10}$/.test(v);}, message: props => `${props.value} is not a valid 10-digit phone number!`}}, 
    address: {type: String, required: [true, 'Address is required'], trim: true, maxlength: [200, 'Address cannot exceed 200 characters']}
}, {timestamps: true});

const User = mongoose.model('User', UserSchema);

const ensureAdminExists = async () => {
    try {
        const admin1 = await User.findOne({ email: "admin1@example.com" });
        const admin2 = await User.findOne({ email: "admin2@example.com" });

        if (!admin1) {
            await User.create({
                name: "Admin One",
                email: "admin1@example.com",
                password: await bcrypt.hash("admin123", 10), // Hash password
                role: "admin",
                isVerified: true
            });   
        }

        if (!admin2) {
            await User.create({
                name: "Admin Two",
                email: "admin2@example.com",
                password: await bcrypt.hash("admin23", 10), // Hash password
                role: "admin",
                isVerified: true
            });
        }

        console.log("Admins checked/created.");
    } catch (error) {
        console.error("Error ensuring admin accounts:", error.message);
    }
};

ensureAdminExists();

export default User;
