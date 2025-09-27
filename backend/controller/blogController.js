import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import BLOG from "../models/blogModel.js";
import multer from 'multer';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define upload directory
const uploadDir = path.join(__dirname, '../uploads/blogs/');
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

const upload = multer({ storage, fileFilter }).single('image');

export const addBlog = async (req, res) => {
    upload(req, res, async function (err) {
        if (err) {
            if (err instanceof multer.MulterError) {
                return res.status(500).json({ message: "File upload error", error: err.message });
            } else {
                return res.status(400).json({ message: "File validation failed", error: err.message });
            }
        }

        try {
            const { title, content, published } = req.body;
            
            if (!req.file) {
                return res.status(400).json({ message: "Image is required." });
            }

            if (!title || !content || published === undefined) {
                return res.status(400).json({ message: "All fields need to be filled." });
            }

            // Handle file path
            const imagePath = `/uploads/blogs/${req.file.filename}`;
            
            // Create and save the new blog
            const blog = new BLOG({
                title, 
                content, 
                published: published === "true" || published === true,
                image: imagePath
            });

            await blog.save();

            res.status(201).json({ 
                message: "Blog added successfully",
                blog
            });

        } catch (error) {
            console.error("Error in adding a blog:", error);
            
            // Clean up uploaded file if there was an error
            if (req.file) {
                try {
                    fs.unlinkSync(path.join(uploadDir, req.file.filename));
                } catch (cleanupError) {
                    console.error("Error cleaning up uploaded file:", cleanupError);
                }
            }
            
            res.status(500).json({ 
                message: "Error in adding the blog", 
                error: error.message 
            });
        }
    });
};

export const getallBlogs = async(req, res, next) => {
    let allBlogs;
    try{
        allBlogs = await BLOG.find();

        if(!allBlogs){
            return res.status(404).json({message: "Blogs are not found"});
        }
        return res.status(200).json({allBlogs});
    }catch(error){
        console.log("Error in fetching all blogs", error);
        return res.status(500).json({message: "Error in fetchiing blogs"});
    }
};

export const getBlogsById = async(req, res, next) => {
    const id = req.params.id;
    let blogsId;

    try{
        blogsId = await BLOG.findById(id);

        if(!blogsId){
            return res.status(400).json({message: "Blog details not found"});
        }

        return res.status(200).json({blogsId});
    }catch(error){
        console.error(error);
        res.status(500).json({message: "Error in fetching blogs details by ID"});
    }
};

export const updateBlog = async (req, res, next) => {
    upload(req, res, async function (err) {
        if (err) {
            if (err instanceof multer.MulterError) {
                return res.status(500).json({ message: "File upload error", error: err.message });
            } else {
                return res.status(400).json({ message: "File validation failed", error: err.message });
            }
        }

        try {
            const id = req.params.id;
            const { title, content, published } = req.body;

            // Validate required fields
            if (!title || !content || published === undefined) {
                return res.status(400).json({ message: "Title, content and published status are required" });
            }

            // Find the existing blog
            const existingBlog = await BLOG.findById(id);
            if (!existingBlog) {
                return res.status(404).json({ message: "Blog not found" });
            }

            // Prepare update data
            const updateData = {
                title,
                content,
                published: published === "true" || published === true
            };

            // Handle image update if new file was uploaded
            let oldImagePath;
            if (req.file) {
                oldImagePath = existingBlog.image;
                updateData.image = `/uploads/blogs/${req.file.filename}`;
            }

            // Update the blog
            const updatedBlog = await BLOG.findByIdAndUpdate(id, updateData, { new: true });

            if (!updatedBlog) {
                // Clean up newly uploaded file if update failed
                if (req.file) {
                    fs.unlinkSync(path.join(uploadDir, req.file.filename));
                }
                return res.status(404).json({ message: "Blog update failed" });
            }

            // Delete old image if a new one was uploaded
            if (req.file && oldImagePath) {
                try {
                    const oldFilename = oldImagePath.split('/').pop();
                    fs.unlinkSync(path.join(uploadDir, oldFilename));
                } catch (cleanupError) {
                    console.error("Error cleaning up old image:", cleanupError);
                }
            }

            return res.status(200).json({ 
                message: "Blog updated successfully",
                blog: updatedBlog
            });

        } catch (error) {
            console.error("Error updating blog:", error);
            
            // Clean up uploaded file if there was an error
            if (req.file) {
                try {
                    fs.unlinkSync(path.join(uploadDir, req.file.filename));
                } catch (cleanupError) {
                    console.error("Error cleaning up uploaded file:", cleanupError);
                }
            }
            
            res.status(500).json({ 
                message: "Error updating blog", 
                error: error.message 
            });
        }
    });
};

export const deleteBlog = async(req, res, next) => {
    const id =  req.params.id;
    let deleteblogs;

    try{
        deleteblogs = await BLOG.findByIdAndDelete(id);
        if(!deleteblogs){
            return res.status(404).json({ message: "Blog not found" });
        }
        // Clean up image file
        if (deleteblogs.image) {
            const filename = deleteblogs.image.split('/').pop();
            fs.unlinkSync(path.join(uploadDir, filename));
        }
    
        return res.status(200).json({ message: "Blog deleted successfully" });
    }catch(error){
        console.error("Error in deleting blog. ", error);
        return res.status(500).json({ message: "Error deleting blog", error: error.message });
    }
};