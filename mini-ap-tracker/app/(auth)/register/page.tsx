import Link from "next/link";
import { signInWithGoogle, signUpWithPassword } from "../actions";

export default function RegisterPage() {
  return (
    <main className="container">
      <section className="card" style={{ maxWidth: 460, margin: "0 auto" }}>
        <h1>Create account</h1>
        <form action={signUpWithPassword}>
          <label>
            Email
            <input type="email" name="email" required />
          </label>
          <label>
            Password
            <input type="password" name="password" required minLength={6} />
          </label>
          <label>
            Role
            <select name="role" defaultValue="student">
              <option value="student">Student</option>
              <option value="teacher">Teacher</option>
            </select>
          </label>
          <button type="submit">Sign up</button>
        </form>
        <form action={signInWithGoogle}>
          <button className="secondary" type="submit" style={{ marginTop: "0.75rem" }}>
            Sign up with Google
          </button>
        </form>
        <p>
          Already have an account? <Link href="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}
