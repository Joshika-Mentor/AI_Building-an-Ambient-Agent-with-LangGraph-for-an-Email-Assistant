'use client';

import { useState, useEffect, useMemo } from 'react';
import {
  Users, Search, Shield, UserCheck, UserX, ChevronDown,
  MoreHorizontal, Mail, Calendar, Filter,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import api from '@/lib/api';
import type { User } from '@/types';

interface UserListItem extends User {}

export default function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<UserListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [editingRole, setEditingRole] = useState<number | null>(null);
  const [actionMenu, setActionMenu] = useState<number | null>(null);

  useEffect(() => {
    fetchUsers();
  }, [page]);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const response = await api.get('/users/', { params: { page, page_size: 20 } });
      setUsers(response.data.users);
      setTotal(response.data.total);
    } catch {
      // Mock data for demo
      setUsers([
        { id: 1, email: 'admin@threatlens.ai', username: 'admin', full_name: 'System Admin', role: 'administrator', is_active: true, last_login: new Date().toISOString(), created_at: '2026-01-15T00:00:00Z', updated_at: '' },
        { id: 2, email: 'analyst@threatlens.ai', username: 'jdoe', full_name: 'Jane Doe', role: 'security_analyst', is_active: true, last_login: new Date(Date.now() - 3600000).toISOString(), created_at: '2026-02-20T00:00:00Z', updated_at: '' },
        { id: 3, email: 'soc@threatlens.ai', username: 'msmith', full_name: 'Mike Smith', role: 'soc_member', is_active: true, last_login: new Date(Date.now() - 86400000).toISOString(), created_at: '2026-03-10T00:00:00Z', updated_at: '' },
        { id: 4, email: 'researcher@threatlens.ai', username: 'alee', full_name: 'Alice Lee', role: 'researcher', is_active: false, last_login: null, created_at: '2026-04-05T00:00:00Z', updated_at: '' },
      ]);
      setTotal(4);
    }
    setIsLoading(false);
  };

  const handleRoleChange = async (userId: number, newRole: string) => {
    try {
      await api.put(`/users/${userId}/role`, { role: newRole });
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole as User['role'] } : u))
      );
    } catch {
      // Fallback: update locally
      setUsers((prev) =>
        prev.map((u) => (u.id === userId ? { ...u, role: newRole as User['role'] } : u))
      );
    }
    setEditingRole(null);
  };

  const handleDeactivate = async (userId: number) => {
    try {
      await api.delete(`/users/${userId}`);
    } catch { /* fallback */ }
    setUsers((prev) =>
      prev.map((u) => (u.id === userId ? { ...u, is_active: !u.is_active } : u))
    );
    setActionMenu(null);
  };

  const formatRole = (role: string) => role.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  const roleColorMap: Record<string, string> = {
    administrator: 'text-[var(--color-danger)] bg-[var(--color-danger)]/15 border-[var(--color-danger)]/30',
    security_analyst: 'text-[var(--color-primary)] bg-[var(--color-primary)]/15 border-[var(--color-primary)]/30',
    soc_member: 'text-[var(--color-warning)] bg-[var(--color-warning)]/15 border-[var(--color-warning)]/30',
    researcher: 'text-[var(--color-purple)] bg-[var(--color-purple)]/15 border-[var(--color-purple)]/30',
  };

  const filteredUsers = useMemo(() => {
    return users.filter((u) => {
      const matchesSearch = !search ||
        u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        u.username.toLowerCase().includes(search.toLowerCase());
      const matchesRole = !roleFilter || u.role === roleFilter;
      return matchesSearch && matchesRole;
    });
  }, [users, search, roleFilter]);

  const stats = useMemo(() => ({
    total: users.length,
    active: users.filter((u) => u.is_active).length,
    inactive: users.filter((u) => !u.is_active).length,
    admins: users.filter((u) => u.role === 'administrator').length,
  }), [users]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--color-text)]">User Management</h1>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">
          Manage users, roles, and access permissions. Administrator only.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Total Users', value: stats.total, icon: <Users className="w-5 h-5 text-[var(--color-primary)]" />, color: 'var(--color-primary)' },
          { label: 'Active', value: stats.active, icon: <UserCheck className="w-5 h-5 text-[var(--color-accent)]" />, color: 'var(--color-accent)' },
          { label: 'Inactive', value: stats.inactive, icon: <UserX className="w-5 h-5 text-[var(--color-text-muted)]" />, color: 'var(--color-text-muted)' },
          { label: 'Admins', value: stats.admins, icon: <Shield className="w-5 h-5 text-[var(--color-danger)]" />, color: 'var(--color-danger)' },
        ].map((stat) => (
          <div key={stat.label} className="glass rounded-2xl p-4 animate-slide-up">
            <div className="flex items-center justify-between">
              <p className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">{stat.label}</p>
              <div className="p-2 rounded-lg" style={{ background: `${stat.color}15` }}>{stat.icon}</div>
            </div>
            <p className="text-2xl font-bold font-mono mt-1" style={{ color: stat.color }}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, or username..."
            className="w-full bg-white/5 border border-[var(--color-border)] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)]/50 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
          />
        </div>
        <div className="relative">
          <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)]" />
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="appearance-none bg-white/5 border border-[var(--color-border)] rounded-xl pl-10 pr-10 py-2.5 text-sm text-[var(--color-text)] cursor-pointer focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]/40"
          >
            <option value="" className="bg-[var(--color-surface-card)]">All Roles</option>
            <option value="administrator" className="bg-[var(--color-surface-card)]">Administrator</option>
            <option value="security_analyst" className="bg-[var(--color-surface-card)]">Security Analyst</option>
            <option value="soc_member" className="bg-[var(--color-surface-card)]">SOC Member</option>
            <option value="researcher" className="bg-[var(--color-surface-card)]">Researcher</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--color-text-muted)] pointer-events-none" />
        </div>
      </div>

      {/* Users table */}
      <div className="glass rounded-2xl overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center">
            <div className="w-8 h-8 border-[3px] rounded-full animate-spin border-[var(--color-primary)]/20 border-t-[var(--color-primary)] mx-auto" />
            <p className="text-sm text-[var(--color-text-muted)] mt-3">Loading users...</p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="p-12 text-center">
            <Users className="w-12 h-12 text-[var(--color-text-muted)]/30 mx-auto mb-4" />
            <p className="text-sm text-[var(--color-text-muted)]">No users found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--color-border)]">
                  {['User', 'Role', 'Status', 'Last Login', 'Joined', 'Actions'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="border-b border-[var(--color-border)] last:border-0 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[var(--color-primary)]/30 to-[var(--color-accent)]/30 flex items-center justify-center text-sm font-bold text-[var(--color-primary)]">
                          {u.full_name.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-[var(--color-text)]">{u.full_name}</p>
                          <p className="text-xs text-[var(--color-text-muted)] flex items-center gap-1">
                            <Mail className="w-3 h-3" /> {u.email}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {editingRole === u.id ? (
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          onBlur={() => setEditingRole(null)}
                          autoFocus
                          className="bg-white/5 border border-[var(--color-primary)]/40 rounded-lg px-2 py-1 text-xs text-[var(--color-text)] focus:outline-none"
                        >
                          <option value="administrator" className="bg-[var(--color-surface-card)]">Administrator</option>
                          <option value="security_analyst" className="bg-[var(--color-surface-card)]">Security Analyst</option>
                          <option value="soc_member" className="bg-[var(--color-surface-card)]">SOC Member</option>
                          <option value="researcher" className="bg-[var(--color-surface-card)]">Researcher</option>
                        </select>
                      ) : (
                        <button
                          onClick={() => setEditingRole(u.id)}
                          className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border cursor-pointer ${roleColorMap[u.role] || 'text-[var(--color-text-muted)] bg-white/5 border-white/10'}`}
                        >
                          {formatRole(u.role)}
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${u.is_active ? 'text-[var(--color-accent)]' : 'text-[var(--color-text-muted)]'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-[var(--color-accent)]' : 'bg-gray-500'}`} />
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">
                      {u.last_login
                        ? new Date(u.last_login).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                        : 'Never'
                      }
                    </td>
                    <td className="px-4 py-3 text-sm text-[var(--color-text-muted)]">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {new Date(u.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="relative">
                        <button
                          onClick={() => setActionMenu(actionMenu === u.id ? null : u.id)}
                          className="p-1.5 rounded-lg hover:bg-white/5 text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
                        >
                          <MoreHorizontal className="w-4 h-4" />
                        </button>
                        {actionMenu === u.id && (
                          <div className="absolute right-0 top-full mt-1 glass-strong rounded-xl py-1 w-40 z-20 shadow-xl animate-fade-in">
                            <button
                              onClick={() => { setEditingRole(u.id); setActionMenu(null); }}
                              className="w-full text-left px-4 py-2 text-sm text-[var(--color-text)] hover:bg-white/5 cursor-pointer"
                            >
                              Change Role
                            </button>
                            <button
                              onClick={() => handleDeactivate(u.id)}
                              className={`w-full text-left px-4 py-2 text-sm cursor-pointer hover:bg-white/5 ${u.is_active ? 'text-[var(--color-danger)]' : 'text-[var(--color-accent)]'}`}
                            >
                              {u.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-[var(--color-text-muted)]">
            Showing {(page - 1) * 20 + 1}-{Math.min(page * 20, total)} of {total} users
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm rounded-lg glass hover:bg-white/10 disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * 20 >= total}
              className="px-3 py-1.5 text-sm rounded-lg glass hover:bg-white/10 disabled:opacity-30 cursor-pointer disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
