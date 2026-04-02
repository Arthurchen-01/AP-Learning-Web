export type UserRole = "student" | "teacher";

export type Database = {
  public: {
    Tables: {
      student_profiles: {
        Row: {
          id: string;
          role: UserRole;
          grade_level: string | null;
          target_college: string | null;
          created_at: string;
        };
        Insert: {
          id: string;
          role: UserRole;
          grade_level?: string | null;
          target_college?: string | null;
        };
        Update: Partial<{
          role: UserRole;
          grade_level: string | null;
          target_college: string | null;
        }>;
      };
    };
  };
};
