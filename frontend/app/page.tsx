"use client";

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";
import { Session } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || "",
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ""
);

interface Task {
  id: string;
  title: string;
  description: string | null;
  status: string;
  assignee: { email: string } | null;
}

interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
}

export default function Home() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assigneeId, setAssigneeId] = useState("");

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:5000";

  useEffect(() => {
    const getSession = async () => {
      try {
        const {
          data: { session },
        } = await supabase.auth.getSession();
        setSession(session);
        console.log("Session loaded:", session?.user?.email || "No user");
      } catch (err) {
        console.error("Session load error:", err);
      } finally {
        setLoading(false);
      }
    };
    getSession();

    const { data: authListener } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      console.log("Auth state changed:", session?.user?.email || "No user");
    });

    return () => {
      authListener?.subscription.unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!session || loading) return;

    const fetchData = async () => {
      const token = session.access_token;

      try {
        const tasksRes = await fetch(`${backendUrl}/api/tasks`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!tasksRes.ok) {
          console.error("Tasks fetch failed:", tasksRes.status, tasksRes.statusText);
          const errData = await tasksRes.json();
          console.error("Error details:", errData);
          return;
        }
        const tasksData = await tasksRes.json();
        setTasks(tasksData || []);
      } catch (err) {
        console.error("Tasks fetch error:", err);
      }

      try {
        const usersRes = await fetch(`${backendUrl}/api/users`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (!usersRes.ok) {
          console.error("Users fetch failed:", usersRes.status, usersRes.statusText);
          const errData = await usersRes.json();
          console.error("Error details:", errData);
          return;
        }
        const usersData = await usersRes.json();
        setUsers(usersData || []);
      } catch (err) {
        console.error("Users fetch error:", err);
      }
    };

    fetchData();
  }, [session, loading, backendUrl]);

  const signInWithGoogle = async () => {
    try {
      const { error } = await supabase.auth.signInWithOAuth({ provider: "google" });
      if (error) {
        console.error("Sign-in error:", error);
      }
    } catch (err) {
      console.error("Sign-in exception:", err);
    }
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
      setSession(null);
      setTasks([]);
      setUsers([]);
    } catch (err) {
      console.error("Sign-out error:", err);
    }
  };

  const createTask = async () => {
    if (!title || !assigneeId) return;
    const token = session?.access_token;
    if (!token) return;

    try {
      const res = await fetch(`${backendUrl}/api/tasks`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ title, description, assignee_id: assigneeId }),
      });
      if (!res.ok) {
        console.error("Create task failed:", res.status, res.statusText);
        return;
      }

      setTitle("");
      setDescription("");
      setAssigneeId("");
      
      const tasksRes = await fetch(`${backendUrl}/api/tasks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const tasksData = await tasksRes.json();
      setTasks(tasksData || []);
    } catch (err) {
      console.error("Create task error:", err);
    }
  };

  const updateStatus = async (taskId: string, status: string) => {
    const token = session?.access_token;
    if (!token) return;

    try {
      const res = await fetch(`${backendUrl}/api/tasks/${taskId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) {
        console.error("Update task failed:", res.status, res.statusText);
        return;
      }

      const tasksRes = await fetch(`${backendUrl}/api/tasks`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const tasksData = await tasksRes.json();
      setTasks(tasksData || []);
    } catch (err) {
      console.error("Update task error:", err);
    }
  };

  if (loading) {
    return (
      <main style={{ padding: 24 }}>
        <h1>Task Manager</h1>
        <p>Loading...</p>
      </main>
    );
  }

  if (!session) {
    return (
      <main style={{ padding: 24 }}>
        <h1>Task Manager</h1>
        <p>Sign in with your Google account to get started.</p>
        <button onClick={signInWithGoogle}>Sign in with Google</button>
      </main>
    );
  }

  return (
    <main style={{ padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Task Manager</h1>
        <div>
          <p style={{ margin: "0 16px 0 0", display: "inline" }}>
            {session?.user?.email}
          </p>
          <button onClick={signOut}>Sign Out</button>
        </div>
      </div>

      <section style={{ marginTop: 24 }}>
        <h2>Create Task</h2>
        <div style={{ display: "grid", gap: 12, maxWidth: 420 }}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Task title" />
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" rows={4} />
          <select value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)}>
            <option value="">Select assignee</option>
            {users.map((user) => (
              <option key={user.id} value={user.id}>
                {user.email}
              </option>
            ))}
          </select>
          <button onClick={createTask}>Create Task</button>
        </div>
      </section>

      <section style={{ marginTop: 24 }}>
        <h2>Tasks ({tasks.length})</h2>
        {tasks.length === 0 ? (
          <p style={{ color: "#6b7280" }}>No tasks yet. Create one to get started!</p>
        ) : (
          <div style={{ display: "grid", gap: 16 }}>
            {tasks.map((task) => (
              <div key={task.id} style={{ border: "1px solid #ddd", padding: 16, borderRadius: 8 }}>
                <h3>{task.title}</h3>
                <p style={{ color: "#6b7280" }}>{task.description || "No description"}</p>
                <p>Status: <strong>{task.status}</strong></p>
                <p>Assignee: {task.assignee?.email || "Unassigned"}</p>
                <select value={task.status} onChange={(e) => updateStatus(task.id, e.target.value)}>
                  <option value="Open">Open</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Completed">Completed</option>
                </select>
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}