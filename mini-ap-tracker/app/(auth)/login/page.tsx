import Link from "next/link";
import { signInWithGoogle, signInWithPassword } from "../actions";

export default function LoginPage() {
  return (
    <main className="container">
      <section className="card" style={{ maxWidth: 460, margin: "0 auto" }}>
        <h1>Login</h1>
        <form action={signInWithPassword}>
          <label>
            Email
            <input type="email" name="email" required />
          </label>
          <label>
            Password
            <input type="password" name="password" required minLength={6} />
          </label>
          <button type="submit">Sign in</button>
        </form>
        <form action={signInWithGoogle}>
          <button className="secondary" type="submit" style={{ marginTop: "0.75rem" }}>
            Continue with Google
          </button>
        </form>
        <p>
          New user? <Link href="/register">Create account</Link>
        </p>
      </section>
    </main>
  );
}
