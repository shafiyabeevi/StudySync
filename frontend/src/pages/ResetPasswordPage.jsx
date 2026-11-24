import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function ResetPasswordPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const { error: authError } = await supabase.auth.updateUser({ password });
      if (authError) throw authError;
      navigate('/', { replace: true });
    } catch (authError) {
      setError(authError.message || 'Unable to update your password. Open the latest reset link and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="glass-panel w-full max-w-md p-8">
        <h1 className="text-2xl font-bold text-white">Choose a new password</h1>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <label className="block text-sm text-gray-300">
            New password
            <input
              type="password"
              autoComplete="new-password"
              minLength={6}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-primary"
            />
          </label>
          {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
          <button disabled={submitting} className="w-full rounded-lg bg-primary px-4 py-2.5 font-medium text-white disabled:opacity-60">
            {submitting ? 'Saving…' : 'Update password'}
          </button>
        </form>
        <p className="mt-6 text-sm text-gray-400"><Link className="text-primary hover:underline" to="/login">Back to login</Link></p>
      </div>
    </main>
  );
}
