import { useEffect, useState } from 'react';
import { apiClient } from '../../lib/api';
import { toast } from 'sonner';

interface LoyaltyStatus { points: number; level: string; points_to_next: number; total_spent: number; badges: string[] }
interface Badge { id: string; name: string; description: string; icon_url: string; unlocked: boolean; unlocked_at: string }
interface Reward { id: string; name: string; description: string; points_cost: number; reward_type: string; limited: boolean; remaining: number }
interface LeaderboardEntry { user_id: string; points: number; level: string; badge_count: number }

export const LoyaltyPage = () => {
  const [status, setStatus] = useState<LoyaltyStatus | null>(null);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [rewards, setRewards] = useState<Reward[]>([]);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'status' | 'badges' | 'rewards' | 'leaderboard'>('status');
  const [redeeming, setRedeeming] = useState<string | null>(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [s, b, r, l] = await Promise.all([
        apiClient.get('/api/marketplace/loyalty/status'),
        apiClient.get('/api/marketplace/loyalty/badges'),
        apiClient.get('/api/marketplace/loyalty/rewards'),
        apiClient.get('/api/marketplace/loyalty/leaderboard'),
      ]);
      setStatus(s);
      setBadges(Array.isArray(b) ? b : b?.badges || []);
      setRewards(Array.isArray(r) ? r : r?.rewards || []);
      setLeaderboard(Array.isArray(l) ? l : l?.leaderboard || []);
    } catch { toast.error('Failed to load loyalty data'); }
    finally { setLoading(false); }
  };

  const handleRedeem = async (rewardId: string) => {
    setRedeeming(rewardId);
    try {
      const r = await apiClient.post(`/api/marketplace/loyalty/rewards/${rewardId}/redeem`, {});
      toast.success(`Redeemed: ${r.reward_name || rewardId}`);
      loadData();
    } catch { toast.error('Failed to redeem'); }
    finally { setRedeeming(null); }
  };

  const levelColors: Record<string, string> = { bronze: 'text-amber-600', silver: 'text-slate-300', gold: 'text-yellow-400', platinum: 'text-cyan-400', diamond: 'text-blue-400' };
  const levelIcons: Record<string, string> = { bronze: '🥉', silver: '🥈', gold: '🥇', platinum: '💎', diamond: '🔷' };

  if (loading) return <div className="text-slate-400 p-8">Loading loyalty data...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Loyalty & Reward System</h1>
          <p className="text-slate-400">Earn points, unlock badges, and redeem rewards</p>
        </div>
        <button onClick={loadData} className="px-4 py-2 bg-slate-800 border border-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-700">Refresh</button>
      </div>

      {status && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <div className="flex items-center gap-6 mb-6">
            <div className="text-6xl">{levelIcons[status.level?.toLowerCase()] || '⭐'}</div>
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <h2 className="text-2xl font-bold text-white capitalize">{status.level}</h2>
                <span className="text-sm text-slate-400">Level</span>
              </div>
              <div className="text-4xl font-bold text-yellow-400 mb-1">{status.points.toLocaleString()} <span className="text-lg text-slate-400">points</span></div>
              {status.points_to_next > 0 && <div className="text-sm text-slate-500">{status.points_to_next} points to next level</div>}
            </div>
            <div className="text-right">
              <div className="text-sm text-slate-400">Total Spent</div>
              <div className="text-2xl font-bold text-white">${status.total_spent.toFixed(2)}</div>
              <div className="text-sm text-slate-400">Badges: {status.badges.length}</div>
            </div>
          </div>
          {status.points_to_next > 0 && (
            <div className="w-full bg-slate-800 rounded-full h-3">
              <div className="bg-gradient-to-r from-yellow-500 to-yellow-400 h-3 rounded-full" style={{ width: `${Math.min(100, (status.points / (status.points + status.points_to_next)) * 100)}%` }} />
            </div>
          )}
        </div>
      )}

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        {(['status', 'badges', 'rewards', 'leaderboard'] as const).map(t => (
          <button key={t} onClick={() => setActiveTab(t)} className={`px-4 py-2 text-sm rounded-t-lg capitalize ${activeTab === t ? 'bg-slate-800 text-white border border-slate-700 border-b-transparent' : 'text-slate-400 hover:text-white'}`}>
            {t === 'status' ? 'Overview' : t} ({t === 'status' ? status?.badges.length || 0 : t === 'badges' ? badges.length : t === 'rewards' ? rewards.length : leaderboard.length})
          </button>
        ))}
      </div>

      {activeTab === 'badges' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {badges.map(b => (
            <div key={b.id} className={`bg-slate-900 border rounded-lg p-5 ${b.unlocked ? 'border-yellow-600/50' : 'border-slate-800 opacity-60'}`}>
              <div className="flex items-center gap-3 mb-2">
                <span className="text-3xl">{b.unlocked ? '🏅' : '🔒'}</span>
                <div>
                  <h3 className={`font-semibold ${b.unlocked ? 'text-white' : 'text-slate-500'}`}>{b.name}</h3>
                  <p className="text-xs text-slate-500">{b.description}</p>
                </div>
              </div>
              {b.unlocked && b.unlocked_at && <div className="text-xs text-slate-500">Unlocked: {b.unlocked_at.split('T')[0]}</div>}
            </div>
          ))}
        </div>
      )}

      {activeTab === 'rewards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {rewards.map(r => {
            const canAfford = status ? status.points >= r.points_cost : false;
            return (
              <div key={r.id} className="bg-slate-900 border border-slate-800 rounded-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">{r.name}</h3>
                  <span className="text-lg font-bold text-yellow-400">{r.points_cost} pts</span>
                </div>
                <p className="text-sm text-slate-400 mb-4">{r.description}</p>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-500 capitalize">{r.reward_type} {r.limited && `| ${r.remaining} left`}</span>
                  <button onClick={() => handleRedeem(r.id)} disabled={!canAfford || redeeming === r.id} className={`px-4 py-2 rounded text-xs font-semibold transition-colors ${canAfford ? 'bg-yellow-600 hover:bg-yellow-700 text-white' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}>
                    {redeeming === r.id ? '...' : canAfford ? 'Redeem' : 'Need More Points'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === 'leaderboard' && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="text-slate-400 text-xs border-b border-slate-800"><th className="text-left px-4 py-3">Rank</th><th className="text-left px-4 py-3">User</th><th className="text-right px-4 py-3">Level</th><th className="text-right px-4 py-3">Points</th><th className="text-right px-4 py-3">Badges</th></tr></thead>
            <tbody>
              {leaderboard.map((u, i) => (
                <tr key={u.user_id} className="border-b border-slate-800 hover:bg-slate-800/50 text-white">
                  <td className="px-4 py-3">
                    {i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `${i + 1}.`}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">{u.user_id.slice(0, 12)}...</td>
                  <td className="px-4 py-3 text-right capitalize">{u.level}</td>
                  <td className="px-4 py-3 text-right font-bold">{u.points.toLocaleString()}</td>
                  <td className="px-4 py-3 text-right">{u.badge_count}</td>
                </tr>
              ))}
              {leaderboard.length === 0 && <tr><td colSpan={5} className="text-center py-4 text-slate-500">No leaderboard data.</td></tr>}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default LoyaltyPage;
