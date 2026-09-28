import { useState } from 'react';
import { Shield, ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authApi } from '../services/sentinelApi';

export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('admin@sentinel.ai');
  const [password, setPassword] = useState('AdminPassword123!');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await authApi.login(email, password);
      login(res.access_token, res.user);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Invalid surveillance operator credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (roleEmail: string, rolePass: string) => {
    setEmail(roleEmail);
    setPassword(rolePass);
  };

  return (
    <div className="min-h-screen bg-[#F6F5FA] flex items-center justify-center p-4 tactical-dots-light select-none">
      <div className="w-full max-w-md bg-white border border-[#E5E1EE] rounded-2xl shadow-xl p-8 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 rounded-2xl bg-[#F0EDFD] border border-[#DCD4FB] flex items-center justify-center text-[#7C5CFC] mx-auto shadow-xs">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-extrabold text-[#211D2B] tracking-tight">
            SENTINEL COMMAND
          </h1>
          <p className="text-xs text-[#625D6D] font-medium">
            AI-Based Video Analytics Platform for Border Surveillance
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {error && (
            <div className="p-3 rounded-lg bg-[#FEE2E2] border border-[#FCA5A5] text-[#B91C1C] font-semibold text-xs text-center">
              {error}
            </div>
          )}

          <div className="space-y-1.5">
            <label className="text-[#8E8899] font-bold uppercase tracking-wider">OPERATOR EMAIL</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="commander@sentinel.ai"
                className="w-full px-4 py-3 bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-[#8E8899] font-bold uppercase tracking-wider">SECURITY PASSCODE</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full px-4 py-3 bg-[#FAF9FD] border border-[#E5E1EE] rounded-xl text-[#211D2B] text-sm focus:outline-none focus:border-[#7C5CFC]"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-[#7C5CFC] hover:bg-[#6A46F9] text-white font-bold text-sm flex items-center justify-center space-x-2 transition shadow-xs disabled:opacity-50"
          >
            <span>{loading ? 'Authenticating Operator...' : 'Sign In to Command Console'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Quick Role Selection */}
        <div className="pt-4 border-t border-[#E5E1EE] space-y-2.5">
          <div className="text-xs text-[#8E8899] font-bold uppercase text-center tracking-wider">
            DEMO WORKSTATION PROFILES
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin@sentinel.ai', 'AdminPassword123!')}
              className="p-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] hover:border-[#DCD4FB] text-xs font-bold text-[#4328A8] transition text-center"
            >
              Commander
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('analyst@sentinel.ai', 'AnalystPassword123!')}
              className="p-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] hover:border-[#DCD4FB] text-xs font-bold text-[#4328A8] transition text-center"
            >
              AI Analyst
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('operator@sentinel.ai', 'OperatorPassword123!')}
              className="p-2.5 rounded-lg bg-[#FAF9FD] hover:bg-[#F0EDFD] border border-[#E5E1EE] hover:border-[#DCD4FB] text-xs font-bold text-[#4328A8] transition text-center"
            >
              Field Guard
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
