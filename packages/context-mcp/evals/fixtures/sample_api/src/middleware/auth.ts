import { Request, Response, NextFunction } from 'express';
import { TokenService } from '../services/token';
import { UserService } from '../services/user';
import { AuthenticatedRequest } from '../types/auth';

/**
 * Middleware to authenticate JWT tokens
 * Attaches user to request if token is valid
 */
export async function authenticate(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      res.status(401).json({ error: 'No token provided' });
      return;
    }

    const token = authHeader.substring(7);
    const payload = TokenService.verifyToken(token);

    if (!payload) {
      res.status(401).json({ error: 'Invalid token' });
      return;
    }

    const user = await UserService.findById(payload.userId);
    if (!user || !user.isActive) {
      res.status(401).json({ error: 'User not found or inactive' });
      return;
    }

    (req as AuthenticatedRequest).user = user;
    next();
  } catch (error) {
    console.error('Authentication error:', error);
    res.status(401).json({ error: 'Authentication failed' });
  }
}

/**
 * Middleware to require admin role
 * Must be used after authenticate middleware
 */
export function requireAdmin(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const authReq = req as AuthenticatedRequest;

  if (!authReq.user) {
    res.status(401).json({ error: 'Not authenticated' });
    return;
  }

  if (authReq.user.role !== 'admin') {
    res.status(403).json({ error: 'Admin access required' });
    return;
  }

  next();
}

/**
 * Optional authentication - doesn't fail if no token
 * Useful for routes that behave differently for authenticated users
 */
export async function optionalAuth(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  try {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const payload = TokenService.verifyToken(token);

      if (payload) {
        const user = await UserService.findById(payload.userId);
        if (user && user.isActive) {
          (req as AuthenticatedRequest).user = user;
        }
      }
    }

    next();
  } catch (error) {
    // Ignore errors for optional auth
    next();
  }
}
