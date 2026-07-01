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
