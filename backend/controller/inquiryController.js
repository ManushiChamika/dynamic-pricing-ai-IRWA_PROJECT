import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import Inquiry from '../models/inquiryModel.js';
import sendEmail from '../config/nodemailer.js';
import { inquiryTemplate } from '../emailTemplates/inquiryTemplate.js';
import FAQ from '../models/faqModel.js';
import multer from 'multer';
import cron from "node-cron";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define upload directory
const uploadDir = path.join(__dirname, '../uploads/inquiries/');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir, { recursive: true });
}
// Configure Multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadDir);
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`);
    }
});

// File filter for image validation
const fileFilter = (req, file, cb) => {
    const allowedTypes = /jpeg|jpg|png/;
    const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
    const mimetype = allowedTypes.test(file.mimetype);

    if (extname && mimetype) {
        return cb(null, true);
    } else {
        return cb(new Error('Only images (jpeg, jpg, png) are allowed'));
    }
};

const upload = multer({ storage, fileFilter }).single('attachment');

// Submit Inquiry
export const submitInquiry = async (req, res) => {
    upload(req, res, async function (err) {
        if (err) {
            return res.status(500).json({ message: "File upload failed", error: err.message });
        }

        try {
            const { fullName, email, contactNumber, inquiryType, productName, additionalDetails, userApproval, inquirySubject } = req.body;
            
            if (!req.user || !req.user.id) {
                return res.status(401).json({ message: "Unauthorized: User ID missing" });
            }

            if (!fullName || !email || !contactNumber || !inquiryType || !additionalDetails || !inquirySubject) {
                return res.status(400).json({ message: "All required fields must be filled." });
            }

            // Check for existing similar inquiries
            const existingInquiry = await Inquiry.findOne({
                additionalDetails: { $regex: additionalDetails, $options: "i" },
            }).maxTimeMS(5000);

            if (existingInquiry) {
                return res.status(409).json({
                    message: "A similar inquiry already exists.",
                    existingInquiry
                });
            }

            // Handle file upload
            let filePath = req.file ? `/uploads/inquiries/${req.file.filename}` : null;
            
            // Create and save the new inquiry
            const newInquiry = new Inquiry({
                userId: req.user.id,
                fullName,
                email,
                contactNumber,
                inquiryType,
                productName,
                inquirySubject,
                additionalDetails,
                userApproval: userApproval === "true" || userApproval === true,
                attachment: filePath // Store file path in the database
            });

            await newInquiry.save({maxTimeMS: 5000});

            // Fetch FAQs (handle errors separately)
            let relatedFAQs = [];
            try {
                relatedFAQs = await FAQ.find().maxTimeMS(5000);
            } catch (faqError) {
                console.error("Error fetching FAQs:", faqError);
            }

            // Send confirmation email
            const htmlContent = inquiryTemplate(fullName, inquiryType, productName, additionalDetails);
            await sendEmail(email, 'Inquiry Submitted', htmlContent);

            res.status(201).json({ 
                message: "Inquiry submitted successfully and check your email", 
                relatedFAQs,
                inquiry: newInquiry // Send the inquiry details back for download
            });

        } catch (error) {
            console.error("Inquiry submission error:", {
                name: error.name,
                message: error.message,
                stack: error.stack
            });

            if (error.name === 'MongoServerError') {
                return res.status(503).json({ message: "Database operation timed out" });
            }
            res.status(500).json({ 
                message: "Error processing inquiry",
                error: process.env.NODE_ENV === 'development' ? error.message : undefined
            });
        }
    });
};

//Get user's inquiry
export const getUserInquiries = async (req, res) => {
    try {
        // Add query timeout and lean for performance
        const inquiries = await Inquiry.find({ userId: req.user.id })
            .maxTimeMS(5000)
            .lean()
            .sort({ createdAt: -1 }); // Newest first

        if (!inquiries || inquiries.length === 0) {
            return res.status(200).json([]); // Return empty array instead of 404
        }
        res.status(200).json(inquiries);

    } catch (error) {
        console.error("Inquiry Fetch Error:", {
            userId: req.user?.id,
            error: error.name,
            message: error.message,
            stack: error.stack
        });

        if (error.name === 'MongoServerError') {
            return res.status(503).json({ 
                message: "Database operation timed out",
                suggestion: "Please try again in a moment"
            });
        }
        res.status(500).json({ 
            message: "Error fetching inquiries",
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        });
    }
};

//Update User Inquiry within 24 hours
export const updateInquiry = async(req, res) => {
    try{
        const inquiry = await Inquiry.findById(req.params.id)
            .maxTimeMS(5000);

        if(!inquiry){
            return res.status(404).json({message: "Inquiry not found"});
        }

        //Check whether user is loggin or not
        if(inquiry.userId.toString() !== req.user.id){
            return res.status(403).json({message: "Unauthorized"});
        }

        //Check how many hours passed after created the inquiry (It should be less that 24 hours)
        const hoursSinceCreated = (Date.now() - inquiry.createdAt) / (1000 * 60 * 60);
        if(hoursSinceCreated > 24){
            return res.status(400).json({message: "Inquiries can only be updated within 24 hours"});
        }

        inquiry.additionalDetails = req.body.additionalDetails || inquiry.additionalDetails;
        inquiry.inquirySubject = req.body.inquirySubject || inquiry.inquirySubject;
        await inquiry.save({ maxTimeMS: 5000});

        res.status(200).json({message: "Inquiry updated successfully"});
    }catch(error){
        res.status(500).json({message:"Error in updating inquiry", error: error.message});
    }
};

//Delete user inquiry (within 24 hours)
export const deleteInquiry = async(req, res) => {
    try{
        const inquiry = await Inquiry.findById(req.params.id)
            .maxTimeMS(5000);

        if(!inquiry){
            return res.status(404).json({message: "Inquiry not found"});
        }

        if(inquiry.userId.toString() !== req.user.id){
            return res.status(403).json({message: "unauthorized"});
        }

        const hoursSinceCreated = (Date.now() - inquiry.createdAt) / (1000 * 60 * 60);
        if(hoursSinceCreated > 24){
            return res.status(400).json({message: "Inquiries can only be deleted within 24 hours"});
        }

        await inquiry.deleteOne({ maxTimeMS: 5000 });
        res.status(200).json({message: "Inquiry deleted successfully"});
    }catch(error){
        res.status(500).json({message:"Error in deleting inquiry", error: error.message});
    }
};

// Get all inquiries with categorization
export const getAllInquiries = async (req, res) => {
    try {
        const inquiries = await Inquiry.find()
            .populate('userId', 'fullName email')
            .select('fullName email contactNumber productName inquirySubject additionalDetails inquiryType status attachment userApproval');

        const categorizedInquiries = {
            General: inquiries.filter(inq => inq.inquiryType === 'General'),
            ProductAvailability: inquiries.filter(inq => inq.inquiryType === 'Product Availability'),
            Support: inquiries.filter(inq => inq.inquiryType === 'Support')
        };

        res.status(200).json({ inquiries, categorizedInquiries });
    } catch (error) {
        res.status(500).json({ message: "Error in getting all inquiries", error: error.message });
    }
};

// Admin: Mark Inquiry as Resolved and Option to Add to FAQ
export const resolveInquiry = async (req, res) => {
    try {
        const inquiry = await Inquiry.findById(req.params.id);

        if (!inquiry) {
            return res.status(404).json({ message: "Inquiry not found" });
        }

        inquiry.status = 'Resolved';
        if (!inquiry.resolvedAt) {
            inquiry.resolvedAt = new Date();
        }

        await inquiry.save();

        res.status(200).json({ message: "Inquiry marked as resolved and user notified", inquiry  });
    } catch (error) {
        res.status(500).json({ message: "Error in updating status", error: error.message });
    }
};

// Admin: Add Inquiry as FAQ
export const addToFAQ = async (req, res) => {
    try {
        const { id: inquiryId } = req.params; // Get inquiryId from req.params
        const { userApproval, answer } = req.body; //Get userApproval from req.body

        if (!inquiryId) {
            return res.status(400).json({ message: "Inquiry ID is required." });
        }

        const inquiry = await Inquiry.findById(inquiryId);

        if (!inquiry) {
            return res.status(404).json({ message: "Inquiry not found" });
        }

        if (inquiry.status !== 'Resolved') {
            return res.status(400).json({ message: "Only resolved inquiries can be added to FAQs" });
        }

        if (!userApproval) {
            return res.status(400).json({ message: "User has not approved adding this inquiry to FAQ" });
        }

        if (!answer || !answer.trim()) {
            return res.status(400).json({ message: "Answer is required to add to FAQ" });
        }

        inquiry.adminAnswer = answer;
        await inquiry.save();

        const newFAQ = new FAQ({
            question: inquiry.inquirySubject || "No inquiry subject provided.",  //Prevent null/undefined
            answer: inquiry.adminAnswer,
            category: inquiry.inquiryType
        });

        const savedFAQ = await newFAQ.save();

        res.status(201).json({ message: "Inquiry added to FAQ successfully" });
    } catch (error) {
        console.log("Error adding inquiry to FAQ:", error.message);
        res.status(500).json({ message: "Error in adding inquiry to FAQ", error: error.message });
    }
};

// Admin: Delete resolved inquiry after 48 hours
export const deleteResolvedInquiry = async (req, res) => {
    try {
        const inquiry = await Inquiry.findById(req.params.id);

        if (!inquiry) {
            return res.status(404).json({ message: "Inquiry not found" });
        }

        if (inquiry.status !== "Resolved") {
            return res.status(400).json({ message: "Only resolved inquiries can be marked for deletion" });
        }

        // Store the resolved timestamp if not already set
        if (!inquiry.resolvedAt) {
            inquiry.resolvedAt = new Date();
            await inquiry.save();
        }

        res.status(200).json({ message: "Inquiry marked as resolved. Auto-delete countdown started." });
    } catch (error) {
        res.status(500).json({ message: "Error in deleting resolved inquiry", error: error.message });
    }
};

// Scheduled job to run every minute and delete resolved inquiries older than 48 hours
cron.schedule("* * * * *", async () => { 
    try {
        const now = new Date();
        const cutoffTime = new Date(now.getTime() - 48 * 60 * 60 * 1000); 
        
        const deletedInquiries = await Inquiry.deleteMany({
            status: "Resolved",
            resolvedAt: { $lte: cutoffTime }
        });

        if (deletedInquiries.deletedCount > 0) {
            console.log(`${deletedInquiries.deletedCount} resolved inquiries deleted.`);
        }
    } catch (error) {
        console.error("Error in scheduled deletion:", error);
    }
});


