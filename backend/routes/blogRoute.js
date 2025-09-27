import express from 'express';
import { addBlog, deleteBlog, getallBlogs, getBlogsById, updateBlog } from "../controller/blogController.js";

const router = express.Router();

router.post("/addBlog", addBlog);
router.get("/allBlogs", getallBlogs);
router.get("/allBlogs/:id", getBlogsById);
router.put("/allBlogs/:id", updateBlog);
router.delete("/allBlogs/:id", deleteBlog);

export default router;