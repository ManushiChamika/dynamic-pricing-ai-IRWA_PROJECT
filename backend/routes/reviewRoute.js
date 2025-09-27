import express from "express";
import { approvedReviews, deleteReview, getAllReviews, getUserReviews, moderateReview, submitReview, updateReview } from '../controller/reviewController.js';
import authMiddleware from '../middleware/authMiddleware.js';

const router = express.Router();

router.post('/submit', 
    (req, res, next) => {
        next();
    },
    authMiddleware(),
    (req, res, next) => {
        next();
    },
    submitReview
);

router.get('/user-review', 
    (req, res, next) => {
      next();
    },
    authMiddleware(),
    (req, res, next) => {
      next();
    },
    getUserReviews
  );
  
  router.put('/update/:id', 
    (req, res, next) => {
      next();
    },
    authMiddleware(),
    (req, res, next) => {
      next();
    },
    updateReview
  );

router.delete('/delete/:id', 
  (req, res, next) => {
    next();
  },
  authMiddleware(),
  (req, res, next) => {
    next();
  },
  deleteReview
);

router.get('/all-reviews', getAllReviews)
router.get('/approved', approvedReviews);
router.put('/moderate/:id', moderateReview);

export default router;