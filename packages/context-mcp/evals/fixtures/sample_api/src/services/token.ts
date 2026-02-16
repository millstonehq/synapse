import jwt from 'jsonwebtoken';
import { IUser } from '../models/user';
import { config } from '../config';
import { TokenPayload } from '../types/auth';

/**
 * Service for generating and verifying JWT tokens
 */
export class TokenService {
  /**
   * Generate an access token for a user
   * @param user - The user to generate token for
   * @returns JWT access token
   */
  static generateToken(user: IUser): string {
    const payload: TokenPayload = {
      userId: user.id,
      email: user.email,
      role: user.role,
    };

    return jwt.sign(payload, config.jwt.secret, {
      expiresIn: config.jwt.accessTokenExpiry,
      issuer: config.jwt.issuer,
    });
  }

  /**
   * Generate a refresh token for a user
   * @param user - The user to generate token for
   * @returns JWT refresh token
   */
  static generateRefreshToken(user: IUser): string {
    const payload = {
      userId: user.id,
      type: 'refresh',
    };

    return jwt.sign(payload, config.jwt.refreshSecret, {
      expiresIn: config.jwt.refreshTokenExpiry,
      issuer: config.jwt.issuer,
    });
  }

  /**
   * Verify an access token
   * @param token - JWT token to verify
   * @returns Decoded payload or null if invalid
   */
  static verifyToken(token: string): TokenPayload | null {
    try {
      const decoded = jwt.verify(token, config.jwt.secret, {
        issuer: config.jwt.issuer,
      }) as TokenPayload;
      return decoded;
    } catch (error) {
      return null;
    }
  }

  /**
   * Verify a refresh token
   * @param token - JWT refresh token to verify
   * @returns Decoded payload or null if invalid
   */
  static verifyRefreshToken(token: string): { userId: string } | null {
    try {
      const decoded = jwt.verify(token, config.jwt.refreshSecret, {
        issuer: config.jwt.issuer,
      }) as { userId: string; type: string };

      if (decoded.type !== 'refresh') {
        return null;
      }

      return { userId: decoded.userId };
    } catch (error) {
      return null;
    }
  }

  /**
   * Decode a token without verification (for debugging)
   * @param token - JWT token to decode
   * @returns Decoded payload or null
   */
  static decodeToken(token: string): TokenPayload | null {
    try {
      return jwt.decode(token) as TokenPayload;
    } catch {
      return null;
    }
  }
}
