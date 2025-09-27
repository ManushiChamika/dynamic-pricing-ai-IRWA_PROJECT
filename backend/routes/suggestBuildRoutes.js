// routes/suggestBuildRoutes.js
import express from "express";
import { suggestBuild } from "../controller/suggestBuildController.js";

const router = express.Router();

router.post("/suggest-build", suggestBuild);

export default router;
