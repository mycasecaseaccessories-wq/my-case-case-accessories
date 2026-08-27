import { Router, type IRouter, type Request, type Response } from "express";
import { HealthCheckResponse } from "@workspace/api-zod";

const router: IRouter = Router();

function healthResponse(_req: Request, res: Response) {
  const data = HealthCheckResponse.parse({ status: "ok" });
  res.json(data);
}

router.get("/healthz", healthResponse);
router.get("/v1/healthz", healthResponse);

export default router;
