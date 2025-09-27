import User from '../models/userModel.js';  
import bcrypt from 'bcryptjs';
 

export const updateUser = async(req, res) => {
    try{
        const {name, email, contactNumber, address} = req.body;
        const updatedUser = await User.findByIdAndUpdate(
            req.user.id,
            {name, email, contactNumber, address},
            {new: true, maxTimeMS: 5000}
        );

        if(!updatedUser){
            return res.status(404).json({message: "User not found"});
        }

        res.status(200).json({
            message: "User updated successfully", 
            user: updatedUser
        });

    }catch(error){
        console.error("Update User Error:", {
            name: error.name,
            message: error.message,
            stack: error.stack
        });

        if (error.name === 'MongoServerError' || error.message.includes('operation timed out')) {
            return res.status(503).json({ message: "Database operation timed out" });
        }
        res.status(500).json({ 
            message: "Error updating user",
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }    
};

export const deleteUser = async(req, res) => {
    try{
        const user = await User.findByIdAndDelete(req.user.id)
            .maxTimeMS(5000);

        if(!user){
            return res.status(404).json({message: "User not found"});
        }

        res.status(200).json({
            message: "User deleted successfully",
            logout: true //Signal frontend to logout
        });

    }catch(error){
        console.error("Delete User Error:", {
            name: error.name,
            message: error.message,
            stack: error.stack
        });

        if (error.name === 'MongoServerError' || error.message.includes('operation timed out')) {
            return res.status(503).json({ message: "Database operation timed out" });
        }
        res.status(500).json({ 
            message: "Error deleting user",
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
};

export const changePassword = async(req, res) => {
    try{
        const {oldPassword, newPassword} = req.body;
        const user = await User.findById(req.user.id)
            .maxTimeMS(5000);

        if(!user){
            return res.status(404).json({message: "User not found"});
        }

        if(!(await bcrypt.compare(oldPassword, user.password))){
            return res.status(400).json({message: "Incorrect old password"});
        }

        const hashedPassword = await bcrypt.hash(newPassword, 10);
        user.password = hashedPassword;
        await user.save({ maxTimeMS: 5000 });

        res.status(200).json({
            message: "Password changed successfully",
            logout: true //Signal frontend to log out
        });
    }catch(error){
        console.error("Change Password Error:", {
            name: error.name,
            message: error.message,
            stack: error.stack
        });

        if (error.name === 'MongoServerError' || error.message.includes('operation timed out')) {
            return res.status(503).json({ message: "Database operation timed out" });
        }
        res.status(500).json({
            message: "Error changing password",
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
};

export const verifyDetails = async (req, res) => {
    // Immediate response headers
    res.header('Access-Control-Allow-Origin', 'http://localhost:5173');
    res.header('Access-Control-Allow-Credentials', 'true');
    res.header('X-Response-Time', 'ms');

    // Timeout configuration
    const REQUEST_TIMEOUT = 8000; // 8 seconds (shorter than frontend)
    let timeoutFired = false;
    const timeout = setTimeout(() => {
        timeoutFired = true;
        if (!res.headersSent) {
            console.error('⏱️ Request timeout triggered');
            return res.status(504).json({ 
                error: "timeout",
                message: "Verification timeout" 
            });
        }
    }, REQUEST_TIMEOUT);

    try {
        // Validate request
        if (!req.body?.email) {
            clearTimeout(timeout);
            return res.status(400).json({ 
                error: "invalid_request",
                message: "Email is required" 
            });
        }

        console.log('🔍 Verifying:', req.body.email);

        // Optimized database query
        const user = await User.findOne({ email: req.body.email })
            .select('name email contactNumber')
            .maxTimeMS(5000) // 5s database timeout
            .lean()
            .exec();

        if (timeoutFired) return; // Abort if timeout already handled

        if (!user) {
            clearTimeout(timeout);
            return res.status(404).json({ 
                verified: false,
                message: "User not found" 
            });
        }

        // Efficient comparison
        const isVerified = (
            user.email === req.body.email &&
            (!req.body.name || user.name?.trim() === req.body.name?.trim()) &&
            (!req.body.contactNumber || user.contactNumber?.trim() === req.body.contactNumber?.trim())
        );

        clearTimeout(timeout);
        return res.json({ 
            verified: isVerified,
            message: isVerified ? "Details verified" : "Details mismatch"
        });

    } catch (error) {
        if (timeoutFired) return;
        clearTimeout(timeout);
        
        console.error('🚨 Verification error:', {
            error: error.message,
            query: error instanceof mongoose.Error ? error.query : undefined,
            time: new Date().toISOString()
        });

        return res.status(500).json({ 
            error: "server_error",
            message: "Verification service unavailable"
        });
    }
};

export const verifyDetailsReveiws = async(req, res) => {
    const {name, email} = req.body;

    try{
        const user = await User.findOne({email});
        if(!user){
            return res.status(404).json({ message: "User not found." });
        }

        // Normalize names by trimming spaces and converting to lowercase
        const normalizedInputName = name?.trim().toLowerCase();
        const normalizedDbName = user.name?.trim().toLowerCase() || "";  // Avoid undefined issue

        console.log("Input Name:", normalizedInputName);
        console.log("DB Name:", normalizedDbName);

        if (normalizedDbName === normalizedInputName &&
            user.email === email) {
            return res.status(200).json({ message: "User details match." });
        } else {
            return res.status(400).json({ message: "Provided details do not match registered details." });
        }
        
    }catch(error){
        console.error("Error in verifyDetails:", error);  // Logs the exact error in the backend console
        res.status(500).json({ message: "Server error.", error: error.message });
    }
};

export const getUsers = async (req, res) => {
    try {
        const users = await User.find({ role: "customer" }, "name email address contactNumber");

        if (!users.length) {
            return res.status(404).json({ message: "No customers found." });
        }

        res.status(200).json(users);
    } catch (error) {
        console.error("Error fetching users:", error);
        res.status(500).json({ message: "Error fetching users", error });
    }
 
};


