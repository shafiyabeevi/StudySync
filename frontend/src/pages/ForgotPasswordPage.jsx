import { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const { error: authError } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      if (authError) throw authError;
      setSent(true);
    } catch (authError) {
      setError(authError.message || 'Unable to send a password reset email.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="glass-panel w-full max-w-md p-8">
        <h1 className="text-2xl font-bold text-white">Reset your password</h1>
        <p className="mt-2 text-sm text-gray-400">We’ll email you a secure password-reset link.</p>
        {sent ? (
          <p role="status" className="mt-6 text-sm text-green-500">If an account exists for that email, a reset link has been sent.</p>
        ) : (
          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block text-sm text-gray-300">
              Email
              <input
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-primary"
              />
            </label>
            {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
            <button disabled={submitting} className="w-full rounded-lg bg-primary px-4 py-2.5 font-medium text-white disabled:opacity-60">
              {submitting ? 'Sending…' : 'Send reset link'}
            </button>
          </form>
        )}
        <p className="mt-6 text-sm text-gray-400"><Link className="text-primary hover:underline" to="/login">Back to login</Link></p>
      </div>
    </main>
  );
}
