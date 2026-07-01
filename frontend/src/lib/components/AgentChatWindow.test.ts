import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import AgentChatWindow from './AgentChatWindow.svelte';
import type { ChatMessageRecord } from '$lib/api/chat';

describe('AgentChatWindow', () => {
  const messages: ChatMessageRecord[] = [
    {
      id: 1,
      role: 'user',
      text: 'What is networking?',
      sources: null,
      created_at: '2026-07-01T14:00:00Z',
    },
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
