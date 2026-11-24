import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { BookOpen, Loader2 } from 'lucide-react';
import { useAuth } from '../auth/AuthContext';
import { supabase } from '../lib/supabase';

export default function AuthPage({ mode }) {
  const isSignup = mode === 'signup';
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const { session } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  if (session) return <Navigate to="/" replace />;

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setMessage('');
    setSubmitting(true);

    try {
      if (isSignup) {
        const { data, error: authError } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: { emailRedirectTo: `${window.location.origin}/login` },
        });
        if (authError) throw authError;
        if (data.session) {
          navigate('/', { replace: true });
        } else {
          setMessage('Check your email to confirm your account, then log in.');
        }
      } else {
        const { error: authError } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });
        if (authError) throw authError;
        navigate(location.state?.from?.pathname || '/', { replace: true });
      }
    } catch (authError) {
      setError(authError.message || 'Authentication failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="glass-panel w-full max-w-md p-8">
        <div className="mb-7 flex flex-col items-center text-center">
          <div className="mb-3 rounded-xl bg-primary/20 p-3"><BookOpen className="h-7 w-7 text-primary" /></div>
          <h1 className="text-2xl font-bold text-white">Study<span className="text-primary">Sync</span></h1>
          <p className="mt-2 text-sm text-gray-400">{isSignup ? 'Create your account' : 'Welcome back'}</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
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
          <label className="block text-sm text-gray-300">
            Password
            <input
              type="password"
              autoComplete={isSignup ? 'new-password' : 'current-password'}
              minLength={6}
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-1 w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2.5 text-white outline-none focus:border-primary"
            />
          </label>

          {error && <p role="alert" className="text-sm text-red-400">{error}</p>}
          {message && <p role="status" className="text-sm text-green-500">{message}</p>}

          <button
            type="submit"
            disabled={submitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 font-medium text-white transition hover:bg-primary/90 disabled:opacity-60"
          >
            {submitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSignup ? 'Create account' : 'Log in'}
          </button>
        </form>

        {!isSignup && <p className="mt-4 text-center text-sm"><Link className="text-primary hover:underline" to="/forgot-password">Forgot your password?</Link></p>}
        <p className="mt-6 text-center text-sm text-gray-400">
          {isSignup ? 'Already have an account? ' : 'New to StudySync? '}
          <Link className="text-primary hover:underline" to={isSignup ? '/login' : '/signup'}>
            {isSignup ? 'Log in' : 'Create an account'}
          </Link>
        </p>
      </div>
    </main>
  );
}
