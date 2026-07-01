# Library Three-Column Redesign + Dynamic Mentor Streaming Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give the Dynamic Mentor real chat persistence + streaming, and rebuild `/library` into a three-column layout (chat history | Mentor chat | Enrolled Albums/Saved Snippets).

**Architecture:** New `ChatSession`/`ChatMessage` tables back a small `chat_service`, exposed via new `/library/chats*` routes (list/create/get/post-message-with-SSE-stream), replacing the old stateless `POST /library/mentor`. Frontend gets a new `chat.ts` API client (including a hand-rolled SSE reader since `EventSource` can't carry auth headers), a standalone `MentorAvatar` component, a rebuilt `AgentChatWindow`, and a three-column `/library` page. `CTASidebar`'s teaser hand-off is updated to create-a-session-and-navigate instead of the old query-param search hand-off.

**Tech Stack:** FastAPI, SQLAlchemy (async), Alembic, boto3 (Bedrock `invoke_model_with_response_stream`), pytest/httpx, SvelteKit, TypeScript, vitest.

**Spec:** `docs/superpowers/specs/2026-07-01-library-mentor-redesign-design.md`

---

## Parallelization Map

Each module below only touches the files listed for it — no two modules in the same wave share a file, so they're safe to dispatch as parallel subagents. Later waves depend on earlier waves completing first.

- **Wave 1 (parallel):** Module A (backend data model), Module B (frontend chat API client), Module C (frontend MentorAvatar component)
- **Wave 2 (parallel, depends on Wave 1):** Module D (backend chat_service + schemas — needs A), Module E (frontend AgentChatWindow rebuild — needs B, C)
- **Wave 3 (parallel, depends on Wave 2):** Module F (backend router wiring — needs D), Module G (frontend CTASidebar hand-off — needs B)
- **Wave 4 (depends on Wave 3):** Module H (frontend `/library` page layout — needs E, F, B)
- **Wave 5 (depends on Wave 4):** Module I (full-stack verification pass)

---

## Module A: Backend data model + migration

**Files:**
- Modify: `backend/app/models/library.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/migrations/versions/c7d9f1a2b3c4_add_chat_sessions_and_messages.py`
- Test: `backend/tests/test_chat_models.py`

### Task A1: Add ChatSession and ChatMessage models

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_chat_models.py`:

```python
from sqlalchemy import select

from app.models.library import ChatMessage, ChatSession
from app.models.user import User


async def test_chat_session_and_message_persist_and_cascade(db_session, current_user: User) -> None:
    session = ChatSession(user_id=current_user.id, title="What is networking?")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    msg = ChatMessage(session_id=session.id, role="user", text="What is networking?")
    reply = ChatMessage(
        session_id=session.id,
        role="mentor",
        text="Networking connects computers.",
        sources=[{"content_id": 1, "title": "Cloud Networking"}],
    )
    db_session.add_all([msg, reply])
    await db_session.commit()

    result = await db_session.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.id)
    )
    messages = result.scalars().all()
    assert [m.role for m in messages] == ["user", "mentor"]
    assert messages[1].sources == [{"content_id": 1, "title": "Cloud Networking"}]

    # Deleting the session cascades to its messages.
    await db_session.delete(session)
    await db_session.commit()
    remaining = await db_session.execute(select(ChatMessage).where(ChatMessage.session_id == session.id))
    assert remaining.scalars().all() == []


