import { User, IUser } from '../models/user';

interface CreateUserInput {
  email: string;
  password: string;
  name: string;
}

/**
 * Service for user operations
 */
export class UserService {
  static async findById(id: string): Promise<IUser | null> {
    return User.findById(id);
  }

  static async findByEmail(email: string): Promise<IUser | null> {
    return User.findOne({ email: email.toLowerCase() });
  }

  static async create(input: CreateUserInput): Promise<IUser> {
    const user = new User({
      email: input.email.toLowerCase(),
      password: input.password,
      name: input.name,
    });
    return user.save();
  }

  static async verifyPassword(user: IUser, password: string): Promise<boolean> {
    return user.comparePassword(password);
  }

  static async updateLastLogin(userId: string): Promise<void> {
    await User.findByIdAndUpdate(userId, { lastLoginAt: new Date() });
  }

  static async deactivate(userId: string): Promise<void> {
    await User.findByIdAndUpdate(userId, { isActive: false });
  }
}
