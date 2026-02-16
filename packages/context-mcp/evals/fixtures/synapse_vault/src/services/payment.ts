import Stripe from 'stripe';
import { PayPalClient } from '../providers/paypal';

interface ChargeInput {
  amount: number;
  currency: string;
  provider: 'stripe' | 'paypal';
  paymentMethodId?: string;
  userId: string;
}

interface RefundInput {
  chargeId: string;
  amount?: number;
  reason?: string;
}

interface HistoryInput {
  userId: string;
  cursor?: string;
  limit: number;
}

/**
 * Payment service handling multi-provider payment processing.
 * Supports Stripe and PayPal.
 */
export class PaymentService {
  private static stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);
  private static paypal = new PayPalClient(process.env.PAYPAL_CLIENT_ID!, process.env.PAYPAL_SECRET!);

  static async charge(input: ChargeInput) {
    if (input.provider === 'stripe') {
      return this.chargeStripe(input);
    } else {
      return this.chargePayPal(input);
    }
  }

  private static async chargeStripe(input: ChargeInput) {
    const paymentIntent = await this.stripe.paymentIntents.create({
      amount: input.amount,
      currency: input.currency,
      payment_method: input.paymentMethodId,
      confirm: true,
      metadata: { userId: input.userId },
    });
    return {
      id: paymentIntent.id,
      status: paymentIntent.status,
      provider: 'stripe',
    };
  }

  private static async chargePayPal(input: ChargeInput) {
    const order = await this.paypal.createOrder({
      amount: input.amount,
      currency: input.currency,
      userId: input.userId,
    });
    return {
      id: order.id,
      status: order.status,
      provider: 'paypal',
    };
  }

  static async refund(input: RefundInput) {
    // Determine provider from charge ID prefix
    if (input.chargeId.startsWith('pi_')) {
      return this.refundStripe(input);
    } else {
      return this.refundPayPal(input);
    }
  }

  private static async refundStripe(input: RefundInput) {
    const refund = await this.stripe.refunds.create({
      payment_intent: input.chargeId,
      amount: input.amount,
      reason: input.reason as Stripe.RefundCreateParams.Reason,
    });
    return { id: refund.id, status: refund.status, provider: 'stripe' };
  }

  private static async refundPayPal(input: RefundInput) {
    const refund = await this.paypal.refundOrder({
      orderId: input.chargeId,
      amount: input.amount,
      reason: input.reason,
    });
    return { id: refund.id, status: refund.status, provider: 'paypal' };
  }

  static async getHistory(input: HistoryInput) {
    // Aggregate from both providers
    const [stripeCharges, paypalOrders] = await Promise.all([
      this.stripe.paymentIntents.list({
        customer: input.userId,
        limit: input.limit,
        starting_after: input.cursor,
      }),
      this.paypal.listOrders({
        userId: input.userId,
        limit: input.limit,
        cursor: input.cursor,
      }),
    ]);

    // Merge and sort by date
    const combined = [
      ...stripeCharges.data.map(c => ({ ...c, provider: 'stripe' })),
      ...paypalOrders.data.map(o => ({ ...o, provider: 'paypal' })),
    ].sort((a, b) => (b as any).created - (a as any).created);

    return {
      data: combined.slice(0, input.limit),
      hasMore: stripeCharges.has_more || paypalOrders.hasMore,
    };
  }
}
