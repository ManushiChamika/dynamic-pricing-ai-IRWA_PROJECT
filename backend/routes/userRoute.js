import express from 'express';
import { changePassword, deleteUser, updateUser, verifyDetails, verifyDetailsReveiws, getUsers } from '../controller/userController.js';
import authMiddleware from '../middleware/authMiddleware.js';

const router = express.Router();

router.put('/update',
    (req, res, next) => {
        next();
    },
    authMiddleware(), 
    (req, res, next) => {
        next();
    },
    updateUser);

router.put('/change-password', 
    (req, res, next) => {
        next();
    },
    authMiddleware(), 
    (req, res, next) => {
        next();
    },
    changePassword);

router.delete('/delete',
    (req, res, next) => {
        next();
    },
    authMiddleware(), 
    (req, res, next) => {
        next();
    }, 
    deleteUser);

router.post('/verify-details', authMiddleware, verifyDetails);
router.post('/verify-details-review', authMiddleware, verifyDetailsReveiws);
router.get('/get-all-users', getUsers);


export default router;