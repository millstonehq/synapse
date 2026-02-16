export const config = {
  port: parseInt(process.env.PORT || '3000', 10),

  database: {
    uri: process.env.DATABASE_URL || 'mongodb://localhost:27017/payments',
    poolSize: 10,
  },

  stripe: {
    secretKey: process.env.STRIPE_SECRET_KEY || '',
    webhookSecret: process.env.STRIPE_WEBHOOK_SECRET || '',
  },

  paypal: {
    clientId: process.env.PAYPAL_CLIENT_ID || '',
    secret: process.env.PAYPAL_SECRET || '',
    sandbox: process.env.NODE_ENV !== 'production',
  },

  rateLimit: {
    windowMs: 15 * 60 * 1000,
    max: 200,
  },

  cors: {
    origin: process.env.CORS_ORIGIN || 'http://localhost:3001',
    credentials: true,
  },
};
