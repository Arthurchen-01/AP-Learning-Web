import { signOut } from "@/app/(auth)/actions";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user }
  } = await supabase.auth.getUser();

  if (!user) return null;

  const { data: profile } = await supabase
    .from("student_profiles")
    .select("role, grade_level, target_college")
    .eq("id", user.id)
    .maybeSingle();

  return (
    <main className="container">
      <section className="card">
        <h1>Dashboard</h1>
        <p>Logged in as: {user.email}</p>
        <p>Role: {profile?.role ?? user.user_metadata.role ?? "student"}</p>
        <p>Module 1 complete: auth with Supabase (email/password + Google).</p>
        <form action={signOut}>
          <button type="submit">Sign out</button>
        </form>
      </section>
    </main>
  );
}
