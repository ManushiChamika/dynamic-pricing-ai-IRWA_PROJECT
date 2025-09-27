import express from 'express';
import { addToFAQ, deleteInquiry, deleteResolvedInquiry, getAllInquiries, getUserInquiries,resolveInquiry, submitInquiry, updateInquiry } from '../controller/inquiryController.js';
import authMiddleware from '../middleware/authMiddleware.js';

const router = express.Router();

//User Routes
router.post('/submit', 
    (req, res, next) => {
        next();
    },
    authMiddleware(),
    (req, res, next) => {
        next();
    },
    submitInquiry
);

router.get('/my-inquiry', 
    (req, res, next) => {
        next();
    },
    authMiddleware(),
    (req, res, next) => {
        next();
    },
    getUserInquiries
);

router.put('/update-inquiry/:id', 
    (req, res, next) => {
        next();
      },
      authMiddleware(),
      (req, res, next) => {
        next();
      },
       updateInquiry);

router.delete('/delete-inquiry/:id', 
    (req, res, next) => {
        next();
    },
    authMiddleware(),
    (req, res, next) => {
        next();
    },
    deleteInquiry
);

//Admin Routes
router.get('/all-inquiries', getAllInquiries);
router.put('/resolve/:id', resolveInquiry);
router.post('/add-to-faq/:id', addToFAQ)
router.delete('/delete-resolved/:id', deleteResolvedInquiry);

export default router;