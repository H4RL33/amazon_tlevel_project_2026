import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';
import { agentDraft } from './agentDraft';

describe('agentDraft', () => {
  beforeEach(() => agentDraft.set(null));

  it('initialises to null', () => {
    expect(get(agentDraft)).toBeNull();
  });

  it('stores a draft message', () => {
    agentDraft.set('What is cloud computing?');
    expect(get(agentDraft)).toBe('What is cloud computing?');
  });

  it('clears back to null', () => {
    agentDraft.set('hello');
    agentDraft.set(null);
    expect(get(agentDraft)).toBeNull();
  });
});
