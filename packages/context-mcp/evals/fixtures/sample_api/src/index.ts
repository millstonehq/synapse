import express from 'express';
import cors from 'cors';
import mongoose from 'mongoose';
import authRoutes from './routes/auth';
import { authenticate } from './middleware/auth';
import { config } from './config';

const app = express();

// Middleware
app.use(cors(config.cors));
app.use(express.json());

// Routes
app.use('/auth', authRoutes);

// Protected route example
app.get('/api/me', authenticate, (req, res) => {
  res.json({ user: req.user });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Connect to database and start server
async function start() {
  try {
    await mongoose.connect(config.database.uri);
    console.log('Connected to MongoDB');

    app.listen(config.port, () => {
      console.log(`Server running on port ${config.port}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
}

start();

export default app;
