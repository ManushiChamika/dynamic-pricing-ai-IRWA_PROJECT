import express from 'express';
import {getChatResponse} from '../controller/chatbotController.js';

const router = express.Router();

router.post('/chat', getChatResponse);

export default router;
