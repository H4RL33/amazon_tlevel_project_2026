import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/svelte';
import CTASidebar from './CTASidebar.svelte';

vi.mock('$app/navigation', () => ({ goto: vi.fn() }));
vi.mock('$lib/api/chat', () => ({
  createChatSession: vi
    .fn()
    .mockResolvedValue({ id: 7, title: 'New chat', updated_at: '2026-07-01T00:00:00Z' }),
}));

describe('CTASidebar mentor hand-off', () => {
  it('creates a chat session and navigates to it with the draft message on submit', async () => {
    const { goto } = await import('$app/navigation');
    const { createChatSession } = await import('$lib/api/chat');

    render(CTASidebar, {
      props: {
        user: {
          id: 1,
          cognito_sub: 'sub-1',
          email: 'harley@example.com',
          first_name: 'Harley',
          last_name: 'Welsh',
          username: null,
          avatar_url: null,
          created_at: '2026-07-01T00:00:00Z',
        },
        albums: [],
        snippets: [],
      },
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
