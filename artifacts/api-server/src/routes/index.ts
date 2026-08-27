import { Router, type IRouter } from "express";
import healthRouter from "./health";
import commerceRouter from "./commerce";
import telegramRouter from "./telegram";

const router: IRouter = Router();

router.use(healthRouter);
router.use(commerceRouter);
router.use(telegramRouter);

export default router;
