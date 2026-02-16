import { Router, Request, Response } from 'express';
import { UserService } from '../services/user';
import { TokenService } from '../services/token';
import { validateLoginInput } from '../middleware/validation';

const router = Router();

/**
 * POST /auth/login
 * Authenticate user with email/password and return JWT token
 */
router.post('/login', validateLoginInput, async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    const user = await UserService.findByEmail(email);
    if (!user) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const isValid = await UserService.verifyPassword(user, password);
    if (!isValid) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const token = TokenService.generateToken(user);
    const refreshToken = TokenService.generateRefreshToken(user);

    res.json({
      token,
      refreshToken,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /auth/register
 * Create new user account
 */
router.post('/register', async (req: Request, res: Response) => {
  try {
    const { email, password, name } = req.body;

    const existingUser = await UserService.findByEmail(email);
    if (existingUser) {
      return res.status(400).json({ error: 'Email already registered' });
    }

    const user = await UserService.create({ email, password, name });
    const token = TokenService.generateToken(user);

    res.status(201).json({
      token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name,
      },
    });
  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /auth/refresh
 * Refresh JWT token using refresh token
 */
router.post('/refresh', async (req: Request, res: Response) => {
  try {
    const { refreshToken } = req.body;

    const payload = TokenService.verifyRefreshToken(refreshToken);
    if (!payload) {
      return res.status(401).json({ error: 'Invalid refresh token' });
    }

    const user = await UserService.findById(payload.userId);
    if (!user) {
      return res.status(401).json({ error: 'User not found' });
    }

    const token = TokenService.generateToken(user);
    res.json({ token });
  } catch (error) {
    console.error('Token refresh error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

/**
 * POST /auth/logout
 * Invalidate user session
 */
router.post('/logout', async (req: Request, res: Response) => {
  // In a real app, you'd invalidate the token server-side
  res.json({ message: 'Logged out successfully' });
});

export default router;