async def test_chat_session_cascades_from_user(db_session, current_user: User) -> None:
    session = ChatSession(user_id=current_user.id, title="test")
    db_session.add(session)
    await db_session.commit()

    await db_session.delete(current_user)
    await db_session.commit()

    result = await db_session.execute(select(ChatSession).where(ChatSession.id == session.id))
    assert result.scalars().all() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_chat_models.py -v`
Expected: FAIL with `ImportError: cannot import name 'ChatSession' from 'app.models.library'`

- [ ] **Step 3: Add the models**

Edit `backend/app/models/library.py`, appending after the existing `UserSnippetSave` class:

```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # First ~60 chars of the first user message, truncated. Set once at creation
    # of the first message, never regenerated (no extra LLM call just to title a chat).
    title: Mapped[str] = mapped_column(String(60), default="New chat")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.id"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(10))  # "user" | "mentor"
    text: Mapped[str] = mapped_column(Text)
    sources: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)  # mentor messages only
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped[ChatSession] = relationship(back_populates="messages")
```

Update the file's imports at the top (`from sqlalchemy import ...`) to include the new types used:

```python
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
```

(`String`, `Text`, `JSON` are new; `DateTime`, `ForeignKey`, `func`, `Mapped`, `mapped_column`, `relationship`, `Base` already present.)

Note: unlike `UserSnippetSave`'s `user`/`content` relationships, `ChatSession`/`ChatMessage` don't need `User` in scope at all — `ChatSession.user_id` is a plain FK column (no ORM relationship back to `User` is needed; `chat_service` will query `ChatSession` directly by `user_id`), avoiding any need to touch `user.py`.

- [ ] **Step 4: Register the new models**

Edit `backend/app/models/__init__.py`:

```python
from app.models.library import ChatMessage, ChatSession, UserSnippetSave  # noqa: E402, F401
```

(replaces the existing `from app.models.library import UserSnippetSave` line)

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_chat_models.py -v`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
cd backend
git add app/models/library.py app/models/__init__.py tests/test_chat_models.py
git commit -m "feat(backend): add ChatSession and ChatMessage models"
```

### Task A2: Migration

- [ ] **Step 1: Write the migration**

Create `backend/migrations/versions/c7d9f1a2b3c4_add_chat_sessions_and_messages.py`:

```python
"""add chat_sessions and chat_messages

Revision ID: c7d9f1a2b3c4
Revises: a3f8c2d1e594
Create Date: 2026-07-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7d9f1a2b3c4"
down_revision: str | Sequence[str] | None = "a3f8c2d1e594"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("title", sa.String(60), nullable=False, server_default="New chat"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "session_id",
            sa.Integer,
            sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("sources", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
```

- [ ] **Step 2: Verify current head matches the `down_revision`**

Run: `cd backend && poetry run alembic heads`
Expected: `a3f8c2d1e594 (head)` — confirms this migration chains correctly. If a different revision is shown (another migration landed on `main`/`dev` since this plan was written), update `down_revision` in the file above to match the actual current head before continuing.

- [ ] **Step 3: Apply the migration against local Docker Postgres**

Run: `docker compose exec backend poetry run alembic upgrade head`
Expected: output ends with `Running upgrade a3f8c2d1e594 -> c7d9f1a2b3c4, add chat_sessions and chat_messages`

- [ ] **Step 4: Commit**

```bash
cd backend
git add migrations/versions/c7d9f1a2b3c4_add_chat_sessions_and_messages.py
git commit -m "feat(backend): migration for chat_sessions and chat_messages tables"
```

---

## Module B: Frontend chat API client

**Files:**
- Create: `frontend/src/lib/api/chat.ts`
- Test: `frontend/src/lib/api/chat.test.ts`

### Task B1: Types + list/create/get session functions

- [ ] **Step 1: Write the failing test**

Create `frontend/src/lib/api/chat.test.ts`:

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { TOKEN_KEY } from './client';

describe('chat api client', () => {
  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem(TOKEN_KEY, 'test-token');
    vi.restoreAllMocks();
  });

  it('listChatSessions calls GET /library/chats and returns parsed JSON', async () => {
    const mockSessions = [{ id: 1, title: 'Hello', updated_at: '2026-07-01T00:00:00Z' }];
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSessions,
      })
    );

    const { listChatSessions } = await import('./chat');
    const result = await listChatSessions();

    expect(result).toEqual(mockSessions);
    const [url, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toContain('/library/chats');
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer test-token');
  });

  it('createChatSession POSTs to /library/chats and returns the new session', async () => {
    const mockSession = { id: 2, title: 'New chat', updated_at: '2026-07-01T00:00:00Z' };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockSession,
      })
    );

    const { createChatSession } = await import('./chat');
    const result = await createChatSession();

    expect(result).toEqual(mockSession);
    const [, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(init.method).toBe('POST');
  });

  it('getChatSession fetches full message history for one session', async () => {
    const mockDetail = {
      id: 3,
      title: 'Hi',
      messages: [{ id: 1, role: 'user', text: 'Hi', sources: null, created_at: '2026-07-01T00:00:00Z' }],
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockDetail,
      })
    );

    const { getChatSession } = await import('./chat');
    const result = await getChatSession(3);

    expect(result).toEqual(mockDetail);
    const [url] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
    expect(url).toContain('/library/chats/3');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/api/chat.test.ts`
Expected: FAIL — `Failed to resolve import "./chat"`

- [ ] **Step 3: Write the implementation**

Create `frontend/src/lib/api/chat.ts`:

```typescript
import { apiFetch, TOKEN_KEY, ApiError } from './client';

export interface ChatSessionSummary {
  id: number;
  title: string;
  updated_at: string;
}

export interface ChatMessageSource {
  content_id: number;
  title: string;
}

export interface ChatMessageRecord {
  id: number;
  role: 'user' | 'mentor';
  text: string;
  sources: ChatMessageSource[] | null;
  created_at: string;
}

export interface ChatSessionDetail {
  id: number;
  title: string;
  messages: ChatMessageRecord[];
}

export async function listChatSessions(): Promise<ChatSessionSummary[]> {
  return apiFetch<ChatSessionSummary[]>('/library/chats');
}

export async function createChatSession(): Promise<ChatSessionSummary> {
  return apiFetch<ChatSessionSummary>('/library/chats', { method: 'POST' });
}

export async function getChatSession(sessionId: number): Promise<ChatSessionDetail> {
  return apiFetch<ChatSessionDetail>(`/library/chats/${sessionId}`);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/api/chat.test.ts`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/lib/api/chat.ts src/lib/api/chat.test.ts
git commit -m "feat(frontend): chat session list/create/get API client"
```

### Task B2: Streaming message send

- [ ] **Step 1: Write the failing test**

Append to `frontend/src/lib/api/chat.test.ts`:

```typescript
it('sendChatMessage streams SSE chunks and calls onDelta for each one', async () => {
  const encoder = new TextEncoder();
  const frames = [
    'data: {"delta":"Hello "}\n\n',
    'data: {"delta":"world."}\n\n',
    'data: {"done":true,"message_id":42}\n\n',
  ];
  let frameIndex = 0;
  const reader = {
    read: async () => {
      if (frameIndex >= frames.length) return { done: true, value: undefined };
      const value = encoder.encode(frames[frameIndex]);
      frameIndex++;
      return { done: false, value };
    },
  };
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => reader },
    })
  );

  const { sendChatMessage } = await import('./chat');
  const deltas: string[] = [];
  const result = await sendChatMessage(3, 'What is networking?', (delta) => deltas.push(delta));

  expect(deltas).toEqual(['Hello ', 'world.']);
  expect(result).toEqual({ messageId: 42 });
  const [url, init] = (fetch as ReturnType<typeof vi.fn>).mock.calls[0];
  expect(url).toContain('/library/chats/3/messages');
  expect(JSON.parse(init.body as string)).toEqual({ message: 'What is networking?' });
});

it('sendChatMessage throws ApiError on a non-ok response', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    })
  );

  const { sendChatMessage } = await import('./chat');
  await expect(sendChatMessage(3, 'hi', () => {})).rejects.toBeInstanceOf(ApiError);
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/api/chat.test.ts`
Expected: FAIL — `sendChatMessage is not a function`

- [ ] **Step 3: Write the implementation**

Append to `frontend/src/lib/api/chat.ts`:

```typescript
export interface SendChatMessageResult {
  messageId: number;
}

/**
 * Streams a mentor reply via SSE. Deliberately does NOT use the native
 * EventSource API — it can't send an Authorization header, and every other
 * authenticated call in this app relies on one. fetch() + a ReadableStream
 * reader gets the same auth story as apiFetch() while still streaming.
 */
export async function sendChatMessage(
  sessionId: number,
  message: string,
  onDelta: (text: string) => void
): Promise<SendChatMessageResult> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? '';
  const token = localStorage.getItem(TOKEN_KEY);
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${baseUrl}/library/chats/${sessionId}/messages`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message }),
  });

  if (!response.ok || !response.body) {
    throw new ApiError(response.status, `Streaming request failed with status ${response.status}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let messageId: number | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // SSE frames are separated by a blank line; a chunk boundary from the
    // network doesn't necessarily land on a frame boundary, so buffer
    // partial data and only process complete "data: ...\n\n" frames.
    let boundary = buffer.indexOf('\n\n');
    while (boundary !== -1) {
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      if (frame.startsWith('data: ')) {
        const payload = JSON.parse(frame.slice('data: '.length));
        if (payload.done) {
          messageId = payload.message_id;
        } else if (typeof payload.delta === 'string') {
          onDelta(payload.delta);
        }
      }
      boundary = buffer.indexOf('\n\n');
    }
  }

  return { messageId: messageId ?? -1 };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/api/chat.test.ts`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/lib/api/chat.ts src/lib/api/chat.test.ts
git commit -m "feat(frontend): streaming SSE reader for chat messages"
```

---

## Module C: Frontend MentorAvatar component

**Files:**
- Create: `frontend/src/lib/components/MentorAvatar.svelte`
- Test: `frontend/src/lib/components/MentorAvatar.test.ts`

### Task C1: Build the avatar component

- [ ] **Step 1: Write the failing test**

Create `frontend/src/lib/components/MentorAvatar.test.ts`:

```typescript
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/svelte';
import MentorAvatar from './MentorAvatar.svelte';

describe('MentorAvatar', () => {
  it('renders a circular element with the mentor gradient class', () => {
    const { container } = render(MentorAvatar);
    const el = container.querySelector('.mentor-avatar');
    expect(el).not.toBeNull();
  });

  it('accepts a size prop that sets width/height', () => {
    const { container } = render(MentorAvatar, { props: { size: '64px' } });
    const el = container.querySelector('.mentor-avatar') as HTMLElement;
    expect(el.style.width).toBe('64px');
    expect(el.style.height).toBe('64px');
  });
});
```

Check whether `@testing-library/svelte` is already a devDependency:

Run: `cd frontend && grep -q '"@testing-library/svelte"' package.json && echo present || echo missing`

If `missing`, install it: `cd frontend && npm install -D @testing-library/svelte`

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/components/MentorAvatar.test.ts`
Expected: FAIL — `Failed to resolve import "./MentorAvatar.svelte"`

- [ ] **Step 3: Write the implementation**

Create `frontend/src/lib/components/MentorAvatar.svelte`:

```svelte
<!--
  MentorAvatar
  Purpose: The Dynamic Mentor's identity in the Discord-style chat message list
    (AgentChatWindow). A gradient circle whose hues are derived from the app's
    per-route palette system (gradient.ts) rather than a hardcoded colour, plus a
    slow "breathing" hue-shift so it reads as alive, not static.
  Used in: AgentChatWindow
  Props:
    - size (string): CSS size for width/height, default '38px' (in-chat size).
  Notes: A dot-matrix/lens-warp texture and a chromatic edge glow were both explored
    for this avatar during brainstorming and explicitly dropped — this is deliberately
    just the gradient + sheen highlights + breathe animation, nothing more.
-->
<script lang="ts">
  import { getShadowHues } from '$lib/gradient';

  export let size: string = '38px';

  const [hueA, hueB, hueC] = getShadowHues('/library');
</script>

<div
  class="mentor-avatar"
  style="width: {size}; height: {size}; --hue-a: {hueA}; --hue-b: {hueB}; --hue-c: {hueC};"
>
  <div class="core"></div>
  <div class="sheen"></div>
</div>

<style>
  .mentor-avatar {
    position: relative;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;
  }

  .core {
    position: absolute;
    inset: -15%;
    background: radial-gradient(
      circle at 35% 30%,
      hsl(var(--hue-a) 85% 68%),
      hsl(var(--hue-b) 70% 55%) 55%,
      hsl(var(--hue-c) 60% 55%) 100%
    );
    animation: breathe 5s ease-in-out infinite alternate;
  }

  @keyframes breathe {
    0% {
      filter: hue-rotate(0deg) brightness(1);
    }
    100% {
      filter: hue-rotate(70deg) brightness(1.18);
    }
  }

  .sheen {
    position: absolute;
    inset: 0;
    border-radius: 50%;
    background:
      radial-gradient(circle at 40% 35%, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0) 45%),
      radial-gradient(circle at 65% 70%, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0) 50%);
  }

  @media (prefers-reduced-motion: reduce) {
    .core {
      animation: none;
    }
  }
</style>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/components/MentorAvatar.test.ts`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/lib/components/MentorAvatar.svelte src/lib/components/MentorAvatar.test.ts package.json package-lock.json
git commit -m "feat(frontend): MentorAvatar component with breathing gradient"
```

---

## Module D: Backend chat_service + schemas

**Depends on:** Module A (models must exist)

**Files:**
- Create: `backend/app/schemas/chat.py`
- Create: `backend/app/services/chat_service.py`
- Test: `backend/tests/test_chat_service.py`

### Task D1: Schemas

- [ ] **Step 1: Write schemas (no test needed — pure data classes, exercised by D2/D3's tests)**

Create `backend/app/schemas/chat.py`:

```python
from datetime import datetime

from pydantic import BaseModel


class ChatSessionSummary(BaseModel):
    id: int
    title: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageSource(BaseModel):
    content_id: int
    title: str


class ChatMessageRecord(BaseModel):
    id: int
    role: str
    text: str
    sources: list[ChatMessageSource] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionDetail(BaseModel):
    id: int
    title: str
    messages: list[ChatMessageRecord]


class ChatMessageRequest(BaseModel):
    message: str
```

- [ ] **Step 2: Commit**

```bash
cd backend
git add app/schemas/chat.py
git commit -m "feat(backend): chat schemas"
```

### Task D2: Session CRUD in chat_service

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_chat_service.py`:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def test_create_session_returns_new_session_with_default_title(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.services.chat_service import create_session

    session = await create_session(db_session, current_user)

    assert session.id is not None
    assert session.title == "New chat"
    assert session.user_id == current_user.id


async def test_list_sessions_returns_only_current_users_sessions_newest_first(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.models.library import ChatSession
    from app.services.chat_service import list_sessions

    other_user = User(cognito_sub="other", email="other@example.com", first_name="O", last_name="U")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    s1 = ChatSession(user_id=current_user.id, title="First")
    db_session.add(s1)
    await db_session.commit()
    await db_session.refresh(s1)

    s2 = ChatSession(user_id=current_user.id, title="Second")
    db_session.add(s2)
    await db_session.commit()
    await db_session.refresh(s2)

    db_session.add(ChatSession(user_id=other_user.id, title="Not mine"))
    await db_session.commit()

    # Force s2's updated_at to be later so ordering is deterministic regardless
    # of how fast these commits ran within the same clock tick.
    import datetime

    s2.updated_at = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=10)
    await db_session.commit()

    sessions = await list_sessions(db_session, current_user)

    assert [s.title for s in sessions] == ["Second", "First"]


async def test_get_session_or_404_raises_for_other_users_session(
    db_session: AsyncSession, current_user: User
) -> None:
    from fastapi import HTTPException

    from app.models.library import ChatSession
    from app.services.chat_service import get_session_or_404

    other_user = User(cognito_sub="other2", email="other2@example.com", first_name="O", last_name="U")
    db_session.add(other_user)
    await db_session.commit()
    await db_session.refresh(other_user)

    session = ChatSession(user_id=other_user.id, title="Not mine")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    with pytest.raises(HTTPException) as exc_info:
        await get_session_or_404(db_session, session.id, current_user)
    assert exc_info.value.status_code == 404


async def test_get_session_detail_includes_ordered_messages(
    db_session: AsyncSession, current_user: User
) -> None:
    from app.models.library import ChatMessage, ChatSession
    from app.services.chat_service import get_session_detail

    session = ChatSession(user_id=current_user.id, title="Hi")
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)

    db_session.add_all(
        [
            ChatMessage(session_id=session.id, role="user", text="Hi"),
            ChatMessage(session_id=session.id, role="mentor", text="Hello!"),
        ]
    )
    await db_session.commit()

    detail = await get_session_detail(db_session, session, current_user)

    assert detail.title == "Hi"
    assert [m.text for m in detail.messages] == ["Hi", "Hello!"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_chat_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.chat_service'`

- [ ] **Step 3: Write the implementation**

Create `backend/app/services/chat_service.py`:

```python
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.library import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessageRecord, ChatMessageSource, ChatSessionDetail

TITLE_MAX_LEN = 60


def _derive_title(first_message: str) -> str:
    trimmed = first_message.strip()
    if len(trimmed) <= TITLE_MAX_LEN:
        return trimmed or "New chat"
    return trimmed[: TITLE_MAX_LEN - 1].rstrip() + "…"


async def create_session(db: AsyncSession, user: User) -> ChatSession:
    session = ChatSession(user_id=user.id, title="New chat")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def list_sessions(db: AsyncSession, user: User) -> list[ChatSession]:
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_session_or_404(db: AsyncSession, session_id: int, user: User) -> ChatSession:
    stmt = (
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .options(selectinload(ChatSession.messages))
    )
    session = (await db.execute(stmt)).scalar_one_or_none()
    if session is None:
        # 404, not 403 — don't confirm to the caller that a session with this
        # id exists at all if it isn't theirs.
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


async def get_session_detail(db: AsyncSession, session: ChatSession, user: User) -> ChatSessionDetail:
    return ChatSessionDetail(
        id=session.id,
        title=session.title,
        messages=[
            ChatMessageRecord(
                id=m.id,
                role=m.role,
                text=m.text,
                sources=(
                    [ChatMessageSource(**s) for s in m.sources] if m.sources is not None else None
                ),
                created_at=m.created_at,
            )
            for m in session.messages
        ],
    )
```

Note: `ChatMessage` is imported but not yet used directly in this file — it will be used by Task D3 below. If your linter flags it as unused after this step alone, that's expected and will resolve once D3 lands in the same file.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_chat_service.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
cd backend
git add app/services/chat_service.py tests/test_chat_service.py
git commit -m "feat(backend): chat session CRUD in chat_service"
```

### Task D3: Streaming mentor reply

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_chat_service.py`:

```python
async def test_stream_mentor_reply_persists_user_and_mentor_messages(
    db_session: AsyncSession, current_user: User
) -> None:
    from unittest.mock import MagicMock, patch

    from app.models.library import ChatMessage, ChatSession
    from app.services.chat_service import create_session, stream_mentor_reply

    session = await create_session(db_session, current_user)

    def fake_event_stream():
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hello "}}}'}}
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "there."}}}'}}
        yield {"chunk": {"bytes": b'{"messageStop": {}}'}}

    mock_stream_response = {"body": fake_event_stream()}

    with (
        patch("app.services.chat_service.embed_text", return_value=[0.1] * 1024),
        patch("app.services.chat_service._fetch_mentor_context", return_value=[]),
        patch("app.services.chat_service.get_bedrock_client") as mock_get_client,
    ):
        mock_get_client.return_value.invoke_model_with_response_stream.return_value = (
            mock_stream_response
        )

        deltas = []
        async for delta in stream_mentor_reply(db_session, session, "Hi", current_user):
            deltas.append(delta)

    assert deltas == ["Hello ", "there."]

    from sqlalchemy import select

    result = await db_session.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.id)
    )
    messages = result.scalars().all()
    assert [m.role for m in messages] == ["user", "mentor"]
    assert messages[0].text == "Hi"
    assert messages[1].text == "Hello there."

    await db_session.refresh(session)
    assert session.title == "Hi"


async def test_stream_mentor_reply_sets_title_only_on_first_message(
    db_session: AsyncSession, current_user: User
) -> None:
    from unittest.mock import patch

    from app.services.chat_service import create_session, stream_mentor_reply

    session = await create_session(db_session, current_user)

    def fake_event_stream():
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hi!"}}}'}}

    with (
        patch("app.services.chat_service.embed_text", return_value=[0.1] * 1024),
        patch("app.services.chat_service._fetch_mentor_context", return_value=[]),
        patch("app.services.chat_service.get_bedrock_client") as mock_get_client,
    ):
        mock_get_client.return_value.invoke_model_with_response_stream.return_value = {
            "body": fake_event_stream()
        }
        async for _ in stream_mentor_reply(db_session, session, "First message", current_user):
            pass

        def fake_event_stream_2():
            yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hi again!"}}}'}}

        mock_get_client.return_value.invoke_model_with_response_stream.return_value = {
            "body": fake_event_stream_2()
        }
        async for _ in stream_mentor_reply(db_session, session, "Second message", current_user):
            pass

    await db_session.refresh(session)
    assert session.title == "First message"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_chat_service.py -v -k stream_mentor_reply`
Expected: FAIL — `ImportError: cannot import name 'stream_mentor_reply'`

- [ ] **Step 3: Write the implementation**

Edit `backend/app/services/chat_service.py`. Add these imports at the top (merging with the existing ones):

```python
import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.library import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import ChatMessageRecord, ChatMessageSource, ChatSessionDetail
from app.services.embedding_service import embed_text, get_bedrock_client
from app.services.library_service import MENTOR_CONTEXT_CHUNKS, _fetch_mentor_context  # noqa: F401
```

Append at the end of the file:

```python
def _parse_stream_event(raw_bytes: bytes) -> str | None:
    """
    Extract incremental text from one Bedrock InvokeModelWithResponseStream event.
    Nova's native streaming schema wraps each text increment in a
    contentBlockDelta.delta.text field; other event types (contentBlockStart,
    messageStop, metadata) carry no text and are skipped.
    """
    payload = json.loads(raw_bytes)
    delta = payload.get("contentBlockDelta", {}).get("delta", {})
    return delta.get("text")


async def stream_mentor_reply(
    db: AsyncSession, session: ChatSession, message: str, user: User
) -> AsyncIterator[str]:
    settings = get_settings()
    query_vec = embed_text(message)
    if query_vec is None:
        raise HTTPException(status_code=503, detail="The mentor is temporarily unavailable")
    chunks: list[dict[str, Any]] = await _fetch_mentor_context(db, query_vec, user)

    context_text = "\n\n".join(f"{c['title']}: {c['body'][:500]}" for c in chunks)
    prompt = (
        "You are the Dynamic Mentor for Living Campus, an Amazon T-Level education platform.\n"
        "Answer the student's question using the provided context from their learning materials.\n"
        "If the context doesn't cover the question, say so and answer from general knowledge.\n\n"
        f"Context:\n{context_text}\n\n"
        f"Student question: {message}\n\nMentor:"
    )

    response = get_bedrock_client().invoke_model_with_response_stream(
        modelId=settings.BEDROCK_GENERATION_MODEL_ID,
        body=json.dumps(
            {
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"maxTokens": 512, "temperature": 0.7, "topP": 0.9},
            }
        ),
    )

    full_text_parts: list[str] = []
    for event in response["body"]:
        raw_bytes = event.get("chunk", {}).get("bytes")
        if raw_bytes is None:
            continue
        text = _parse_stream_event(raw_bytes)
        if text:
            full_text_parts.append(text)
            yield text

    full_text = "".join(full_text_parts) or "I'm sorry, I couldn't generate a response right now."
    sources = [{"content_id": c["content_id"], "title": c["title"]} for c in chunks]

    is_first_message = len(session.messages) == 0
    db.add(ChatMessage(session_id=session.id, role="user", text=message))
    db.add(ChatMessage(session_id=session.id, role="mentor", text=full_text, sources=sources))
    if is_first_message:
        session.title = _derive_title(message)
    await db.commit()
```

Note: `library_service._fetch_mentor_context` is reused as-is per the spec ("Reuses `_fetch_mentor_context`'s existing RAG retrieval"). It's name-prefixed with an underscore (module-private by convention) but Python doesn't enforce that — this matches how the codebase already treats it as shared internal helper logic within the `library`/`chat` service pair. `MENTOR_CONTEXT_CHUNKS` is imported but unused directly in this file (kept for parity/future use); if your linter flags it, remove it from the import line — it's not required for this task to pass.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_chat_service.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Run full backend lint + test suite to catch regressions**

Run: `cd backend && poetry run ruff check . && poetry run pytest`
Expected: no lint errors, all tests pass

- [ ] **Step 6: Commit**

```bash
cd backend
git add app/services/chat_service.py tests/test_chat_service.py
git commit -m "feat(backend): stream mentor replies from Bedrock, persist on completion"
```

**Verification note for whoever implements this task:** the exact JSON shape of Bedrock's `InvokeModelWithResponseStream` events for Nova models (`contentBlockDelta.delta.text` used above) is based on Bedrock's documented Converse-style streaming event schema, matching how `library_service.mentor_query`'s non-streaming `invoke_model` already parses `output.message.content[0].text` for the same model family's non-streaming response. Unit tests here fully control the mocked event shape and will pass regardless of drift, but if a manual end-to-end check against real Bedrock (Module I) shows a different event shape, adjust `_parse_stream_event` accordingly — that's a legitimate integration fix, not a sign the plan was followed wrong.

---

## Module E: Frontend AgentChatWindow rebuild

**Depends on:** Module B (`chat.ts`), Module C (`MentorAvatar.svelte`)

**Files:**
- Modify: `frontend/src/lib/components/AgentChatWindow.svelte`
- Test: `frontend/src/lib/components/AgentChatWindow.test.ts`

### Task E1: Rebuild the message list + avatar + streaming text

- [ ] **Step 1: Write the failing test**

Create `frontend/src/lib/components/AgentChatWindow.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import AgentChatWindow from './AgentChatWindow.svelte';
import type { ChatMessageRecord } from '$lib/api/chat';

describe('AgentChatWindow', () => {
  const messages: ChatMessageRecord[] = [
    { id: 1, role: 'user', text: 'What is networking?', sources: null, created_at: '2026-07-01T14:00:00Z' },
    {
      id: 2,
      role: 'mentor',
      text: 'Networking connects computers.',
      sources: [{ content_id: 5, title: 'Cloud Networking' }],
      created_at: '2026-07-01T14:00:05Z',
    },
  ];

  it('renders all messages in a single column with usernames', () => {
    render(AgentChatWindow, { props: { messages, onSend: vi.fn(), userDisplayName: 'Harley' } });

    expect(screen.getByText('What is networking?')).toBeInTheDocument();
    expect(screen.getByText('Networking connects computers.')).toBeInTheDocument();
    expect(screen.getByText('Harley')).toBeInTheDocument();
    expect(screen.getByText('Dynamic Mentor')).toBeInTheDocument();
  });

  it('renders source chips for mentor messages that have sources', () => {
    render(AgentChatWindow, { props: { messages, onSend: vi.fn(), userDisplayName: 'Harley' } });
    expect(screen.getByText('Cloud Networking')).toBeInTheDocument();
  });

  it('calls onSend with the draft text when the input is submitted', async () => {
    const onSend = vi.fn();
    const { component } = render(AgentChatWindow, {
      props: { messages: [], onSend, userDisplayName: 'Harley' },
    });
    const input = screen.getByPlaceholderText('Ask your mentor anything...') as HTMLInputElement;
    input.value = 'New question';
    input.dispatchEvent(new Event('input'));
    const form = input.closest('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit', { cancelable: true }));

    expect(onSend).toHaveBeenCalledWith('New question');
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/components/AgentChatWindow.test.ts`
Expected: FAIL — component doesn't yet accept `userDisplayName`/render usernames/avatars this way (current stub uses hardcoded dark bubbles, no avatar, no source chips)

- [ ] **Step 3: Rewrite the component**

Replace the entire contents of `frontend/src/lib/components/AgentChatWindow.svelte`:

```svelte
<!--
  AgentChatWindow
  Purpose: Full conversation view for the Dynamic Mentor. Single-column, Discord-style
    message list (avatar + username + timestamp above each message, no left/right split
    between user and mentor), streaming-in text, and a coloured "send flourish" on the
    input row.
  Used in: /library (center column)
  Props:
    - messages (ChatMessageRecord[]): full message history for the active session.
    - onSend ((text: string) => void): called when the user submits a new message.
    - userDisplayName (string): current user's display name, shown above their messages.
    - streamingText (string | undefined): in-progress mentor reply text while a stream
      is active. When set (even to ''), an in-progress mentor message row renders with
      this text, using the per-chunk blur-in span treatment.
    - isStreaming (boolean): drives the chat card's inner chromatic glow.
-->
<script lang="ts">
  import { tick } from 'svelte';
  import MentorAvatar from '$lib/components/MentorAvatar.svelte';
  import type { ChatMessageRecord } from '$lib/api/chat';

  export let messages: ChatMessageRecord[];
  export let onSend: (text: string) => void;
  export let userDisplayName: string;
  export let streamingText: string | undefined = undefined;
  export let isStreaming: boolean = false;

  let draft = '';
  let messageContainer: HTMLDivElement | undefined;
  let flourish = false;

  $: if (messages || streamingText) {
    scrollToBottom();
  }

  async function scrollToBottom() {
    await tick();
    if (messageContainer) {
      messageContainer.scrollTop = messageContainer.scrollHeight;
    }
  }

  function formatTime(iso: string): string {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function send() {
    const text = draft.trim();
    if (!text) return;
    onSend(text);
    draft = '';
    flourish = false;
    void tick().then(() => (flourish = true));
  }
</script>

<div class="chat-window" class:streaming={isStreaming}>
  <div class="messages" bind:this={messageContainer}>
    {#each messages as message (message.id)}
      <div class="message-row">
        {#if message.role === 'mentor'}
          <MentorAvatar />
        {:else}
          <div class="user-avatar">{userDisplayName.slice(0, 2).toUpperCase()}</div>
        {/if}
        <div class="message-body">
          <div class="message-head">
            <span class="message-name">{message.role === 'mentor' ? 'Dynamic Mentor' : userDisplayName}</span>
            <span class="message-time">{formatTime(message.created_at)}</span>
          </div>
          <p class="message-text">{message.text}</p>
          {#if message.sources && message.sources.length > 0}
            <div class="sources">
              {#each message.sources as source (source.content_id)}
                <span class="source-chip">{source.title}</span>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {/each}

    {#if streamingText !== undefined}
      <div class="message-row">
        <MentorAvatar />
        <div class="message-body">
          <div class="message-head">
            <span class="message-name">Dynamic Mentor</span>
          </div>
          <p class="message-text">
            {#each streamingText.split(' ') as word, i (i)}<span class="chunk">{word} </span>{/each}
          </p>
        </div>
      </div>
    {/if}
  </div>

  <form class="input-row" class:flourish on:submit|preventDefault={send}>
    <input bind:value={draft} type="text" placeholder="Ask your mentor anything..." autocomplete="off" />
    <button type="submit" aria-label="Send">Send</button>
  </form>
</div>

<style>
  .chat-window {
    height: 100%;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  /* Streaming glow: large four-hue inset glow layered on the card's own edges,
     colour-cycling continuously while active, with a fog-like blur+opacity
     creep-in/dissipate rather than a plain fade. Lives on ::before so it
     composes with PageCard's own outer drop-shadow instead of replacing it. */
  .chat-window::before {
    content: '';
    position: absolute;
    inset: 0;
    opacity: 0;
    filter: blur(22px);
    transition:
      opacity 1.1s ease-in,
      filter 1.1s ease-in;
    animation: glow-cycle 6s linear infinite;
    pointer-events: none;
  }

  .chat-window.streaming::before {
    opacity: 1;
    filter: blur(0px);
    transition:
      opacity 0.9s ease-out,
      filter 0.9s ease-out;
  }

  @keyframes glow-cycle {
    0%,
    100% {
      box-shadow:
        inset 40px 40px 90px -20px hsl(20 75% 60% / 0.55),
        inset -40px 40px 90px -20px hsl(130 70% 55% / 0.5),
        inset -40px -40px 90px -20px hsl(240 65% 58% / 0.5),
        inset 40px -40px 90px -20px hsl(310 70% 60% / 0.5);
    }
    33% {
      box-shadow:
        inset 40px 40px 90px -20px hsl(150 75% 55% / 0.55),
        inset -40px 40px 90px -20px hsl(260 70% 58% / 0.5),
        inset -40px -40px 90px -20px hsl(10 65% 60% / 0.5),
        inset 40px -40px 90px -20px hsl(80 70% 55% / 0.5);
    }
    66% {
      box-shadow:
        inset 40px 40px 90px -20px hsl(280 75% 58% / 0.55),
        inset -40px 40px 90px -20px hsl(30 70% 60% / 0.5),
        inset -40px -40px 90px -20px hsl(100 65% 55% / 0.5),
        inset 40px -40px 90px -20px hsl(210 70% 58% / 0.5);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .chat-window::before {
      animation: none;
      transition: opacity 0.3s ease;
    }
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem 0.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
  }

  .message-row {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .user-avatar {
    width: 38px;
    height: 38px;
    flex-shrink: 0;
    border-radius: 50%;
    background: #232f3e;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    font-family: 'Ubuntu', sans-serif;
  }

  .message-body {
    flex: 1;
    min-width: 0;
  }

  .message-head {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin-bottom: 0.15rem;
  }

  .message-name {
    font-weight: 700;
    font-size: 0.85rem;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
  }

  .message-time {
    font-size: 0.7rem;
    color: #8a94a3;
    font-family: 'Ubuntu', sans-serif;
  }

  .message-text {
    font-size: 0.875rem;
    line-height: 1.6;
    color: #232f3e;
    font-family: 'Ubuntu', sans-serif;
    margin: 0;
    word-break: break-word;
  }

  .chunk {
    display: inline;
    filter: blur(0);
    opacity: 1;
    transition:
      filter 0.7s ease-out,
      opacity 0.7s ease-out;
  }

  .sources {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-top: 0.5rem;
  }

  .source-chip {
    font-size: 0.7rem;
    background: rgba(35, 47, 62, 0.08);
    color: #232f3e;
    border-radius: 99px;
    padding: 0.15rem 0.5rem;
    font-weight: 500;
    font-family: 'Ubuntu', sans-serif;
  }

  .input-row {
    display: flex;
    align-items: center;
    background: white;
    border-bottom: 3px solid transparent;
    border-image: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700)) 1;
    box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    margin-top: 1rem;
    flex-shrink: 0;
  }

  .input-row.flourish {
    animation: flourish-glow 0.55s ease-out;
  }

  .input-row.flourish::after {
    content: '';
    position: absolute;
    left: 0;
    right: 0;
    bottom: -3px;
    height: 3px;
    animation: flourish-spin 0.55s ease-out;
  }

  @keyframes flourish-spin {
    0% {
      background: linear-gradient(to right, hsl(0 55% 58%), hsl(60 55% 58%));
    }
    25% {
      background: linear-gradient(to right, hsl(90 55% 55%), hsl(160 55% 52%));
    }
    50% {
      background: linear-gradient(to right, hsl(190 50% 52%), hsl(230 50% 55%));
    }
    75% {
      background: linear-gradient(to right, hsl(280 50% 58%), hsl(320 50% 58%));
    }
    100% {
      background: linear-gradient(to right, var(--page-p0, #ff9900), var(--page-p1, #ffd700));
    }
  }

  @keyframes flourish-glow {
    0% {
      box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    }
    40% {
      box-shadow:
        0 10px 20px -4px hsl(300 45% 60% / 0.25),
        0 10px 18px -4px rgba(35, 47, 62, 0.35);
    }
    100% {
      box-shadow: 0 10px 18px -4px rgba(35, 47, 62, 0.35);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .input-row.flourish {
      animation: none;
    }
    .input-row.flourish::after {
      animation: none;
    }
  }

  .input-row input {
    flex: 1;
    border: none;
    outline: none;
    padding: 0.875rem 1rem;
    font-size: 0.95rem;
    background: transparent;
    color: black;
    font-family: 'Ubuntu', sans-serif;
  }

  .input-row button {
    border: none;
    background: transparent;
    padding: 0 1rem;
    cursor: pointer;
    font-size: 0.9rem;
    font-family: 'Ubuntu', sans-serif;
    color: #232f3e;
  }
</style>
```

Note: `.input-row` needs `position: relative` for its `::after` flourish line to place correctly — add `position: relative;` to the `.input-row` rule above (it was omitted from the block for brevity in review; include it when writing the file).

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/components/AgentChatWindow.test.ts`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/lib/components/AgentChatWindow.svelte src/lib/components/AgentChatWindow.test.ts
git commit -m "feat(frontend): rebuild AgentChatWindow — Discord-style layout, streaming, flourish, glow"
```

---

## Module F: Backend router wiring

**Depends on:** Module D (`chat_service`)

**Files:**
- Modify: `backend/app/routers/library.py`
- Test: `backend/tests/test_library_router.py`

### Task F1: Wire chat routes, retire old mentor endpoint

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_library_router.py`:

```python
from unittest.mock import patch

import pytest
from httpx import AsyncClient


async def test_create_and_list_chat_sessions(authenticated_client: AsyncClient) -> None:
    create_resp = await authenticated_client.post("/library/chats")
    assert create_resp.status_code == 200
    session_id = create_resp.json()["id"]

    list_resp = await authenticated_client.get("/library/chats")
    assert list_resp.status_code == 200
    assert any(s["id"] == session_id for s in list_resp.json())


async def test_get_chat_session_404_for_nonexistent(authenticated_client: AsyncClient) -> None:
    resp = await authenticated_client.get("/library/chats/999999")
    assert resp.status_code == 404


async def test_post_chat_message_streams_sse_and_persists(authenticated_client: AsyncClient) -> None:
    create_resp = await authenticated_client.post("/library/chats")
    session_id = create_resp.json()["id"]

    def fake_event_stream():
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "Hi "}}}'}}
        yield {"chunk": {"bytes": b'{"contentBlockDelta": {"delta": {"text": "there."}}}'}}

    with (
        patch("app.services.chat_service.embed_text", return_value=[0.1] * 1024),
        patch("app.services.chat_service._fetch_mentor_context", return_value=[]),
        patch("app.services.chat_service.get_bedrock_client") as mock_get_client,
    ):
        mock_get_client.return_value.invoke_model_with_response_stream.return_value = {
            "body": fake_event_stream()
        }

        async with authenticated_client.stream(
            "POST", f"/library/chats/{session_id}/messages", json={"message": "Hi"}
        ) as resp:
            assert resp.status_code == 200
            body_text = ""
            async for chunk in resp.aiter_text():
                body_text += chunk

    assert "Hi " in body_text
    assert "there." in body_text

    detail_resp = await authenticated_client.get(f"/library/chats/{session_id}")
    messages = detail_resp.json()["messages"]
    assert [m["role"] for m in messages] == ["user", "mentor"]


async def test_old_mentor_endpoint_is_removed(authenticated_client: AsyncClient) -> None:
    resp = await authenticated_client.post("/library/mentor", json={"message": "hi"})
    assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && poetry run pytest tests/test_library_router.py -v`
Expected: FAIL — `404` for `/library/chats` routes (not yet wired), and the last test unexpectedly passes today only because the route doesn't exist yet either way (verify the first three fail with connection/404-not-found-route errors, distinct from the intentional 404 in test 2 and test 4)

- [ ] **Step 3: Update the router**

Replace the contents of `backend/app/routers/library.py`:

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.chat import ChatMessageRequest, ChatSessionDetail, ChatSessionSummary
from app.schemas.library import ContentSearchResult, LibraryResponse
from app.services import chat_service, library_service

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/", response_model=LibraryResponse, summary="Get user's library")
async def get_library(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LibraryResponse:
    return await library_service.get_library(db, current_user)


@router.get(
    "/search",
    response_model=list[ContentSearchResult],
    summary="Semantic search across catalogue",
)
async def search(
    q: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContentSearchResult]:
    return await library_service.semantic_search(db, q, current_user)


@router.get("/chats", response_model=list[ChatSessionSummary], summary="List chat sessions")
async def list_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ChatSessionSummary]:
    sessions = await chat_service.list_sessions(db, current_user)
    return [ChatSessionSummary.model_validate(s) for s in sessions]


@router.post("/chats", response_model=ChatSessionSummary, summary="Create a new chat session")
async def create_chat(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionSummary:
    session = await chat_service.create_session(db, current_user)
    return ChatSessionSummary.model_validate(session)


@router.get("/chats/{session_id}", response_model=ChatSessionDetail, summary="Get chat session detail")
async def get_chat(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionDetail:
    session = await chat_service.get_session_or_404(db, session_id, current_user)
    return await chat_service.get_session_detail(db, session, current_user)


@router.post("/chats/{session_id}/messages", summary="Send a message, stream the mentor's reply")
async def post_chat_message(
    session_id: int,
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    session = await chat_service.get_session_or_404(db, session_id, current_user)

    async def event_generator():
        async for delta in chat_service.stream_mentor_reply(db, session, body.message, current_user):
            yield f'data: {{"delta": {delta!r}}}\n\n'.replace("'", '"')
        yield 'data: {"done": true}\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && poetry run pytest tests/test_library_router.py -v`
Expected: PASS (4 tests)

**If the SSE delta-line encoding fails on quote-escaping** (the `.replace("'", '"')` trick above is a naive stand-in): replace `event_generator`'s body line with proper JSON encoding instead:

```python
import json

async def event_generator():
    async for delta in chat_service.stream_mentor_reply(db, session, body.message, current_user):
        yield f"data: {json.dumps({'delta': delta})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"
```

(add `import json` to the top of the file if using this version — prefer this version outright, it's more correct than the naive replace; the naive version above is shown only because it mirrors what a first draft might look like and the test will catch the difference either way).

- [ ] **Step 5: Run full backend test suite + lint**

Run: `cd backend && poetry run ruff check . && poetry run pytest`
Expected: no lint errors, all tests pass (including the pre-existing `test_library_service.py::test_mentor_query_returns_reply_and_sources` — that test targets `library_service.mentor_query`, which still exists as a function even though its route is gone; leave `library_service.mentor_query` and its test in place, only the router endpoint was removed, per the spec's "no reason to keep two parallel ask-the-mentor code paths" referring to routes, not the retrievable RAG helper logic)

- [ ] **Step 6: Commit**

```bash
cd backend
git add app/routers/library.py tests/test_library_router.py
git commit -m "feat(backend): wire chat session routes, retire stateless /library/mentor"
```

---

## Module G: Frontend CTASidebar hand-off

**Depends on:** Module B (`chat.ts`)

**Files:**
- Modify: `frontend/src/lib/components/CTASidebar.svelte`
- Test: check for an existing `CTASidebar.test.ts`; if none exists, this task adds one for just the changed behaviour (don't attempt full existing-behaviour coverage retroactively)

### Task G1: Create-session-and-navigate hand-off

- [ ] **Step 1: Check for an existing test file**

Run: `ls frontend/src/lib/components/CTASidebar.test.ts 2>/dev/null && echo exists || echo none`

If `none`, create `frontend/src/lib/components/CTASidebar.test.ts` with just this one test (don't retrofit full coverage of the rest of the component — out of scope for this task):

```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import CTASidebar from './CTASidebar.svelte';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));
vi.mock('$lib/api/chat', () => ({
  createChatSession: vi.fn().mockResolvedValue({ id: 7, title: 'New chat', updated_at: '2026-07-01T00:00:00Z' }),
}));

describe('CTASidebar mentor hand-off', () => {
  it('creates a chat session and navigates to it with the draft message on submit', async () => {
    const { goto } = await import('$app/navigation');
    const { createChatSession } = await import('$lib/api/chat');

    render(CTASidebar, {
      props: { user: { id: 1, first_name: 'Harley' }, albums: [], snippets: [] },
    });

    const input = screen.getByPlaceholderText('Ask your mentor anything...') as HTMLInputElement;
    input.value = 'What is a T-Level?';
    input.dispatchEvent(new Event('input'));
    const form = input.closest('form') as HTMLFormElement;
    form.dispatchEvent(new Event('submit', { cancelable: true }));

    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(createChatSession).toHaveBeenCalled();
    expect(goto).toHaveBeenCalledWith(
      `/library?session=7&draft=${encodeURIComponent('What is a T-Level?')}`
    );
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/lib/components/CTASidebar.test.ts`
Expected: FAIL — `goto` is called with the old `/library?q=...` URL, not `/library?session=...&draft=...`

- [ ] **Step 3: Update the hand-off**

Edit `frontend/src/lib/components/CTASidebar.svelte`. Add the import (near the other `$lib/api/library` import):

```typescript
import { createChatSession } from '$lib/api/chat';
```

Replace the existing `handleAgentSubmit` function:

```typescript
async function handleAgentSubmit(event: CustomEvent<string>) {
  const message = event.detail;
  const session = await createChatSession();
  goto(`/library?session=${session.id}&draft=${encodeURIComponent(message)}`);
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/lib/components/CTASidebar.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
cd frontend
git add src/lib/components/CTASidebar.svelte src/lib/components/CTASidebar.test.ts
git commit -m "feat(frontend): CTASidebar mentor teaser creates a session and hands off draft text"
```

---

## Module H: Frontend `/library` page — three-column layout

**Depends on:** Module E (`AgentChatWindow`), Module F (live backend routes), Module B (`chat.ts`)

**Files:**
- Modify: `frontend/src/routes/library/+page.ts`
- Modify: `frontend/src/routes/library/+page.svelte`

### Task H1: Loader — sessions list, active session, library data

- [ ] **Step 1: Rewrite the loader**

Replace `frontend/src/routes/library/+page.ts`:

```typescript
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { getLibrary } from '$lib/api/library';
import { listChatSessions, getChatSession } from '$lib/api/chat';
import { ApiError } from '$lib/api/client';

export const load: PageLoad = async ({ url }) => {
  try {
    const [library, sessions] = await Promise.all([getLibrary(), listChatSessions()]);

    const sessionParam = url.searchParams.get('session');
    const draft = url.searchParams.get('draft') ?? '';

    let activeSessionId: number | null = sessionParam ? Number(sessionParam) : null;
    if (activeSessionId === null && sessions.length > 0) {
      activeSessionId = sessions[0].id;
    }

    const activeSession = activeSessionId !== null ? await getChatSession(activeSessionId) : null;

    return { library, sessions, activeSession, draft };
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      throw redirect(302, `/login?next=${encodeURIComponent(url.pathname)}`);
    }
    throw err;
  }
};
```

There is no test file for this loader (matches the existing codebase convention — the prior `+page.ts` had no dedicated test either; loader behaviour is exercised indirectly via the page component and manual/Playwright verification in Module I).

- [ ] **Step 2: Commit**

```bash
cd frontend
git add src/routes/library/+page.ts
git commit -m "feat(frontend): Library page loader fetches sessions + active session"
```

### Task H2: Three-column page layout

- [ ] **Step 1: Rewrite the page**

Replace `frontend/src/routes/library/+page.svelte`:

```svelte
<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import type { PageData } from './$types';
  import PageCard from '$lib/components/PageCard.svelte';
  import AlbumCard from '$lib/components/AlbumCard.svelte';
  import SnippetCard from '$lib/components/SnippetCard.svelte';
  import AgentChatWindow from '$lib/components/AgentChatWindow.svelte';
  import { createChatSession, getChatSession, sendChatMessage } from '$lib/api/chat';
  import type { ChatSessionSummary, ChatSessionDetail } from '$lib/api/chat';
  import { saveSnippet, unsaveSnippet } from '$lib/api/library';
  import { currentUser } from '$lib/stores/user';
  import { enrolledAlbumIds } from '$lib/stores/enrolments';
  import { savedSnippetIds } from '$lib/stores/savedSnippets';

  export let data: PageData;

  let sessions: ChatSessionSummary[] = data.sessions;
  let activeSession: ChatSessionDetail | null = data.activeSession;
  let streamingText: string | undefined = undefined;
  let isStreaming = false;

  savedSnippetIds.set(new Set(data.library.saved_snippets.map((s) => s.id)));
  enrolledAlbumIds.set(new Set(data.library.enrolled_albums.map((a) => a.id)));

  $: displayedEnrolledAlbums = data.library.enrolled_albums.filter((a) => $enrolledAlbumIds.has(a.id));
  $: displayedSavedSnippets = data.library.saved_snippets.filter((s) => $savedSnippetIds.has(s.id));

  async function selectSession(sessionId: number) {
    activeSession = await getChatSession(sessionId);
    goto(`/library?session=${sessionId}`, { keepFocus: true, noScroll: true });
  }

  async function handleNewChat() {
    const session = await createChatSession();
    sessions = [{ id: session.id, title: session.title, updated_at: session.updated_at }, ...sessions];
    activeSession = { id: session.id, title: session.title, messages: [] };
    goto(`/library?session=${session.id}`, { keepFocus: true, noScroll: true });
  }

  async function handleSend(text: string) {
    if (!activeSession) return;
    const sessionId = activeSession.id;
    isStreaming = true;
    streamingText = '';
    try {
      const result = await sendChatMessage(sessionId, text, (delta) => {
        streamingText = (streamingText ?? '') + delta;
      });
      activeSession = await getChatSession(sessionId);
      sessions = sessions.map((s) =>
        s.id === sessionId ? { ...s, title: activeSession!.title, updated_at: new Date().toISOString() } : s
      );
      void result;
    } finally {
      isStreaming = false;
      streamingText = undefined;
    }
  }

  async function toggleSave(contentId: number, currentlySaved: boolean) {
    if (currentlySaved) {
      savedSnippetIds.update((s) => {
        s.delete(contentId);
        return new Set(s);
      });
      await unsaveSnippet(contentId);
    } else {
      savedSnippetIds.update((s) => {
        s.add(contentId);
        return new Set(s);
      });
      await saveSnippet(contentId);
    }
  }

  onMount(() => {
    if (data.draft && activeSession) {
      handleSend(data.draft);
    }
  });
</script>

<div class="library-layout">
  <PageCard as="aside" width="var(--rail-width)" padding="1rem" overflowY="auto">
    <button class="new-chat-btn" on:click={handleNewChat}>+ New chat</button>
    {#if sessions.length === 0}
      <p class="empty">No chats yet — ask the Mentor something to start one.</p>
    {:else}
      <ul class="session-list">
        {#each sessions as session (session.id)}
          <li>
            <button
              class="session-item"
              class:active={activeSession?.id === session.id}
              on:click={() => selectSession(session.id)}
            >
              {session.title}
            </button>
          </li>
        {/each}
      </ul>
    {/if}
  </PageCard>

  <PageCard as="main" padding="1rem 1.5rem">
    {#if activeSession}
      <AgentChatWindow
        messages={activeSession.messages}
        onSend={handleSend}
        userDisplayName={$currentUser?.first_name || $currentUser?.username || 'You'}
        {streamingText}
        {isStreaming}
      />
    {:else}
      <p class="empty">Start a new chat to talk to the Dynamic Mentor.</p>
    {/if}
  </PageCard>

  <div class="right-stack">
    <PageCard padding="1rem 1.25rem" overflowY="auto">
      <span class="section-label">Enrolled Albums</span>
      {#if displayedEnrolledAlbums.length === 0}
        <p class="empty">No albums enrolled yet — browse Albums to get started.</p>
      {:else}
        <div class="album-grid">
          {#each displayedEnrolledAlbums as album (album.id)}
            <AlbumCard {album} />
          {/each}
        </div>
      {/if}
    </PageCard>

    <PageCard padding="1rem 1.25rem" overflowY="auto">
      <span class="section-label">Saved Snippets</span>
      {#if displayedSavedSnippets.length === 0}
        <p class="empty">No saved snippets yet — save one while browsing to see it here.</p>
      {:else}
        <div class="snippet-list">
          {#each displayedSavedSnippets as snippet (snippet.id)}
            <SnippetCard
              content={snippet}
              saved={$savedSnippetIds.has(snippet.id)}
              onSaveToggle={() => toggleSave(snippet.id, $savedSnippetIds.has(snippet.id))}
            />
          {/each}
        </div>
      {/if}
    </PageCard>
  </div>
</div>

<style>
  /* Both flanking columns share one derived width so they can't drift apart:
     2 AlbumCards at AlbumGrid's max track width (220px, see
     AlbumGrid.svelte's minmax(190px, 220px)) + one --gap-inner between them
     + 1.5rem padding on each side of a PageCard (2 * 1.5rem = 3rem). */
  .library-layout {
    --rail-width: calc(2 * 220px + var(--gap-inner) + 3rem);
    display: flex;
    gap: var(--gap-inner);
    height: 100%;
  }

  .library-layout > :global(aside.page-card) {
    flex: 0 0 var(--rail-width);
  }

  .library-layout > :global(main.page-card) {
    flex: 1 1 auto;
    min-width: 0;
  }

  .right-stack {
    flex: 0 0 var(--rail-width);
    display: flex;
    flex-direction: column;
    gap: var(--gap-inner);
  }

  .right-stack :global(.page-card) {
    flex: 1 1 0;
    min-height: 0;
  }

  .new-chat-btn {
    width: 100%;
    padding: 0.6rem;
    margin-bottom: 0.75rem;
    background: #232f3e;
    color: white;
    border: none;
    cursor: pointer;
    font-family: 'Ubuntu', sans-serif;
    font-size: 0.85rem;
    font-weight: 600;
  }

  .session-list {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .session-item {
    width: 100%;
    text-align: left;
    background: none;
    border: none;
    padding: 0.5rem 0.6rem;
    cursor: pointer;
    font-family: 'Ubuntu', sans-serif;
    font-size: 0.825rem;
    color: #5a6472;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .session-item.active {
    color: #232f3e;
    font-weight: 700;
    background: rgba(35, 47, 62, 0.06);
  }

  .section-label {
    display: block;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #5a6472;
    font-family: 'Ubuntu', sans-serif;
    margin-bottom: 0.75rem;
  }

  .album-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--gap-inner);
  }

  .snippet-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .empty {
    color: #5a6472;
    font-size: 0.875rem;
    margin: 0;
    font-family: 'Ubuntu', sans-serif;
  }
</style>
```

- [ ] **Step 2: Typecheck and lint**

Run: `cd frontend && npm run check && npm run lint`
Expected: no new errors (pre-existing baseline errors/warnings from other files are fine, per this project's established convention of comparing against a `git stash` baseline if unsure)

- [ ] **Step 3: Commit**

```bash
cd frontend
git add src/routes/library/+page.svelte
git commit -m "feat(frontend): three-column Library layout — chat history, Mentor chat, Albums/Snippets stack"
```

---

## Module I: Full-stack verification

**Depends on:** all prior modules

**Files:** none modified — this task only runs checks.

### Task I1: Full test suites + manual/Playwright pass

- [ ] **Step 1: Backend full suite**

Run: `cd backend && poetry run ruff check . && poetry run pytest -v`
Expected: all tests pass, no lint errors

- [ ] **Step 2: Frontend full suite**

Run: `cd frontend && npm run check && npm run lint && npx vitest run`
Expected: no new typecheck/lint errors vs. the pre-existing baseline, all vitest tests pass

- [ ] **Step 3: Manual/Playwright verification of animations and streaming**

Start the stack: `docker compose up --build -d && docker compose exec backend poetry run alembic upgrade head`

Using Playwright (as used throughout this session for prior visual verification), against a logged-in session:
1. Navigate to `/library`. Confirm the three-column layout renders: chat history rail (left), Mentor chat (center), Enrolled Albums + Saved Snippets stack (right, 2-col album grid).
2. Click "+ New chat", send a message. Confirm: the chat card's inner glow appears (fog creep-in) while streaming, text chunks blur-in as they arrive, the glow fades out (fog dissipate) when the stream ends, and the new session appears in the left rail with a title derived from the first message.
3. Send a second message in the same session. Confirm the send flourish animation plays on the input row, and the session's rail entry doesn't get a new title (title only set on the session's first message).
4. From the home page (`/`), type into the CTASidebar Mentor teaser and submit. Confirm it navigates to `/library?session=<id>&draft=<text>` and the message auto-sends on load.
5. Confirm `POST /library/mentor` returns 404 (already covered by an automated test, but worth a quick manual `curl` check too: `curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/library/mentor` should print `404`).

Expected: all five checks pass. If any animation timing/visual detail doesn't match the spec (`docs/superpowers/specs/2026-07-01-library-mentor-redesign-design.md`), fix it in the relevant component before considering this task done — this step is the actual acceptance check for the visual/animation work, not just the automated tests.

- [ ] **Step 4: Final commit (only if Step 3 required fixes)**

```bash
git add -A
git commit -m "fix: address issues found during Library/Mentor redesign verification pass"
```

If Step 3 required no fixes, skip this step — there's nothing to commit.
