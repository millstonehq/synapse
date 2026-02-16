import { Router, Request, Response } from 'express';
import { PaymentService } from '../services/payment';
import { authenticate } from '../middleware/auth';

const router = Router();

/**
 * POST /payments/charge
 * Process a payment charge.
 * Updated: now supports both Stripe and PayPal providers.
 */
router.post('/charge', authenticate(), async (req: Request, res: Response) => {
  const { amount, currency, provider, paymentMethodId } = req.body;

  if (!amount || !currency || !provider) {
    return res.status(400).json({ error: 'amount, currency, and provider are required' });
  }

  if (!['stripe', 'paypal'].includes(provider)) {
    return res.status(400).json({ error: 'provider must be stripe or paypal' });
  }

  try {
    const result = await PaymentService.charge({
      amount,
      currency,
      provider,
      paymentMethodId,
      userId: req.user.id,
    });
    return res.json(result);
  } catch (error) {
    return res.status(500).json({ error: 'Payment processing failed' });
  }
});

/**
 * POST /payments/refund
 * Process a refund. Supports partial refunds.
 */
router.post('/refund', authenticate(), async (req: Request, res: Response) => {
  const { chargeId, amount, reason } = req.body;

  if (!chargeId) {
    return res.status(400).json({ error: 'chargeId is required' });
  }

  try {
    const result = await PaymentService.refund({ chargeId, amount, reason });
    return res.json(result);
  } catch (error) {
    return res.status(500).json({ error: 'Refund processing failed' });
  }
});

/**
 * GET /payments/history
 * Get payment history for the authenticated user.
 * Supports pagination with cursor-based pagination.
 */
router.get('/history', authenticate(), async (req: Request, res: Response) => {
  const { cursor, limit = '20' } = req.query;

  const history = await PaymentService.getHistory({
    userId: req.user.id,
    cursor: cursor as string,
    limit: parseInt(limit as string, 10),
  });

  return res.json(history);
});

export default router;
