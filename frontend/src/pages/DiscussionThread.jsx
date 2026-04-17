import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

function ReplyTree({ node, depth = 0 }) {
  return (
    <div className={depth ? "ml-6 mt-3 border-l-2 border-gray-200 pl-4" : ""}>
      <p className="text-sm font-medium text-primary">{node.author_name}</p>
      <p className="mt-1 whitespace-pre-wrap text-gray-700">{node.body}</p>
      <p className="mt-1 text-xs text-gray-400">{new Date(node.created_at).toLocaleString()}</p>
      {node.replies?.map((r) => (
        <ReplyTree key={r.id} node={r} depth={depth + 1} />
      ))}
    </div>
  );
}

export default function DiscussionThread() {
  const { id } = useParams();
  const [thread, setThread] = useState(null);
  const [replyBody, setReplyBody] = useState("");
  const [err, setErr] = useState("");
  const { role } = useAuth();

  function load() {
    return api.get(`/discussions/${id}`).then((res) => setThread(res.data));
  }

  useEffect(() => {
    load().catch(() => setThread(null));
  }, [id]);

  async function sendReply(e) {
    e.preventDefault();
    setErr("");
    try {
      await api.post(`/discussions/${id}/reply`, { body: replyBody.trim() });
      setReplyBody("");
      await load();
    } catch (ex) {
      setErr(ex.response?.data?.detail || "Failed");
    }
  }

  if (!thread) {
    return (
      <div className="min-h-screen">
        <Navbar />
        <p className="p-8 text-center">Loading or not found…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <Navbar />
      <div className="mx-auto max-w-3xl px-4 py-8">
        <Link to="/discussions" className="text-sm text-primary hover:underline">
          ← All discussions
        </Link>
        <h1 className="mt-4 text-2xl font-bold text-ink">{thread.title}</h1>
        <ReplyTree node={thread} />

        {role && (
          <form onSubmit={sendReply} className="mt-8 rounded-lg border bg-white p-4 shadow">
            <h3 className="font-semibold">Add a reply</h3>
            {err && <p className="text-sm text-red-600">{String(err)}</p>}
            <textarea
              required
              className="mt-2 w-full rounded border px-3 py-2"
              rows={3}
              value={replyBody}
              onChange={(e) => setReplyBody(e.target.value)}
            />
            <button type="submit" className="mt-2 rounded-lg bg-primary px-4 py-2 text-white">
              Reply
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
