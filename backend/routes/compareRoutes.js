import express from "express";
import { compareProducts } from "../controller/compareController.js";

const router = express.Router();

router.post("/compare", compareProducts);

export default router;
