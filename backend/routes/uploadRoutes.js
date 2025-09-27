import express from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import { uploadImage } from "../controller/uploadController.js";

const router = express.Router();

// Create uploads directory if not exists
const uploadsDir = path.join(process.cwd(), "uploads");
if (!fs.existsSync(uploadsDir)) {
    fs.mkdirSync(uploadsDir);
}

// Configure Multer for file uploads
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, uploadsDir); // Save files in "uploads" folder
    },
    filename: (req, file, cb) => {
        cb(null, `${Date.now()}-${file.originalname}`);
    },
});

const upload = multer({ storage });

// POST route for file upload
router.post("/uploadImage", upload.single("image"), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ message: "No file uploaded" });
    }
    
    // Send file path as response
    res.json({ imageUrl: `/uploads/${req.file.filename}` });
});

/**
 * 
 * Product management AI
 * 
 * 
 */

const aiProductFolder = path.join("uploads", "ai_products");
if (!fs.existsSync(aiProductFolder)) fs.mkdirSync(aiProductFolder, { recursive: true });

// Set multer storage
const ai_storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, aiProductFolder),
  filename: (req, file, cb) => cb(null, `${Date.now()}_${file.originalname}`),
});

const ai_upload = multer({ ai_storage });

router.post("/upload", ai_upload.single("file"), uploadImage);


export default router;
